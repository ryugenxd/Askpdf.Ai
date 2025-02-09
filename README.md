# ChatPDF

![AskPdf.AI](https://github.com/lahadiyani/Askpdf.Ai/blob/main/static/image/logo.jpg)

ChatPDF adalah aplikasi berbasis web yang memungkinkan pengguna untuk berinteraksi dengan file PDF melalui chat. Aplikasi ini menggunakan Flask untuk backend, FAISS untuk pencarian berbasis vektor, dan PyMuPDF untuk ekstraksi teks dari file PDF.

## Fitur
- Upload file PDF.
- Ekstraksi teks dari PDF.
- Pencarian informasi menggunakan embedding vektor dengan FAISS.
- Chat interaktif dengan respons yang relevan berdasarkan isi PDF.
- Manajemen history chat per file PDF.
- Penambahan Room Chat

## Instalasi

### Prasyarat
- Python 3.8 atau lebih baru
- Pip

### Langkah Instalasi
1. Clone repositori ini:
   ```bash
   git clone https://github.com/username/chatpdf.git
   cd chatpdf
   ```

2. Buat virtual environment (opsional tapi direkomendasikan):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. Instal dependensi:
   ```bash
   pip install -r requirements.txt
   ```

### Dependensi
- Flask
- numpy
- faiss-cpu
- PyMuPDF
- scikit-learn
- pdfplumber

## Cara Penggunaan

1. Jalankan server Flask:
   ```bash
   python app.py
   ```

2. Akses aplikasi melalui browser di:
   ```
   http://localhost:5000
   ```

3. Upload file PDF, mulai chat, dan eksplorasi informasi dari dokumen Anda.

## API Endpoint

- **POST /upload**: Upload file PDF.
- **POST /ask**: Kirim pertanyaan untuk mendapatkan jawaban berbasis isi PDF.
- **GET /history**: Mendapatkan history chat untuk file tertentu.

## Kontribusi

1. Fork repositori ini.
2. Buat branch fitur baru: `git checkout -b fitur-baru`
3. Commit perubahan: `git commit -m 'Tambah fitur baru'`
4. Push ke branch: `git push origin fitur-baru`
5. Buat Pull Request.

## Lisensi
Proyek ini dilisensikan di bawah [MIT License](LICENSE).

## Kontak
Jika ada pertanyaan atau saran, silakan hubungi: [Email Saya](mailto:lahadiyani@gmail.com)

