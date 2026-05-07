// State Management
const STATE = {
    IDLE: 'IDLE',
    LISTENING: 'LISTENING',
    THINKING: 'THINKING',
    SPEAKING: 'SPEAKING'
};

let currentState = STATE.IDLE;
let continuousMode = false;
let hasStartedListening = false;
let recognitionActive = false;
let agentSpeaking = false;
let micPermissionGranted = false;
const DEFAULT_GREETING = 'Namaste, main Rupeezy AI Agent bol raha hoon. Aapka naam kya hai aur aap professionally kya karte hain?';
let sessionId = sessionStorage.getItem('rupeezy_session_id') || `lead_${Date.now()}`;
sessionStorage.setItem('rupeezy_session_id', sessionId);
const API_BASE_URL = (window.RUPEEZY_API_BASE_URL || '').replace(/\/$/, '');

function selectedRecognitionLang() {
    return languageSelect.selectedOptions[0]?.dataset.recognitionLang || 'en-IN';
}

function selectedLanguage() {
    return languageSelect.value || 'auto';
}

// DOM Elements
const micBtn = document.getElementById('mic-btn');
const statusText = document.getElementById('status-text');
const chatWindow = document.getElementById('chat-window');
const errorToast = document.getElementById('error-toast');
const micDeniedBanner = document.getElementById('mic-denied-banner');
const protocolWarning = document.getElementById('protocol-warning');
const textForm = document.getElementById('text-form');
const textInput = document.getElementById('text-input');
const sendBtn = document.getElementById('send-btn');
const languageSelect = document.getElementById('language-select');
const newLeadBtn = document.getElementById('new-lead-btn');

function isSupportedFrontendOrigin() {
    return window.isSecureContext;
}

if (!isSupportedFrontendOrigin()) {
    protocolWarning.classList.remove('hidden');
    showToast('Please open the app from a secure origin.');
}

// Audio Context for fallback TTS
const synth = window.speechSynthesis;
let currentAudio = null;

// Speech Recognition Setup
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.lang = selectedRecognitionLang();
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.maxAlternatives = 3;

    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(bestTranscript)
            .join(' ');
        
        if (event.results[0].isFinal) {
            recognitionActive = false;
            console.log('[STT] Transcript received', transcript);
            handleUserSpeech(transcript);
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        recognitionActive = false;
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
            micDeniedBanner.classList.remove('hidden');
            stopContinuousMode();
            return;
        }
        if (event.error !== 'no-speech') {
            showToast(`Mic error: ${event.error}`);
        }
        if (continuousMode && !agentSpeaking && currentState === STATE.LISTENING) {
            restartRecognitionSoon();
        } else if (!continuousMode) {
            updateState(STATE.IDLE);
        }
    };

    recognition.onend = () => {
        recognitionActive = false;
        if (continuousMode && !agentSpeaking && currentState === STATE.LISTENING) {
            restartRecognitionSoon();
        } else if (!continuousMode && currentState === STATE.LISTENING) {
            updateState(STATE.IDLE);
        }
    };
} else {
    showToast("Speech Recognition not supported in this browser.");
}

// State Controller
function updateState(newState) {
    currentState = newState;
    micBtn.className = 'mic-btn';
    const busy = newState === STATE.THINKING || newState === STATE.SPEAKING;
    sendBtn.disabled = busy;
    textInput.disabled = busy;
    languageSelect.disabled = newState !== STATE.IDLE;
    
    switch (newState) {
        case STATE.IDLE:
            statusText.innerText = 'Ready';
            break;
        case STATE.LISTENING:
            micBtn.classList.add('listening');
            statusText.innerText = 'Listening...';
            break;
        case STATE.THINKING:
            micBtn.classList.add('thinking');
            statusText.innerText = 'Processing...';
            break;
        case STATE.SPEAKING:
            micBtn.classList.add('speaking');
            statusText.innerText = 'Agent Speaking...';
            break;
    }
}

