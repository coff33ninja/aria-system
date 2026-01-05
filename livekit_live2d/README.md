# LiveKit Live2D Integration

Anime-style Live2D avatars for the Aria Maid System with real-time voice synchronization and personality-driven expressions.

## 🎭 Features

- **Real-time Lip Sync**: Audio analysis drives mouth animations
- **Personality Expressions**: Each maid has unique facial expressions
- **Smooth Animations**: 60 FPS parameter interpolation with easing
- **Voice Activity Detection**: Automatic idle/speaking expression switching
- **Maid-Specific Models**: Custom Live2D models for each maid's personality
- **LiveKit Integration**: Seamless integration with voice handoff system

## 🏗️ Architecture

```
livekit_live2d/
├── __init__.py              # Package exports
├── avatar_session.py        # Main avatar session management
├── expressions.py           # Maid expressions and parameter definitions
├── audio_sync.py           # Real-time audio analysis and lip sync
├── frontend_renderer.js    # JavaScript Live2D renderer
├── demo.html              # Interactive demo page
└── README.md              # This file
```

## 🎌 Maid Expressions

### Aria - Head Maid
- **idle**: Confident elegance with slight smirk
- **smug**: Superior satisfaction, half-lidded eyes
- **sassy**: Side glance with cutting remark expression
- **thinking**: Contemplative with head tilted up

### Sophia - Research Maid
- **idle**: Bookish concentration, head slightly down
- **excited**: Wide eyes with research breakthrough joy
- **nervous**: Worried expression, shrinking back
- **focused**: Narrowed eyes in deep concentration

### Luna - Entertainment Maid
- **idle**: Relaxed and friendly with natural smile
- **playful**: Mischievous energy, head tilted
- **dramatic**: Theatrical performance, head thrown back
- **dreamy**: Half-closed eyes, lost in music

## 🚀 Quick Start

### 1. Basic Integration

```python
from livekit_live2d import Live2DAvatarSession, Live2DModelConfig

# Create avatar configuration
config = Live2DModelConfig(
    model_path="./live2d_models/aria/",
    maid_name="Aria",
    personality="Elegant, sassy, devastatingly witty"
)

# Create and start avatar session
avatar_session = Live2DAvatarSession(config)
await avatar_session.start(session, room)

# Change expression
await avatar_session.set_expression("smug", duration=0.5)
```

### 2. Maid Integration

```python
class Aria(BaseMaid):
    live2d_model_path = "./live2d_models/aria/"
    
    def __init__(self, *args, **kwargs):
        from livekit_live2d.expressions import MaidExpressions
        self.live2d_expressions = MaidExpressions.get_maid_expressions("aria")
        super().__init__(*args, **kwargs)
    
    async def on_enter(self):
        await self._initialize_avatar()
        await self.set_avatar_expression("idle")
```

### 3. Frontend Setup

```javascript
import { createLive2DAvatar } from './livekit_live2d/frontend_renderer.js';

const avatar = createLive2DAvatar('canvas-id', liveKitRoom);
await avatar.initialize();

// Handle model loading from backend
room.on('dataReceived', (data) => {
    const message = JSON.parse(new TextDecoder().decode(data));
    if (message.type === 'live2d_init') {
        avatar.loadMaidModel(message.maid_name, message.model_path, message);
    }
});
```

## 🎤 Audio Synchronization

### Real-time Lip Sync

```python
# Audio analysis configuration
analyzer = AudioAnalyzer(
    sample_rate=48000,
    volume_smoothing=0.7,
    voice_activity_threshold=0.01
)

# Lip sync controller
lip_sync = LipSyncController(
    sensitivity=1.0,
    smoothing_factor=0.6
)

# Process audio frame
mouth_opening = await analyzer.analyze_frame(audio_data)
parameters = await lip_sync.update_mouth_parameters(mouth_opening)
```

### Voice Activity Detection

```python
# Automatic expression switching
vad = VoiceActivityDetector(threshold=0.02, min_duration=0.1)

vad.set_callbacks(
    on_start=lambda: avatar.set_expression("speaking"),
    on_end=lambda: avatar.set_expression("idle")
)
```

## 🎨 Expression System

### Parameter Mapping

Live2D parameters used for expressions:

- `ParamEyeLOpen`, `ParamEyeROpen`: Eye opening (0.0-1.5)
- `ParamEyeBallX`, `ParamEyeBallY`: Eye direction (-1.0 to 1.0)
- `ParamMouthOpenY`: Mouth opening for lip sync (0.0-1.0)
- `ParamMouthForm`: Mouth shape (-1.0=frown, 1.0=smile)
- `ParamAngleX`, `ParamAngleY`, `ParamAngleZ`: Head rotation
- `ParamBodyAngleX`, `ParamBodyAngleY`: Body posture
- `ParamBreath`: Breathing animation (0.0-1.0)

