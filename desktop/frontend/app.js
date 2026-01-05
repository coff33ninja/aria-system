/**
 * Aria Maid System - Desktop Mode Frontend
 * 
 * Handles:
 * - WebSocket connection to Python backend
 * - Live2D avatar rendering and animation
 * - Chat interface and transcript display
 * - Voice input/output controls
 */

// Configuration
const WS_URL = 'ws://localhost:8765';
const RECONNECT_DELAY = 3000;

// Maid configurations
const MAIDS = {
    aria: {
        name: "Aria",
        modelPath: "/live2d/models/aria/长离.model3.json",
        hasModel: true,
        color: "#ff6b9d",
        expressions: ["coat_toggle", "heart_eyes", "angry", "eye_roll", "eye_mask", "blush", "dark_face"]
    },
    sophia: { name: "Sophia", modelPath: null, hasModel: false, color: "#9b59b6" },
    luna: {
        name: "Luna",
        modelPath: "/live2d/models/luna/Nicole.model3.json",
        hasModel: true,
        color: "#3498db",
        expressions: ["black face", "cry", "Love eye", "Love Hand Posture", "Milk Tea", "Money eye", "Money Hand Posture", "Phone Hand Posture", "shyness", "sitting position", "Y Hand Posture"]
    },
    rose: { name: "Rose", modelPath: null, hasModel: false, color: "#e74c3c" },
    mei: { name: "Mei", modelPath: null, hasModel: false, color: "#2ecc71" },
    clara: { name: "Clara", modelPath: null, hasModel: false, color: "#f39c12" }
};

// State
let ws = null;
let pixiApp = null;
let live2dModel = null;
let currentMaid = 'aria';
let isConnected = false;
let reconnectTimer = null;

// DOM Elements
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const loadingOverlay = document.getElementById('loading-overlay');
const loadingText = document.getElementById('loading-text');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const currentMaidBadge = document.getElementById('current-maid-badge');
const maidSelector = document.getElementById('maid-selector');
const micBtn = document.getElementById('mic-btn');
const speakerBtn = document.getElementById('speaker-btn');
const canvas = document.getElementById('live2d-canvas');

// ============================================================================
// WebSocket Connection
// ============================================================================

function connectWebSocket() {
    updateStatus('connecting', 'Connecting...');
    loadingText.textContent = 'Connecting to Aria...';
    
    try {
        ws = new WebSocket(WS_URL);
        
        ws.onopen = () => {
            console.log('✅ WebSocket connected');
            isConnected = true;
            updateStatus('connected', 'Connected');
            loadingOverlay.classList.add('hidden');
            
            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
                reconnectTimer = null;
            }
        };
        
        ws.onclose = () => {
            console.log('❌ WebSocket disconnected');
            isConnected = false;
            updateStatus('disconnected', 'Disconnected');
            scheduleReconnect();
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateStatus('disconnected', 'Error');
        };
        
        ws.onmessage = (event) => {
            handleMessage(JSON.parse(event.data));
        };
        
    } catch (error) {
        console.error('Failed to connect:', error);
        updateStatus('disconnected', 'Failed');
        scheduleReconnect();
    }
}

function scheduleReconnect() {
    if (reconnectTimer) return;
    
    loadingOverlay.classList.remove('hidden');
    loadingText.textContent = 'Reconnecting...';
    
    reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connectWebSocket();
    }, RECONNECT_DELAY);
}

function updateStatus(status, text) {
    statusDot.className = 'status-dot ' + status;
    statusText.textContent = text;
}

// ============================================================================
// Message Handling
// ============================================================================

function handleMessage(data) {
    switch (data.type) {
        case 'init':
            handleInit(data);
            break;
            
        case 'transcript':
            handleTranscript(data);
            break;
            
        case 'handoff':
            handleHandoff(data);
            break;
            
        case 'live2d_param':
            handleLive2DParam(data);
            break;
            
        case 'expression':
            handleExpression(data);
            break;
            
        case 'status':
            handleStatusUpdate(data);
            break;
            
        case 'history':
            handleHistory(data);
            break;
            
        case 'pong':
            // Heartbeat response
            break;
            
        default:
            console.log('Unknown message type:', data.type);
    }
}