// UI Helpers
function showToast(message) {
    errorToast.innerText = message;
    errorToast.classList.add('show');
    setTimeout(() => errorToast.classList.remove('show'), 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function appendMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}-message`;
    
    const avatar = role === 'bot' ? '<div class="avatar">R</div>' : '';
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    msgDiv.innerHTML = `
        ${avatar}
        <div class="message-content">
            <p>${escapeHtml(text)}</p>
            <span class="timestamp">${now}</span>
        </div>
    `;
    
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function resetChatWindow() {
    chatWindow.innerHTML = '';
    appendMessage('bot', DEFAULT_GREETING);
}

function startNewLeadSession() {
    stopContinuousMode();
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    sessionId = `lead_${Date.now()}`;
    sessionStorage.setItem('rupeezy_session_id', sessionId);
    textInput.value = '';
    resetChatWindow();
    updateState(STATE.IDLE);
    showToast('New lead session started.');
}

function bestTranscript(result) {
    let best = result[0];
    for (let i = 1; i < result.length; i += 1) {
        if ((result[i].confidence || 0) > (best.confidence || 0)) {
            best = result[i];
        }
    }
    return best.transcript;
}

function shouldIgnoreTranscript(transcript) {
    const cleaned = transcript.trim().toLowerCase();
    if (!cleaned) return true;
    const words = cleaned.split(/\s+/).filter(Boolean);
    const noiseWords = new Set(['uh', 'um', 'hmm', 'hm', 'ah', 'aa', 'noise']);
    return words.length === 1 && (cleaned.length < 4 || noiseWords.has(cleaned));
}

async function ensureMicPermission() {
    if (micPermissionGranted) return true;
    if (!navigator.mediaDevices?.getUserMedia) {
        showToast('Microphone permission API is unavailable. Use Chrome or Edge on a secure origin.');
        return false;
    }
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach((track) => track.stop());
        micPermissionGranted = true;
        micDeniedBanner.classList.add('hidden');
        console.log('[Mic] Permission granted');
        return true;
    } catch (error) {
        console.error(error);
        micDeniedBanner.classList.remove('hidden');
        showToast('Microphone permission failed. Please allow mic access.');
        return false;
    }
}

async function startContinuousMode() {
    if (!recognition) {
        showToast("Speech Recognition not supported.");
        return;
    }
    if (!isSupportedFrontendOrigin()) {
        protocolWarning.classList.remove('hidden');
        showToast('Please open the app from a secure origin.');
        return;
    }
    const ok = await ensureMicPermission();
    if (!ok) return;
    hasStartedListening = true;
    continuousMode = true;
    startRecognition();
}

function stopContinuousMode() {
    continuousMode = false;
    agentSpeaking = false;
    if (recognitionActive && recognition) {
        try {
            recognition.stop();
        } catch (error) {
            console.error(error);
        }
    }
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    recognitionActive = false;
    updateState(STATE.IDLE);
}

function startRecognition() {
    if (!recognition || recognitionActive || agentSpeaking || !continuousMode) return;

    try {
        recognition.lang = selectedRecognitionLang();
        recognition.start();
        recognitionActive = true;
        console.log('[STT] Listening started');
        updateState(STATE.LISTENING);
    } catch (error) {
        console.error(error);
        recognitionActive = false;
    }
}

function restartRecognitionSoon() {
    if (!continuousMode || agentSpeaking) return;
    window.setTimeout(() => {
        if (continuousMode && !agentSpeaking && currentState === STATE.LISTENING) {
            startRecognition();
        }
    }, 250);
}

function resumeContinuousListening() {
    agentSpeaking = false;
    currentAudio = null;
    if (continuousMode) {
        console.log('[STT] Listening resumed');
        startRecognition();
    } else {
        updateState(STATE.IDLE);
    }
}

// Core Logic
async function handleUserSpeech(transcript) {
    if (shouldIgnoreTranscript(transcript)) {
        console.log('[STT] Ignored noisy transcript', transcript);
        if (continuousMode) startRecognition();
        return;
    }

    appendMessage('user', transcript);
    updateState(STATE.THINKING);

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                message: transcript,
                language: selectedLanguage()
            }),
            signal: AbortSignal.timeout(15000)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Backend request failed');
        }

        const data = await response.json();
        appendMessage('bot', data.response);
        playResponse(data.response, data);

    } catch (error) {
        console.error(error);
        showToast(error.name === 'TimeoutError' ? "Response took too long." : error.message);
        if (continuousMode) {
            startRecognition();
        } else {
            updateState(STATE.IDLE);
        }
    }
}

function playResponse(text, data) {
    if (recognitionActive && recognition) {
        recognitionActive = false;
        try {
            recognition.stop();
        } catch (error) {
            console.error(error);
        }
    }
    agentSpeaking = true;
    updateState(STATE.SPEAKING);

    if (data.audio_stream_url) {
        const audio = new Audio(`${API_BASE_URL}${data.audio_stream_url}`);
        audio.preload = 'auto';
        audio.playbackRate = 1.0;
        currentAudio = audio;
        audio.oncanplay = () => {
            console.log('[Audio] Stream has first playable data');
        };
        audio.onended = () => {
            console.log('[Audio] Stream playback ended');
            resumeContinuousListening();
        };
        audio.onerror = () => {
            console.warn('[Audio] Stream failed, trying base64 fallback');
            playFallbackAudio(text);
        };
        audio.play().then(() => {
            console.log('[Audio] Stream playback started');
        }).catch((error) => {
            console.error(error);
            showToast("Browser blocked audio playback. Click or type again.");
            resumeContinuousListening();
        });
    } else if (data.audio_base64) {
        const mimeType = data.audio_mime_type || 'audio/mpeg';
        const audio = new Audio(`data:${mimeType};base64,${data.audio_base64}`);
        audio.playbackRate = 1.0;
        currentAudio = audio;
        audio.onended = () => {
            console.log('[Audio] Playback ended');
            resumeContinuousListening();
        };
        audio.onerror = () => {
            showToast("Could not play Sarvam audio.");
            resumeContinuousListening();
        };
        audio.play().then(() => {
            console.log('[Audio] Playback started');
        }).catch((error) => {
            console.error(error);
            showToast("Browser blocked audio playback. Click or type again.");
            resumeContinuousListening();
        });
    } else if (data.audio_url) {
        const audio = new Audio(`${API_BASE_URL}${data.audio_url}`);
        audio.playbackRate = 1.0;
        currentAudio = audio;
        audio.onended = () => {
            console.log('[Audio] Playback ended');
            resumeContinuousListening();
        };
        audio.onerror = () => {
            showToast("Could not play Sarvam audio.");
            resumeContinuousListening();
        };
        audio.play().then(() => {
            console.log('[Audio] Playback started');
        }).catch((error) => {
            console.error(error);
            showToast("Browser blocked audio playback. Click or type again.");
            resumeContinuousListening();
        });
    } else {
        showToast(data.tts_error || "No Sarvam audio returned.");
        resumeContinuousListening();
    }
}

async function playFallbackAudio(text) {
    try {
        const response = await fetch(`${API_BASE_URL}/tts/fallback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                message: text,
                language: selectedLanguage()
            }),
            signal: AbortSignal.timeout(15000)
        });
        if (!response.ok) {
            throw new Error('Fallback audio failed');
        }
        const data = await response.json();
        if (!data.audio_base64) {
            throw new Error(data.tts_error || 'No fallback audio returned');
        }
        playResponse(text, data);
    } catch (error) {
        console.error(error);
        showToast(error.message);
        resumeContinuousListening();
    }
}

function fallbackTTS(text) {
    if (!synth) {
        updateState(STATE.IDLE);
        return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'hi-IN';
    utterance.onend = () => updateState(STATE.IDLE);
    synth.speak(utterance);
}

// Event Listeners
micBtn.addEventListener('click', async () => {
    if (continuousMode) {
        stopContinuousMode();
        return;
    }
    await startContinuousMode();
});

languageSelect.addEventListener('change', () => {
    if (recognition) {
        recognition.lang = selectedRecognitionLang();
    }
});

newLeadBtn.addEventListener('click', startNewLeadSession);

textForm.addEventListener('submit', (event) => {
    event.preventDefault();
    if (currentState === STATE.SPEAKING || currentState === STATE.THINKING) return;
    const message = textInput.value.trim();
    if (!message) return;
    if (continuousMode && recognitionActive && recognition) {
        recognitionActive = false;
        try {
            recognition.stop();
        } catch (error) {
            console.error(error);
        }
    }
    textInput.value = '';
    handleUserSpeech(message);
});

updateState(STATE.IDLE);
