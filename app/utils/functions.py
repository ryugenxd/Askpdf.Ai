import json, uuid
from app.constants.paths import UPLOAD_FOLDER, HISTORY_FILE

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

# Fungsi untuk generate ID unik untuk setiap PDF
def generate_pdf_id():
    return str(uuid.uuid4())
