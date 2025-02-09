import fitz
import json
import faiss
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import pdfplumber

# Inisialisasi global
vectorizer = TfidfVectorizer()
index = None
embedding_metadata = []

INDEX_PATH = "faiss_index.bin"
METADATA_PATH = "embedding_metadata.json"
VECTORIZER_PATH = "vectorizer_vocab.json"  # Simpan vocab TF-IDF

# Fungsi untuk menyimpan index dan metadata
def save_faiss_index():
    if index is not None:
        faiss.write_index(index, INDEX_PATH)
    with open(METADATA_PATH, "w", encoding="utf-8") as meta_file:
        json.dump(embedding_metadata, meta_file, ensure_ascii=False, indent=4)
    with open(VECTORIZER_PATH, "w", encoding="utf-8") as vocab_file:
        json.dump(vectorizer.vocabulary_, vocab_file)  # Simpan vocab TF-IDF

# Fungsi untuk memuat index dan metadata
def load_faiss_index():
    global index, embedding_metadata, vectorizer
    if Path(INDEX_PATH).exists():
        index = faiss.read_index(INDEX_PATH)
    if Path(METADATA_PATH).exists():
        with open(METADATA_PATH, "r", encoding="utf-8") as meta_file:
            embedding_metadata = json.load(meta_file)
    if Path(VECTORIZER_PATH).exists():
        with open(VECTORIZER_PATH, "r", encoding="utf-8") as vocab_file:
            vocab = json.load(vocab_file)
            
            if vocab:  # ✅ Hanya lakukan fit jika vocabulary tidak kosong
                vectorizer = TfidfVectorizer(vocabulary=vocab)
                try:
                    dummy_data = list(vocab.keys())
                    vectorizer.fit(dummy_data)  # ✅ Pastikan vectorizer valid
                except ValueError:
                    print("Error: Vocabulary tidak valid. Vectorizer di-reset.")
                    vectorizer = TfidfVectorizer()  # Reset vectorizer jika error
            else:
                vectorizer = TfidfVectorizer()  # Inisialisasi ulang jika kosong 

# Fungsi untuk menghasilkan embedding dan menambahkan metadata
def generate_embeddings(pdf_path, pdf_id):
    global index, vectorizer
    doc = fitz.open(pdf_path)
    pdf_name = Path(pdf_path).stem

    txt_folder = Path(pdf_name) / "txt"
    json_folder = Path(pdf_name) / "json"
    txt_folder.mkdir(parents=True, exist_ok=True)
    json_folder.mkdir(parents=True, exist_ok=True)

    # Menggunakan pdfplumber untuk ekstraksi teks
    all_texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_texts.append(text.strip())

    if not all_texts:
        return

    # Update vocabulary jika belum ada
    vectorizer.fit(all_texts)
    vectors = vectorizer.transform(all_texts).toarray()

    if index is None or index.d != vectors.shape[1]:
        index = faiss.IndexFlatL2(vectors.shape[1])
        embedding_metadata.clear()

    index.add(np.array(vectors, dtype='float32'))

    # Menambahkan metadata untuk setiap teks halaman
    for i, text in enumerate(all_texts):
        embedding_metadata.append({
            "doc_id": pdf_id,
            "page_number": i + 1,
            "text": text,
            "path": f"{pdf_name}.pdf"
        })

    # Menyimpan FAISS index dan metadata
    save_faiss_index()
    save_metadata_json(pdf_id, pdf_path)

# Fungsi untuk menyimpan metadata JSON
def save_metadata_json(pdf_id, pdf_path):
    pdf_name = Path(pdf_path).stem
    json_folder = Path(pdf_name) / "json"
    json_folder.mkdir(parents=True, exist_ok=True)

    metadata = {
        "id": pdf_id,
        "path": f"{pdf_name}.pdf",
        "name": pdf_name,
        "json_folder": f"{pdf_name}/json"
    }

    metadata_file = json_folder / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=4)

# Fungsi untuk pencarian dengan FAISS
def search_with_faiss(pdf_path, query, pdf_id, top_k=5):
    global index, embedding_metadata, vectorizer
    load_faiss_index()

    pdf_metadata = [meta for meta in embedding_metadata if meta["doc_id"] == pdf_id]
    all_texts = [meta["text"] for meta in pdf_metadata]

    if not all_texts:
        return [{"error": "Tidak ada data untuk PDF ini."}]

    # Gunakan vectorizer yang sudah ada
    query_vector = vectorizer.transform([query]).toarray()[0]

    # Pad atau trim agar sesuai dengan dimensi index
    if index.d != len(query_vector):
        if len(query_vector) > index.d:
            query_vector = query_vector[:index.d]  # Trim
        else:
            query_vector = np.pad(query_vector, (0, index.d - len(query_vector)), 'constant')  # Padding

    results = []
    if np.count_nonzero(query_vector) > 0:
        D, I = index.search(np.array([query_vector], dtype='float32'), top_k)
        for idx in I[0]:
            if 0 <= idx < len(pdf_metadata):
                results.append(pdf_metadata[idx])
    else:
        results = [meta for meta in pdf_metadata if query.lower() in meta["text"].lower()]

    return results if results else [{"error": "Tidak ditemukan hasil relevan."}]

# Menambahkan algoritma machine learning (contoh: KMeans clustering) untuk kategorisasi dokumen PDF
def categorize_pdf_elements(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        all_texts = [page.extract_text().strip() for page in pdf.pages if page.extract_text().strip()]

    if not all_texts:
        return []

    vectors = vectorizer.transform(all_texts).toarray()

    # KMeans untuk mengelompokkan elemen berdasarkan teks
    kmeans = KMeans(n_clusters=5, random_state=42)  # Misal 5 cluster
    labels = kmeans.fit_predict(vectors)

    categorized_elements = []
    for idx, label in enumerate(labels):
        categorized_elements.append({
            "page_number": idx + 1,
            "category": f"Cluster {label}",
            "text": all_texts[idx]
        })

    return categorized_elements