### Custom Expressions

```python
# Define custom expression
custom_expression = {
    "ParamEyeLOpen": 0.8,
    "ParamEyeROpen": 0.8,
    "ParamMouthForm": 0.5,
    "ParamAngleY": -10.0
}

# Add to maid's expressions
expression_manager.add_custom_expression("custom", custom_expression)
```

### Context-Aware Expressions

```python
# Automatic expression based on conversation
expression = expression_manager.get_context_expression(message_content)
await avatar_session.set_expression(expression)
```

## 📁 Model Requirements

### File Structure

```
live2d_models/
├── aria/
│   ├── aria.model3.json     # Model configuration
│   ├── aria.moc3            # Compiled model data
│   ├── aria.physics3.json   # Physics simulation
│   └── textures/
│       ├── texture_00.png   # Model textures
│       └── ...
```

### Model Specifications

- **Live2D Cubism 4.0+** compatible
- **Standard parameter names** for cross-compatibility
- **Anime/manga art style** for maid café aesthetic
- **Optimized textures** for web delivery (< 2MB total)
- **Physics simulation** for natural movement

## 🔧 Configuration

### Environment Variables

```bash
# Enable Live2D avatars
ARIA_ENABLE_LIVE2D=true

# Model directory
ARIA_LIVE2D_MODELS_DIR=./live2d_models

# Performance settings
ARIA_LIVE2D_FPS=60
ARIA_LIVE2D_AUDIO_SAMPLE_RATE=48000
```

### Performance Tuning

```python
# Adjust animation quality vs performance
config = Live2DModelConfig(
    animation_speed=1.0,        # Animation speed multiplier
    lip_sync_sensitivity=1.0,   # Mouth movement sensitivity
    default_expression="idle"   # Starting expression
)
```

## 🐛 Troubleshooting

### Common Issues

1. **Model Not Loading**
   ```
   Error: Failed to load model
   Solution: Check file paths and permissions
   ```

2. **No Audio Sync**
   ```
   Issue: Mouth not moving with voice
   Solution: Verify LiveKit audio track connection
   ```

3. **Choppy Animation**
   ```
   Issue: Jerky movements
   Solution: Increase smoothing factor or check frame rate
   ```

### Debug Mode

```python
import logging
logging.getLogger("livekit_live2d").setLevel(logging.DEBUG)

# Check avatar status
if avatar_session.model_loaded:
    print(f"Expressions: {avatar_session.expression_manager.list_available_expressions()}")
```

## 🎯 Demo

### Static Demo (No LiveKit)

Open `demo.html` in a web browser to see an interactive demonstration of the Live2D system:

- Switch between different maids
- Test facial expressions
- Simulate lip sync with volume controls
- Monitor real-time status

### LiveKit + Live2D Demo

For the full experience with real-time voice and lip sync via LiveKit:

1. **Start the token server** (serves files and generates LiveKit tokens):
   ```bash
   python livekit_live2d/token_server.py
   ```

2. **Open the demo** at: `http://localhost:8080/livekit_live2d/livekit-demo.html`

3. **Connect** to your LiveKit room and start talking with Aria!

The token server:
- Serves static files from the project root
- Auto-generates LiveKit access tokens at `/api/token`
- Requires `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` in your `.env` file

**Token endpoint**: `/api/token?room=aria-room&identity=web-user`

## 📚 API Reference

### Live2DAvatarSession

```python
class Live2DAvatarSession:
    async def start(session, room) -> None
    async def stop() -> None
    async def set_expression(name: str, duration: float = 0.5) -> None
```

### ExpressionManager

```python
class ExpressionManager:
    def get_expression(name: str) -> Dict[str, float]
    def get_context_expression(message: str) -> str
    def add_custom_expression(name: str, params: Dict[str, float]) -> None
```

### AudioAnalyzer

```python
class AudioAnalyzer:
    async def analyze_frame(audio_data: bytes) -> float
    def get_breathing_pattern() -> float
    def get_voice_activity() -> bool
```

## 🔮 Future Enhancements

- **Interactive Gestures**: Click/touch avatar interactions
- **Advanced Physics**: Hair and clothing movement
- **Emotion Recognition**: Automatic expressions from voice tone
- **Multi-Avatar Support**: Multiple maids visible simultaneously
- **Custom Animations**: Maid-specific gesture sequences

## 📄 License

Part of the Aria Maid System. See main project LICENSE for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add Live2D models or expressions
4. Test with the demo page
5. Submit a pull request

---

**Transform your voice assistant into an immersive anime maid café experience! 🎭✨**