import fitz
import json
import uuid
import faiss
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random

# Inisialisasi global
vectorizer = TfidfVectorizer()
index = None
embedding_metadata = []

INDEX_PATH = "faiss_index.bin"
METADATA_PATH = "embedding_metadata.json"

# Fungsi untuk menyimpan FAISS Index & Metadata
def save_faiss_index():
    if index is not None:
        faiss.write_index(index, INDEX_PATH)
    with open(METADATA_PATH, "w", encoding="utf-8") as meta_file:
        json.dump(embedding_metadata, meta_file, ensure_ascii=False, indent=4)

# Fungsi untuk memuat FAISS Index & Metadata
def load_faiss_index():
    global index, embedding_metadata
    if Path(INDEX_PATH).exists():
        index = faiss.read_index(INDEX_PATH)
    if Path(METADATA_PATH).exists():
        with open(METADATA_PATH, "r", encoding="utf-8") as meta_file:
            embedding_metadata = json.load(meta_file)

# Muat index saat modul pertama kali diimpor
load_faiss_index()

# Fungsi untuk membuat embedding dari PDF
def generate_embeddings(pdf_path):
    global index
    doc = fitz.open(pdf_path)
    pdf_id = str(uuid.uuid4())
    pdf_name = Path(pdf_path).stem

    folder_path = Path(pdf_name)
    txt_folder = folder_path / "txt"
    json_folder = folder_path / "json"

    txt_folder.mkdir(parents=True, exist_ok=True)
    json_folder.mkdir(parents=True, exist_ok=True)

    all_texts = [doc.load_page(i).get_text("text").strip() for i in range(len(doc))]
    all_texts = [text for text in all_texts if text]

    if not all_texts:
        print("⚠️ Tidak ada teks yang ditemukan dalam PDF.")
        return

    for i, page_text in enumerate(all_texts):
        filename = txt_folder / f"page_{i + 1}.txt"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(page_text)

    vectorizer.fit(all_texts)
    with open(json_folder / "vocabulary.json", "w", encoding="utf-8") as vocab_file:
        json.dump(vectorizer.vocabulary_, vocab_file, ensure_ascii=False, indent=4)

    vectors = vectorizer.transform(all_texts).toarray()

    # Pengecekan dimensi sebelum menambahkan vektor
    if index is None:
        dim = vectors.shape[1]
        index = faiss.IndexFlatL2(dim)
        print(f"✅ Index FAISS baru dibuat dengan dimensi: {dim}")
    elif index.d != vectors.shape[1]:
        print(f"⚠️ Dimensi tidak cocok! Index FAISS: {index.d}, Vektor Baru: {vectors.shape[1]}")
        index = faiss.IndexFlatL2(vectors.shape[1])
        embedding_metadata.clear()
        print("🔄 Index FAISS di-reset karena ketidaksesuaian dimensi.")

    index.add(np.array(vectors, dtype='float32'))

    for i, text in enumerate(all_texts):
        embedding_metadata.append({
            "doc_id": pdf_id,
            "page_number": i + 1,
            "text": text,
            "path": f"{pdf_name}.pdf"
        })
        print(f"✅ Embedding berhasil untuk halaman {i + 1}")

    save_faiss_index()
    save_metadata_json(pdf_id, pdf_path)

# Simpan metadata PDF
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

# Fungsi pencarian dengan FAISS & fallback kreatif
def search_with_faiss(pdf_path, query, top_k=5):
    global index, embedding_metadata
    pdf_name = Path(pdf_path).stem

    load_faiss_index()

    pdf_metadata = [meta for meta in embedding_metadata if meta["path"] == f"{pdf_name}.pdf"]
    all_texts = [meta["text"] for meta in pdf_metadata]

    # Muat vocabulary
    vocab_path = f"{pdf_name}/json/vocabulary.json"
    if Path(vocab_path).exists():
        with open(vocab_path, "r", encoding="utf-8") as vocab_file:
            vocabulary = json.load(vocab_file)
    else:
        vocabulary = None

    vectorizer = TfidfVectorizer(vocabulary=vocabulary)
    combined_texts = all_texts + [query]
    vectors = vectorizer.fit_transform(combined_texts).toarray()

    query_vector = vectors[-1]

    results = []
    if np.count_nonzero(query_vector) > 0:
        # FAISS search jika query valid
        D, I = index.search(np.array([query_vector], dtype='float32'), top_k)
        for idx in I[0]:
            if 0 <= idx < len(embedding_metadata):
                results.append(embedding_metadata[idx])
    else:
        # Alternatif: Pencarian kreatif
        print("⚠️ Query tidak menghasilkan vektor. Menggunakan pendekatan kreatif.")

        # 1️⃣ Pencocokan sederhana
        keyword_results = [meta for meta in pdf_metadata if query.lower() in meta["text"].lower()]

        # 2️⃣ Kemiripan dengan cosine similarity
        query_vector_alt = vectorizer.transform([query]).toarray()
        similarity_scores = cosine_similarity(vectors[:-1], query_vector_alt).flatten()
        top_indices = similarity_scores.argsort()[-top_k:][::-1]

        similarity_results = [pdf_metadata[i] for i in top_indices if similarity_scores[i] > 0]

        # Gabungkan hasil
        results = keyword_results + similarity_results

        # 3️⃣ Jika masih kosong, ambil random konteks
        if not results:
            results = [random.choice(pdf_metadata)]

    return results if results else [{"error": "🔍 Tidak ditemukan hasil relevan, tapi ini konteks acak dari PDF."}]
