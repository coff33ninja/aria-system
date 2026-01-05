# Voice Delay Research & Optimization

## Problem Statement

User reported voice delay or detection issues from master when interacting with Aria. The system was experiencing delays in detecting when the user finished speaking, leading to slower response times.

## Initial Investigation

### Attempted Solution 1: VAD Parameters (Failed)
**Date**: Previous session  
**Approach**: Tried to add Voice Activity Detection (VAD) parameters to the RealtimeModel configuration:
- `vad_threshold`
- `vad_prefix_padding_ms` 
- `vad_silence_timeout_ms`

**Result**: FAILED - These parameters don't exist in LiveKit's RealtimeModel API. Removed invalid parameters.

**Code Location**: `agent.py` - `get_realtime_model()` function

## Research Findings

### LiveKit Voice Detection Documentation

Found key information about LiveKit's voice detection system:

1. **Default End-of-Utterance Delay**: 500ms (`min_endpointing_delay`)
2. **EOU Transformer Model**: Semantic turn detection for better conversation flow
3. **Session-level VAD Configuration**: Available through AgentSession parameters

### Key Parameters Identified

#### `min_endpointing_delay`
- **Default**: 500ms
- **Purpose**: Minimum delay before considering utterance complete
- **Impact**: Lower values = faster response, higher risk of cutting off user
- **Configuration**: Set at AgentSession level, not RealtimeModel level

#### EOU (End of Utterance) Model
- **Purpose**: Uses semantic understanding to detect natural conversation breaks
- **Benefit**: More accurate than simple silence detection
- **Implementation**: Requires specific model configuration

## Current System Configuration

### Voice Models
```python
# Google (Current Primary)
google.realtime.RealtimeModel(
    model="gemini-2.5-flash-native-audio-preview-12-2025",
    voice="Aoede",
    temperature=0.9,
)

# OpenAI (Fallback)
openai.realtime.RealtimeModel(
    voice="shimmer",
)
```

### Maid Voice Configurations
- **Aria**: Aoede (Google) / Shimmer (OpenAI)
- **Sophia**: Kore (Google) - Research maid
- **Luna**: Leda (Google) - Entertainment maid
- **Rose**: Fenrir (Google) - Scheduling maid
- **Mei**: Puck (Google) - Smart Home maid
- **Clara**: Aoede (Google) - Communication maid

## Potential Solutions

### 1. Session-Level VAD Configuration
**Status**: Not yet implemented  
**Approach**: Configure VAD parameters at AgentSession level rather than model level

```python
# Potential implementation in agent session
session_config = {
    "min_endpointing_delay": 300,  # Reduce from 500ms default
    "vad_threshold": 0.5,          # If available at session level
}
```

### 2. EOU Transformer Model
**Status**: Research phase  
**Approach**: Implement semantic turn detection for more natural conversation flow

### 3. Provider Comparison Testing
**Status**: Available for testing  
**Approach**: Compare voice detection performance between Google and OpenAI providers

### 4. Audio Pipeline Optimization
**Status**: Not investigated  
**Approach**: Optimize audio processing pipeline for faster detection

## Next Steps

1. **Research AgentSession VAD Configuration**
   - Investigate available parameters for AgentSession
   - Test `min_endpointing_delay` reduction
   - Document optimal values for different use cases

2. **Implement EOU Model**
   - Research EOU transformer model integration
   - Test semantic turn detection vs silence-based detection
   - Measure improvement in conversation flow

3. **Provider Performance Testing**
   - A/B test Google vs OpenAI voice detection speed
   - Measure latency differences
   - Document optimal provider for different scenarios

4. **Audio Pipeline Analysis**
   - Profile audio processing pipeline
   - Identify bottlenecks in voice detection
   - Optimize for faster response times

## Technical Notes

### File Locations
- **Main Agent**: `agent.py` - Aria class and voice configuration
- **Maid Base**: `maids/base.py` - BaseMaid voice configuration
- **Voice Models**: `get_realtime_model()` function in `agent.py`

### Key Dependencies
- `livekit-agents` - Core voice agent framework
- `livekit-plugins-google` - Google Gemini Live integration
- `livekit-plugins-openai` - OpenAI Realtime API integration

### Environment Variables
- `LLM_PROVIDER` - "google" or "openai"
- `GEMINI_API_KEYS` - Comma-separated Google API keys
- `OPENAI_API_KEY` - OpenAI API key

## Implementation Status

### ✅ IMPLEMENTED: Session-Level VAD Configuration
**Date**: Current session  
**Approach**: Added `min_endpointing_delay=300` to AgentSession configuration
**Location**: `agent.py` - `entrypoint()` function
**Change**: Reduced from 500ms default to 300ms for faster response
**Expected Impact**: 40% reduction in voice detection delay

```python
# Before (default)
session = AgentSession()  # 500ms delay

# After (optimized)
session = AgentSession(
    min_endpointing_delay=300,  # 300ms delay
)
```

**Documentation Links**:
- Implementation: `agent.py:944` (AgentSession configuration)
- Research: `docs/voice-delay-research.md` (this document)

### ✅ IMPLEMENTED: Model-Level Documentation
**Date**: Current session  
**Approach**: Added comments to RealtimeModel creation explaining VAD parameter limitations
**Location**: `maids/base.py` - `_create_realtime_model()` method
**Purpose**: Document why VAD parameters don't work at model level
**Reference**: Links back to this research document

**Documentation Links**:
- Implementation: `maids/base.py:_create_realtime_model()` 
- Research: `docs/voice-delay-research.md` (this document)

## References

- LiveKit Agents Documentation
- LiveKit RealtimeModel API Reference
- Google Gemini Live API Documentation
- OpenAI Realtime API Documentation

---

*Research conducted during voice delay optimization investigation*  
*Last Updated*: Current session