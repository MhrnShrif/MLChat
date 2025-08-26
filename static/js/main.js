const DIABETES_BG = "linear-gradient(180deg, rgba(255,255,255,0.9), rgba(245,250,255,0.9))";
const MOVIE_BG = "linear-gradient(180deg, rgba(12,12,40,0.02), rgba(18,24,60,0.05))";
const clearBtn = document.getElementById('clearHistoryBtn');
if (clearBtn) {
    clearBtn.addEventListener('click', async () => {
        if (!confirm('آیا مطمئن هستید که می‌خواهید تاریخچهٔ چت پاک شود؟')) return;
        try {
            const res = await fetch('/api/clear-history/', {
                method: 'POST',
                headers: {'X-CSRFToken': csrftoken},
                credentials: 'same-origin'
            });
            const data = await res.json();
            if (data.success) {
                messagesList.innerHTML = '';
            } else {
                alert('پاکسازی انجام نشد.');
            }
        } catch (e) {
            console.error(e);
            alert('خطا در اتصال به سرور.');
        }
    });
}

/* ====== CSRF helper ====== */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

/* ====== DOM refs ====== */
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const messagesList = document.getElementById('messagesList');
const messagesContainer = document.getElementById('messagesContainer');
const fileInput = document.getElementById('fileInput');
const chatForm = document.getElementById('chatForm');
const modelSelector = document.getElementById('modelSelector');
const currentModelInput = document.getElementById('currentModelInput');
const scrollToBottomBtn = document.getElementById('scrollToBottomBtn');
let isSending = false;

/* ====== utility: split numbered multiline messages into separate entries ====== */
function isNumberedList(lines) {
    return lines.length > 1 && lines.every(l => /^\d+\.\s+/.test(l));
}

/* ====== build a single message bubble (text only) ====== */
function buildSingleBubbleElement(sender, text) {
    const wrapper = document.createElement('div');
    wrapper.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'} message-animation`;

    const boxContainer = document.createElement('div');
    boxContainer.className = 'max-w-xs lg:max-w-md';

    const bubble = document.createElement('div');
    bubble.className = (sender === 'user')
        ? 'bg-blue-500 text-white rounded-2xl rounded-bl-sm p-4 shadow-md msg-bubble'
        : 'bg-white border border-gray-200 rounded-2xl rounded-tr-sm p-4 shadow-md msg-bubble';

    if (sender !== 'user') {
        const header = document.createElement('div');
        header.className = 'flex items-center space-x-2 space-x-reverse mb-2';
        header.innerHTML = `<div class="w-6 h-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                            </div>
                            <span class="text-xs text-gray-500 font-medium">چت بات</span>`;
        bubble.appendChild(header);
    }

    const p = document.createElement('p');
    p.className = sender === 'user' ? 'text-white' : 'text-gray-800';
    p.textContent = text;
    bubble.appendChild(p);

    boxContainer.appendChild(bubble);
    wrapper.appendChild(boxContainer);
    return wrapper;
}

/* ====== convert server chat_history item (sender, message) into DOM nodes ====== */
function buildMessageElement(sender, messageText) {
    const lines = String(messageText).split(/\r?\n/).map(l => l.trim()).filter(l => l !== '');
    if (isNumberedList(lines)) {
        const frag = document.createDocumentFragment();
        lines.forEach(line => {
            frag.appendChild(buildSingleBubbleElement(sender, line));
        });
        return frag;
    } else {
        return buildSingleBubbleElement(sender, messageText);
    }
}

/* ====== render history (replace contents) and scroll to bottom reliably ====== */
function renderChatHistory(chat_history) {
    messagesList.innerHTML = '';
    for (const item of chat_history) {
        const sender = item[0];
        const message = item[1];
        const el = buildMessageElement(sender, message);
        messagesList.appendChild(el);
    }
    const last = messagesList.lastElementChild;
    if (last) {
        try {
            last.scrollIntoView({behavior: 'smooth', block: 'end'});
        } catch (e) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    } else {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    onScrollContainer(); // update go-to-bottom button
}

/* ====== go-to-bottom button logic ====== */
function onScrollContainer() {
    const tolerance = 60; // px
    const atBottom = (messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight) <= tolerance;
    scrollToBottomBtn.style.display = atBottom ? 'none' : 'flex';
}

messagesContainer.addEventListener('scroll', onScrollContainer);
scrollToBottomBtn.addEventListener('click', () => messagesContainer.scrollTo({
    top: messagesContainer.scrollHeight,
    behavior: 'smooth'
}));

/* ====== send button state ====== */
function updateSendButtonState() {
    sendButton.disabled = !messageInput.value.trim() && !(fileInput && fileInput.files.length > 0);
}

messageInput.addEventListener('input', updateSendButtonState);
if (fileInput) fileInput.addEventListener('change', updateSendButtonState);
updateSendButtonState();

/* ====== background change depending on model ====== */
function applyBackgroundForModel(modelName) {
    if (!modelName) {
        messagesContainer.style.background = DIABETES_BG;
        messagesContainer.classList.add('bg-diabetes');
        messagesContainer.classList.remove('bg-movie');
        return;
    }
    if (modelName === 'movie') {
        messagesContainer.style.background = MOVIE_BG;
        messagesContainer.classList.add('bg-movie');
        messagesContainer.classList.remove('bg-diabetes');
    } else {
        messagesContainer.style.background = DIABETES_BG;
        messagesContainer.classList.add('bg-diabetes');
        messagesContainer.classList.remove('bg-movie');
    }
}

/* ====== AJAX submit ====== */
chatForm.addEventListener('submit', async function (e) {
    e.preventDefault();
    if (isSending) return;
    isSending = true;

    if (modelSelector) currentModelInput.value = modelSelector.value;
    const formData = new FormData(chatForm);
    if (!formData.get('user_input') && (!formData.get('test_image') || formData.get('test_image').size === 0)) {
        isSending = false;
        return;
    }

    sendButton.disabled = true;
    try {
        const res = await fetch(window.location.href, {
            method: 'POST',
            headers: {'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrftoken},
            body: formData,
            credentials: 'same-origin'
        });
        if (!res.ok) throw new Error('Network response was not ok');
        const data = await res.json();
        if (data && data.chat_history) {
            renderChatHistory(data.chat_history);
        }
        if (fileInput) fileInput.value = '';
        messageInput.value = '';
        updateSendButtonState();
        const sel = (data && data.selected_model) ? data.selected_model : (modelSelector ? modelSelector.value : null);
        applyBackgroundForModel(sel);
    } catch (err) {
        console.error('Error sending message:', err);
        const wrapper = document.createElement('div');
        wrapper.className = 'flex justify-start message-animation';
        wrapper.innerHTML = '<div class="max-w-xs lg:max-w-md"><div class="bg-white border border-gray-200 rounded-2xl p-4 shadow-md"><p class="text-gray-800">خطا در ارتباط با سرور. لطفاً دوباره تلاش کنید.</p></div></div>';
        messagesList.appendChild(wrapper);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } finally {
        sendButton.disabled = false;
        isSending = false;
    }
});

/* ====== auto submit on file select و enter behavior ====== */
if (fileInput) {
    fileInput.addEventListener('change', function () {
        if (fileInput.files.length > 0) chatForm.requestSubmit();
    });
}
messageInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.requestSubmit();
    }
});

/* ====== init ====== */
(function init() {
    const selected = "{{ selected_model|default:'' }}";
    applyBackgroundForModel(selected);
    setTimeout(() => {
        try {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        } catch (e) {
        }
    }, 40);
})();