function handleInit(data) {
    console.log('📥 Received init:', data);
    
    // Load conversation history
    if (data.conversation && data.conversation.messages) {
        chatMessages.innerHTML = '';
        data.conversation.messages.forEach(msg => {
            addMessage(msg.content, msg.role, msg.maid, false);
        });
        scrollToBottom();
    }
    
    // Set current maid
    if (data.current_maid) {
        setCurrentMaid(data.current_maid);
    }
}

function handleTranscript(data) {
    addMessage(data.text, data.is_user ? 'user' : 'assistant', data.maid);
    
    // Animate mouth for assistant speech
    if (!data.is_user && live2dModel) {
        animateSpeaking(data.text.length);
    }
}

function handleHandoff(data) {
    console.log(`🎭 Handoff: ${data.from_maid} → ${data.to_maid}`);
    
    addMessage(`${data.from_maid} → ${data.to_maid}`, 'system');
    setCurrentMaid(data.to_maid);
    
    // Load new maid's model if available
    loadMaidModel(data.to_maid);
}

function handleLive2DParam(data) {
    if (live2dModel) {
        setModelParameter(data.param, data.value);
    }
}

function handleExpression(data) {
    if (live2dModel) {
        setExpression(data.expression);
    }
}

function handleStatusUpdate(data) {
    console.log('Status update:', data.status, data.details);
}

function handleHistory(data) {
    if (data.conversation && data.conversation.messages) {
        chatMessages.innerHTML = '';
        data.conversation.messages.forEach(msg => {
            addMessage(msg.content, msg.role, msg.maid, false);
        });
        scrollToBottom();
    }
}

// ============================================================================
// Chat Interface
// ============================================================================

function addMessage(text, role, maid = null, animate = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    if (role === 'assistant' && maid) {
        const header = document.createElement('div');
        header.className = 'message-header';
        header.textContent = MAIDS[maid]?.name || maid;
        messageDiv.appendChild(header);
    }
    
    const content = document.createElement('div');
    content.textContent = text;
    messageDiv.appendChild(content);
    
    if (!animate) {
        messageDiv.style.animation = 'none';
    }
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || !isConnected) return;
    
    // Send to backend
    ws.send(JSON.stringify({
        type: 'user_text',
        text: text
    }));
    
    chatInput.value = '';
}

function setCurrentMaid(maidId) {
    currentMaid = maidId;
    const maid = MAIDS[maidId];
    
    // Update badge
    currentMaidBadge.textContent = maid?.name || maidId;
    currentMaidBadge.style.background = maid?.color || '#ff6b9d';
    
    // Update selector buttons
    document.querySelectorAll('.maid-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.maid === maidId);
    });
}

// ============================================================================
// Live2D Avatar
// ============================================================================

async function initLive2D() {
    loadingText.textContent = 'Loading Live2D...';
    
    try {
        pixiApp = new PIXI.Application({
            view: canvas,
            autoStart: true,
            resizeTo: canvas.parentElement,
            backgroundColor: 0x1a1a2e,
            antialias: true
        });
        
        await loadMaidModel('aria');
        
    } catch (error) {
        console.error('Failed to initialize Live2D:', error);
        loadingText.textContent = 'Live2D failed to load';
    }
}

