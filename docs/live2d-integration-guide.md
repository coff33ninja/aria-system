# Live2D Avatar Integration Guide

## Overview

The Aria Maid System now includes comprehensive Live2D avatar support, bringing anime-style 2D avatars to life with real-time voice synchronization, personality-based expressions, and smooth parameter animations.

## Architecture

### Core Components

```
livekit_live2d/
├── __init__.py              # Package exports
├── avatar_session.py        # Main avatar session management
├── expressions.py           # Maid-specific expressions and parameters
├── audio_sync.py           # Real-time audio analysis and lip sync
└── frontend_renderer.js    # JavaScript Live2D renderer
```

### Integration Points

1. **BaseMaid Class** (`maids/base.py`)
   - Live2D avatar lifecycle management
   - Expression updates during conversation
   - Automatic cleanup on maid handoffs

2. **Individual Maids** (`maids/*/agent.py`)
   - Maid-specific Live2D model paths
   - Custom expression configurations
   - Personality-driven animations

3. **Aria Head Maid** (`agent.py`)
   - Master avatar coordination
   - Performance review expressions
   - Elegant entrance animations

## Live2D Model Structure

### Required Files per Maid

```
live2d_models/
├── aria/
│   ├── aria.model3.json     # Model configuration
│   ├── aria.moc3            # Compiled model
│   ├── aria.physics3.json   # Physics simulation
│   └── textures/            # Model textures
├── sophia/
│   ├── sophia.model3.json
│   └── ...
└── luna/
    ├── luna.model3.json
    └── ...
```

### Model Requirements

- **Live2D Cubism 4.0+** compatible models
- **Anime/manga art style** for maid café aesthetic
- **Standard parameters** for expressions and lip sync:
  - `ParamEyeLOpen`, `ParamEyeROpen` (eye opening)
  - `ParamEyeBallX`, `ParamEyeBallY` (eye direction)
  - `ParamMouthOpenY` (mouth opening for lip sync)
  - `ParamMouthForm` (mouth shape/smile)
  - `ParamAngleX`, `ParamAngleY`, `ParamAngleZ` (head rotation)
  - `ParamBodyAngleX`, `ParamBodyAngleY` (body posture)
  - `ParamBreath` (breathing animation)

## Maid Expression Profiles

### Aria - Head Maid
**Personality**: Elegant, sassy, devastatingly witty

| Expression | Eye State | Mouth | Head Angle | Description |
|------------|-----------|-------|------------|-------------|
| `idle` | Half-lidded (0.8) | Slight smirk (0.2) | Slightly turned (-5°) | Confident elegance |
| `smug` | Half-lidded (0.6) | Confident smile (0.8) | Tilted back (-3°) | Superior satisfaction |
| `sassy` | Normal (0.7) | Slight smirk (0.4) | Side glance (15°) | Delivering cutting remarks |
| `thinking` | Wide (0.9) | Slight frown (-0.1) | Tilted up (5°) | Contemplating solutions |

### Sophia - Research Maid
**Personality**: Bookish, thorough, slightly nervous

| Expression | Eye State | Mouth | Head Angle | Description |
|------------|-----------|-------|------------|-------------|
| `idle` | Normal (1.0) | Slight frown (-0.1) | Down (2°) | Reading/concentrating |
| `excited` | Wide (1.4) | Big smile (0.8) | Up (-2°) | Research breakthrough |
| `nervous` | Wide (1.2) | Worried (-0.3) | Shrinking back (-5°) | Uncertain about answer |
| `focused` | Narrowed (0.8) | Neutral (0.0) | Down (8°) | Deep concentration |

### Luna - Entertainment Maid
**Personality**: Playful, dramatic, expressive

| Expression | Eye State | Mouth | Head Angle | Description |
|------------|-----------|-------|------------|-------------|
| `idle` | Normal (1.0) | Natural smile (0.3) | Slightly turned (3°) | Relaxed and friendly |
| `playful` | Normal (0.9) | Big smile (0.7) | Tilted (12°) | Mischievous energy |
| `dramatic` | Wide (1.3) | Expressive (0.5) | Thrown back (-8°) | Theatrical performance |
| `dreamy` | Half-closed (0.6) | Soft smile (0.4) | Tilted back (-5°) | Lost in music/fantasy |

## Implementation Guide

### 1. Basic Integration

```python
# In maid agent class
class Sophia(BaseMaid):
    # Live2D configuration
    live2d_model_path = "./live2d_models/sophia/"
    
    def __init__(self, *args, **kwargs):
        from livekit_live2d.expressions import MaidExpressions
        self.live2d_expressions = MaidExpressions.get_maid_expressions("sophia")
        super().__init__(*args, **kwargs)
    
    async def on_enter(self) -> None:
        # Initialize avatar and set initial expression
        await self._initialize_avatar()
        await self.set_avatar_expression("nervous", duration=0.5)
        # ... rest of introduction
```

### 2. Context-Aware Expressions

