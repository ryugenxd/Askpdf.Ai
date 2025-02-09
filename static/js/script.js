// 🚩 Inisialisasi Elemen DOM
const uploadButton = document.getElementById('upload');
const fileInput = document.getElementById('file-upload');
const sendButton = document.getElementById('send-button');
const chatInput = document.getElementById('chat-input');
const chatContainer = document.getElementById('chat-container');
const typingIndicator = document.getElementById('typing-indicator');
const historyContainer = document.querySelector('.room-chat');

// 🚩 Fungsi Upload PDF
uploadButton.addEventListener('click', () => {
    fileInput.click();
    fileInput.removeEventListener('change', handleFileUpload);
    fileInput.addEventListener('change', handleFileUpload);
});

function handleFileUpload() {
    const file = this.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.pdf_id) {
                localStorage.setItem('pdf_id', data.pdf_id);
                alert('✅ PDF berhasil diunggah!');
                loadHistory();
            } else {
                console.error('❌ Upload gagal:', data.error);
            }
        })
        .catch(error => console.error('❌ Error:', error));
    } else {
        alert('🚨 Harap pilih file PDF.');
    }
}

// 🚩 Fungsi Kirim Pesan
function sendMessage() {
    const message = chatInput.value.trim();
    const pdfId = localStorage.getItem('pdf_id');

    if (message && pdfId) {
        const formData = new FormData();
        formData.append('question', message);
        formData.append('pdf_id', pdfId);

        appendMessage('person', message);
        showTypingIndicator();

        fetch('/ask', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideTypingIndicator();
            if (data.answer?.trim()) {
                appendMessage('ai', formatMarkdown(data.answer));
                chatInput.value = '';
                chatContainer.style.display = 'flex';
                loadHistory();
            } else {
                appendMessage('ai', '⚠️ Maaf, saya tidak menemukan jawaban yang sesuai.');
            }
        })
        .catch(error => {
            hideTypingIndicator();
            console.error('❌ Error:', error);
            appendMessage('ai', '❗ Terjadi kesalahan saat memproses data.');
        });
    } else {
        alert('🚨 Harap unggah PDF terlebih dahulu!');
    }
}

// 🚩 Event Listener untuk Tombol "Send"
sendButton.addEventListener('click', sendMessage);

// 🚩 Event Listener untuk "Enter" (Shift + Enter untuk newline)
chatInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

// 🚩 Fungsi Tambah Pesan ke Chat
function appendMessage(sender, message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = sender === 'person' ? 'person-chat' : 'ai-chat';
    const formattedMessage = sender === 'ai' ? formatMarkdown(message) : message;

    messageDiv.innerHTML = `
        <div class="message-bubble ${sender}-message">${formattedMessage}</div>
    `;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}


function formatMarkdown(text) {
    // **Bold**
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // *Italic*
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Heading (misalnya "Langkah-langkah:")
    text = text.replace(/(^|\n)([A-Z][\w\s]+):/g, '<strong>$2:</strong>');

    // Daftar terurut (1. Item, 2. Item)
    text = text.replace(/((?:\d+\.\s.*(?:\n|$))+)/g, match => {
        const items = match.trim().split('\n').map(item => item.replace(/\d+\.\s(.*)/, '<li>$1</li>')).join('');
        return `<ol>${items}</ol>`;
    });

    // Daftar tidak terurut (- Item)
    text = text.replace(/((?:- .*(?:\n|$))+)/g, match => {
        const items = match.trim().split('\n').map(item => item.replace(/- (.*)/, '<li>$1</li>')).join('');
        return `<ul>${items}</ul>`;
    });

    // Line breaks
    text = text.replace(/\n/g, '<br>');

    return text.trim();
}

// 🚩 Indikator "Typing" untuk AI
function showTypingIndicator() {
    typingIndicator.style.display = 'flex';
}

function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

// 🚩 Fungsi Load Riwayat Chat
function loadHistory() {
    fetch('/history')
        .then(response => response.json())
        .then(data => {
            historyContainer.innerHTML = '';
            historyContainer.style.display = 'flex';

            const pdfId = localStorage.getItem('pdf_id');
            const filteredHistory = data.history.filter(entry => entry.id === pdfId);

            filteredHistory.forEach(entry => {
                const historyItem = document.createElement('div');
                historyItem.classList.add('room');
                historyItem.innerHTML = `
                    <strong>❓ ${entry.question}</strong>
                    <small>🗓️ ${new Date(entry.timestamp).toLocaleString()}</small>
                `;
                historyContainer.appendChild(historyItem);
            });

            historyContainer.scrollTop = historyContainer.scrollHeight;
        })
        .catch(error => console.error('❌ Gagal memuat riwayat:', error));
}