async function loadMaidModel(maidId) {
    const maid = MAIDS[maidId];
    
    if (!maid || !maid.hasModel || !maid.modelPath) {
        console.log(`No model available for ${maidId}`);
        return;
    }
    
    loadingOverlay.classList.remove('hidden');
    loadingText.textContent = `Loading ${maid.name}...`;
    
    try {
        // Remove existing model
        if (live2dModel) {
            pixiApp.stage.removeChild(live2dModel);
            live2dModel.destroy();
            live2dModel = null;
        }
        
        // Load new model
        live2dModel = await PIXI.live2d.Live2DModel.from(maid.modelPath, {
            autoInteract: true,
            autoUpdate: true
        });
        
        // Scale and position
        resizeModel();
        
        // Enable interaction
        live2dModel.interactive = true;
        live2dModel.on('hit', (hitAreas) => {
            console.log('Hit:', hitAreas);
            if (hitAreas.includes('body') || hitAreas.includes('Body')) {
                live2dModel.motion('tap_body');
            } else if (hitAreas.includes('head') || hitAreas.includes('Head')) {
                live2dModel.motion('flick_head');
            }
        });
        
        pixiApp.stage.addChild(live2dModel);
        
        console.log(`✅ Loaded model for ${maid.name}`);
        loadingOverlay.classList.add('hidden');
        
    } catch (error) {
        console.error(`Failed to load model for ${maidId}:`, error);
        loadingOverlay.classList.add('hidden');
    }
}

function resizeModel() {
    if (!live2dModel || !pixiApp) return;
    
    const scale = Math.min(
        pixiApp.screen.width / live2dModel.width * 0.8,
        pixiApp.screen.height / live2dModel.height * 0.9
    );
    live2dModel.scale.set(scale);
    live2dModel.x = pixiApp.screen.width / 2;
    live2dModel.y = pixiApp.screen.height / 2 + live2dModel.height * scale * 0.3;
    live2dModel.anchor.set(0.5, 0.5);
}

function setModelParameter(paramId, value) {
    if (!live2dModel || !live2dModel.internalModel || !live2dModel.internalModel.coreModel) return;
    
    try {
        const coreModel = live2dModel.internalModel.coreModel;
        const index = coreModel.getParameterIndex(paramId);
        if (index >= 0) {
            coreModel.setParameterValueByIndex(index, value);
        }
    } catch (e) {
        // Parameter might not exist
    }
}

function setExpression(name) {
    if (!live2dModel) return;
    
    try {
        live2dModel.expression(name);
        console.log(`Expression: ${name}`);
    } catch (e) {
        console.error('Expression error:', e);
    }
}

function animateSpeaking(textLength) {
    if (!live2dModel) return;
    
    // Simple mouth animation based on text length
    const duration = Math.min(textLength * 50, 3000);
    const startTime = Date.now();
    
    function animate() {
        const elapsed = Date.now() - startTime;
        if (elapsed > duration) {
            setModelParameter('ParamMouthOpenY', 0);
            return;
        }
        
        // Oscillate mouth
        const value = Math.sin(elapsed / 100) * 0.5 + 0.3;
        setModelParameter('ParamMouthOpenY', Math.max(0, value));
        
        requestAnimationFrame(animate);
    }
    
    animate();
}

// ============================================================================
// Event Listeners
// ============================================================================

// Send message
sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// Maid selector (for manual switching - mainly for testing)
maidSelector.addEventListener('click', (e) => {
    if (e.target.classList.contains('maid-btn')) {
        const maidId = e.target.dataset.maid;
        // Note: In production, maid switching is done via voice commands to Aria
        console.log(`Selected maid: ${maidId} (use voice to switch)`);
    }
});

// Voice controls (placeholder - actual implementation in agent.py)
micBtn.addEventListener('click', () => {
    micBtn.classList.toggle('active');
    console.log('Mic toggled - voice input handled by Python backend');
});

speakerBtn.addEventListener('click', () => {
    speakerBtn.classList.toggle('active');
    console.log('Speaker toggled');
});

// Window resize
window.addEventListener('resize', () => {
    if (pixiApp) {
        pixiApp.renderer.resize(canvas.parentElement.clientWidth, canvas.parentElement.clientHeight);
        resizeModel();
    }
});

// ============================================================================
// Initialization
// ============================================================================

async function init() {
    console.log('🎭 Aria Maid System - Desktop Mode');
    
    // Initialize Live2D
    await initLive2D();
    
    // Connect to backend
    connectWebSocket();
    
    // Heartbeat
    setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
        }
    }, 30000);
}

// Start
init();
