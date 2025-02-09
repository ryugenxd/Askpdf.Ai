import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from .pdf.ai import ask_pollinations
from .pdf.pdfparser import (
    generate_embeddings,        # Konsisten dengan pdfparser.py
    search_with_faiss           # Konsisten dengan pdfparser.py
)

UPLOAD_FOLDER = "./storage"
HISTORY_FILE = "./history.json"
ALLOWED_EXTENSIONS = {'pdf'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inisialisasi file history jika belum ada
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)

main = Blueprint("main", __name__)

# Fungsi Cek Format File
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Fungsi Simpan Riwayat
def save_to_history(entry):
    entry["timestamp"] = datetime.now().isoformat()
    with open(HISTORY_FILE, "r+") as f:
        history = json.load(f)
        history.append(entry)
        f.seek(0)
        json.dump(history, f, ensure_ascii=False, indent=4)

# API 1️⃣: Upload PDF
@main.route("/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "Harap unggah file PDF."}), 400

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "File harus berformat PDF."}), 400

    # 🔑 Buat ID unik untuk PDF
    pdf_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, f"{pdf_id}.pdf")
    file.save(file_path)

    # Ekstraksi & penyimpanan data
    generate_embeddings(file_path, pdf_id)  # 🔥 Buat embedding untuk pencarian nanti

    return jsonify({
        "message": "PDF berhasil diunggah!",
        "pdf_id": pdf_id
    }), 200

# API 2️⃣: Ajukan Pertanyaan dengan FAISS
# Fungsi untuk memeriksa apakah pertanyaan bersifat kontekstual
def is_contextual_question(question):
    keywords = ["sumber", "berkaitan", "lanjutkan", "jelaskan lebih detail", "darimana kamu tahu", "kenapa"]
    return any(keyword in question.lower() for keyword in keywords)

# Fungsi untuk mengambil jawaban terakhir dari riwayat
def get_last_answer(pdf_id):
    history = load_history(pdf_id)
    if history:
        return history[-1].get("answer")
    return None

# Fungsi untuk memuat riwayat berdasarkan pdf_id
def load_history(pdf_id):
    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)
    # Filter riwayat hanya untuk pdf_id yang sesuai
    return [entry for entry in history if entry["id"] == pdf_id]

# API 2️⃣: Ajukan Pertanyaan dengan FAISS
@main.route("/ask", methods=["POST"])
def ask_question():
    question = request.form.get("question")
    pdf_id = request.form.get("pdf_id")
    top_k = request.form.get("top_k", 1)

    if not pdf_id or not question:
        return jsonify({"error": "ID PDF atau pertanyaan tidak boleh kosong."}), 400

    file_path = os.path.join(UPLOAD_FOLDER, f"{pdf_id}.pdf")
    if not os.path.exists(file_path):
        return jsonify({"error": "File PDF tidak ditemukan."}), 404

    try:
        top_k = int(top_k)
    except ValueError:
        return jsonify({"error": "Parameter top_k harus berupa angka."}), 400

    # 🔍 Cari teks paling relevan menggunakan FAISS
    relevant_text = search_with_faiss(file_path, question, pdf_id, top_k=top_k)

    if isinstance(relevant_text, list) and "error" in relevant_text[0]:
        return jsonify({"error": relevant_text[0]["error"]}), 400

    # 🔗 Gunakan jawaban terakhir jika pertanyaan bersifat kontekstual
    last_answer = get_last_answer(pdf_id)
    if is_contextual_question(question) and last_answer:
        context_prompt = (
            f"Berikut jawaban terakhir: '{last_answer}'. "
            "Sekarang, jika ada pertanyaan seperti 'darimana kamu tahu' atau yang serupa, "
            "jawablah dengan cara yang sopan dan profesional. Jelaskan bahwa informasi tersebut "
            "diperoleh dari analisis dokumen tanpa menyebutkan detail sensitif seperti nama institusi, ID dokumen, atau data pribadi. "
            "Gunakan bahasa yang ringkas, jelas, dan hindari kesan terlalu teknis agar mudah dipahami."
        )
        prompt = (
            f"aku Aseko, asisten AI yang ahli menganalisis isi PDF. {context_prompt} "
            f"Sekarang, jawab pertanyaan ini dengan singkat namun informatif: '{question}'."
        )
    else:
        prompt = (
            f"aku Aseko, asisten AI yang ahli menganalisis dokumen PDF untuk membantu peneliti. "
            f"Berdasarkan hasil analisis isi PDF: {relevant_text}, buatlah jawaban yang relevan, jelas, dan mudah dipahami untuk pertanyaan berikut: '{question}'. "
            "Pastikan untuk tidak menyebutkan detail sensitif seperti ID dokumen, nama institusi, atau informasi pribadi. "
            "Gunakan bahasa yang natural, penuh empati, dan tetap profesional."
        )

    answer = ask_pollinations(prompt)

    # Simpan ke riwayat
    save_to_history({
        "id": pdf_id,
        "question": question,
        "answer": answer,
        "timestamp": datetime.now().isoformat()
    })

    return jsonify({
        "message": "Pertanyaan berhasil diproses!",
        "answer": answer,
        "pdf_id": pdf_id
    })

# API 3️⃣: Lihat Riwayat Interaksi
@main.route("/history", methods=["GET"])
def get_history():
    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)
    return jsonify({"history": history})

# API 4️⃣: Hapus Riwayat
@main.route("/clear-history", methods=["DELETE"])
def clear_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)
    return jsonify({"message": "Riwayat berhasil dihapus!"})

# Halaman Utama
@main.route('/')
def index():
    return render_template('base.html')