```python
# Automatic expression updates based on conversation
async def handle_research_request(self, query: str):
    # Set focused expression when starting research
    await self.set_avatar_expression("focused", duration=0.3)
    
    # Perform research...
    result = await self.research_tool(query)
    
    # Set excited expression when presenting results
    await self.set_avatar_expression("excited", duration=0.5)
    
    return result
```

### 3. Frontend Integration

```javascript
// Initialize Live2D renderer
import { createLive2DAvatar } from './livekit_live2d/frontend_renderer.js';

const avatar = createLive2DAvatar('live2d-canvas', liveKitRoom);
await avatar.initialize();

// Handle backend messages
room.on('dataReceived', (data) => {
    const message = JSON.parse(new TextDecoder().decode(data));
    if (message.type === 'live2d_init') {
        avatar.loadMaidModel(message.maid_name, message.model_path, message);
    }
});
```

## Audio Synchronization

### Real-Time Lip Sync

The system provides automatic lip sync through audio analysis:

1. **Audio Capture**: LiveKit audio tracks are analyzed in real-time
2. **Volume Analysis**: RMS volume calculation with logarithmic scaling
3. **Mouth Animation**: Volume mapped to `ParamMouthOpenY` with natural curves
4. **Smoothing**: Exponential smoothing prevents jitter
5. **Voice Activity**: Automatic expression switching between idle/speaking

### Configuration

```python
# Audio analysis settings
class AudioAnalyzer:
    sample_rate = 48000          # LiveKit standard
    volume_smoothing = 0.7       # Higher = more smoothing
    voice_threshold = 0.01       # Voice activity detection
    
class LipSyncController:
    sensitivity = 1.0            # Mouth movement sensitivity
    smoothing_factor = 0.6       # Parameter smoothing
```

## Performance Optimizations

### Efficient Rendering

- **60 FPS Parameter Updates**: Smooth real-time animation
- **30 FPS Breathing**: Lower frequency for idle animations
- **Selective Updates**: Only changed parameters are transmitted
- **Animation Caching**: Parameter interpolation cached locally

### Memory Management

- **Model Streaming**: Models loaded on-demand per maid
- **Texture Compression**: Optimized for web delivery
- **Resource Cleanup**: Automatic cleanup on maid handoffs
- **Connection Pooling**: Reuse LiveKit data channels

## Troubleshooting

### Common Issues

1. **Model Not Loading**
   ```
   Error: Failed to load model for Sophia
   Solution: Check model path and file permissions
   ```

2. **No Lip Sync**
   ```
   Issue: Mouth not moving with voice
   Solution: Verify audio track connection and parameter names
   ```

3. **Choppy Animations**
   ```
   Issue: Jerky parameter transitions
   Solution: Increase smoothing factor or check frame rate
   ```

### Debug Mode

```python
# Enable Live2D debug logging
import logging
logging.getLogger("livekit_live2d").setLevel(logging.DEBUG)

# Check avatar session status
if maid._avatar_session:
    expressions = maid.get_avatar_expressions()
    print(f"Available expressions: {expressions}")
```

## Development Workflow

### 1. Model Creation

1. **Design**: Create anime-style character design
2. **Modeling**: Use Live2D Cubism Editor
3. **Rigging**: Set up parameters and physics
4. **Export**: Generate .model3.json and assets
5. **Testing**: Verify parameter ranges and expressions

### 2. Expression Tuning

1. **Define Personality**: Map traits to parameter values
2. **Create Presets**: Define expression parameter sets
3. **Test Transitions**: Verify smooth animation between states
4. **Context Mapping**: Link expressions to conversation context
5. **Fine-tune**: Adjust timing and intensity

### 3. Integration Testing

1. **Voice Sync**: Test lip sync accuracy with different voices
2. **Handoffs**: Verify avatar cleanup during maid switches
3. **Performance**: Monitor frame rate and memory usage
4. **Expressions**: Test all personality expressions
5. **Error Handling**: Verify graceful fallbacks

## Future Enhancements

### Planned Features

- **Interactive Gestures**: Click/touch interactions with avatars
- **Advanced Physics**: Hair and clothing movement
- **Emotion Recognition**: Automatic expression from voice tone
- **Custom Animations**: Maid-specific gesture sequences
- **Multi-Avatar**: Multiple maids visible simultaneously

### Technical Roadmap

1. **Phase 1**: Basic avatar rendering and lip sync ✅
2. **Phase 2**: Expression system and personality mapping ✅
3. **Phase 3**: Advanced audio analysis and emotion detection
4. **Phase 4**: Interactive features and gesture recognition
5. **Phase 5**: Multi-avatar support and scene composition

## Conclusion

The Live2D integration transforms the Aria Maid System from a voice-only assistant into a fully immersive anime maid café experience. Each maid's unique personality shines through their expressions and animations, creating a more engaging and emotionally connected interaction.

The system is designed for:
- **Performance**: Smooth 60 FPS animations
- **Scalability**: Easy addition of new maids and expressions
- **Maintainability**: Clean separation of concerns
- **Extensibility**: Plugin architecture for future features

With Live2D avatars, users don't just hear their maids—they see their personalities come to life with every conversation.

---

**Next Steps**: Deploy Live2D models, test real-time performance, and gather user feedback for expression refinement.