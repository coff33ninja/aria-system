# Voice Optimization Rebuild Plan

## Executive Summary

The Aria Maid System currently uses LiveKit Agents v1.x with `AgentSession` and `Agent` classes. To properly implement voice delay optimization, the system needs to be rebuilt using the correct LiveKit APIs with proper voice detection parameters.

## Current Architecture Analysis

### Current Implementation
- **Framework**: LiveKit Agents v1.x (modern)
- **Agent Type**: Custom `Agent` class extending `livekit.agents.Agent`
- **Session Management**: `AgentSession()` for orchestration
- **Voice Model**: Google Gemini Realtime API / OpenAI Realtime API
- **Architecture**: Multi-agent system with voice handoffs

### Voice Detection Current State
- **Default Delay**: 500ms (LiveKit default)
- **Configuration**: No voice detection parameters currently configured
- **Issue**: Voice input feels slow and unresponsive
- **Failed Attempt**: Tried adding `min_endpointing_delay=300` to `AgentSession()` constructor (invalid)
- **Sophia Bug**: Research maid stops mid-response after 2-3 sentences, requiring user acknowledgment to continue (likely related to voice detection interrupting longer responses)

## Research Findings

### Key Discovery: Voice Detection Parameters Location
Based on LiveKit documentation research:

1. **Correct Location**: Voice detection parameters belong in the `Agent` constructor, NOT `AgentSession`
2. **Valid Parameters**: 
   - `min_endpointing_delay: float` - Minimum silence before end-of-turn (default: 500ms)
   - `max_endpointing_delay: float` - Maximum silence before forced end-of-turn
3. **API Reference**: `livekit.agents.voice.Agent` class supports these parameters

### LiveKit Voice Detection Architecture
```
User Speech → VAD (Voice Activity Detection) → Endpointing Delay → LLM Processing
                                              ↑
                                    min_endpointing_delay (500ms default)
```

### Advanced Option: EOU (End of Utterance) Model
- **Technology**: 135M parameter transformer model
- **Purpose**: Semantic turn detection (not just silence-based)
- **Benefit**: Reduces interruptions while maintaining responsiveness
- **Implementation**: Available as LiveKit Agents plugin

## Rebuild Plan

### Phase 1: Basic Voice Delay Optimization

#### 1.1 Update Agent Constructor
**File**: `agent.py` - `Aria` class constructor
**Change**: Add voice detection parameters to `Agent` parent class

```python
# Current (in Aria.__init__)
super().__init__(
    instructions=AGENT_INSTRUCTION,
    llm=get_realtime_model(llm_provider),
    tools=[...],
    chat_ctx=chat_ctx
)

# Proposed (optimized)
super().__init__(
    instructions=AGENT_INSTRUCTION,
    llm=get_realtime_model(llm_provider),
    tools=[...],
    chat_ctx=chat_ctx,
    # Voice optimization parameters
    min_endpointing_delay=0.3,  # 300ms (40% faster than 500ms default)
    max_endpointing_delay=2.0,  # 2 seconds maximum wait
)
```

#### 1.2 Update BaseMaid Constructor
**File**: `maids/base.py` - `BaseMaid` class constructor
**Change**: Add same voice detection parameters to all maids

```python
# Current (in BaseMaid.__init__)
super().__init__(
    instructions=self.get_instructions(),
    llm=self._create_realtime_model(provider),
    tools=all_tools,
    chat_ctx=chat_ctx
)

# Proposed (optimized)
super().__init__(
    instructions=self.get_instructions(),
    llm=self._create_realtime_model(provider),
    tools=all_tools,
    chat_ctx=chat_ctx,
    # Voice optimization parameters (consistent across all maids)
    min_endpointing_delay=0.3,  # 300ms for faster response
    max_endpointing_delay=2.0,  # 2 seconds maximum
)
```

#### 1.3 Configuration Management
**File**: `agent.py` - Add configuration constants

```python
# Voice detection configuration
VOICE_MIN_ENDPOINTING_DELAY = float(os.environ.get("ARIA_MIN_ENDPOINTING_DELAY", "0.3"))
VOICE_MAX_ENDPOINTING_DELAY = float(os.environ.get("ARIA_MAX_ENDPOINTING_DELAY", "2.0"))
```

### Phase 2: Advanced Semantic Turn Detection (EOU Model)

#### 2.1 Install EOU Plugin
**File**: `requirements.txt`
```
# Add EOU (End of Utterance) model support
livekit-plugins-turn-detector
```

#### 2.2 Implement EOU Turn Detection
**File**: `agent.py` - Enhanced voice detection

```python
from livekit.plugins.turn_detector import EOUModel

# In Agent constructor
super().__init__(
    instructions=AGENT_INSTRUCTION,
    llm=get_realtime_model(llm_provider),
    tools=[...],
    chat_ctx=chat_ctx,
    # Basic voice optimization
    min_endpointing_delay=0.3,
    max_endpointing_delay=2.0,
    # Advanced semantic turn detection
    turn_detection=EOUModel(),  # Uses transformer for semantic understanding
)
```

### Phase 3: Performance Monitoring & Tuning

#### 3.1 Voice Response Metrics
**File**: `tools.py` - Add voice performance monitoring

```python
@function_tool
async def voice_performance_report(context: RunContext) -> str:
    """Report voice detection performance metrics."""
    # Track response times, interruption rates, user satisfaction
    return "Voice performance metrics..."
```

#### 3.2 Dynamic Tuning
**File**: `agent.py` - Adaptive voice detection

```python
class AdaptiveVoiceConfig:
    """Dynamically adjust voice detection based on user behavior."""
    
    def __init__(self):
        self.base_delay = 0.3
        self.interruption_count = 0
        self.response_times = []
    
    def adjust_delay(self, was_interrupted: bool, response_time: float):
        """Adjust endpointing delay based on interaction patterns."""
        if was_interrupted:
            self.base_delay += 0.05  # Increase delay to reduce interruptions
        elif response_time > 1.0:
            self.base_delay -= 0.02  # Decrease delay for faster response
        
        # Keep within reasonable bounds
        self.base_delay = max(0.2, min(0.8, self.base_delay))
```

## Implementation Timeline

### Week 1: Basic Optimization
- [ ] Update `Aria` class constructor with voice parameters
- [ ] Update `BaseMaid` class constructor with voice parameters  
- [ ] Add environment variable configuration
- [ ] Test and validate 40% improvement in response time
- [ ] Deploy and monitor for issues

### Week 2: Advanced Features
- [ ] Research and implement EOU model integration
- [ ] Add voice performance monitoring tools
- [ ] Create user feedback mechanism for voice quality
- [ ] Fine-tune parameters based on real usage

### Week 3: Polish & Documentation
- [ ] Implement adaptive voice detection
- [ ] Create comprehensive voice optimization documentation
- [ ] Add troubleshooting guides
- [ ] Performance benchmarking and comparison

### Expected Improvements

### Quantitative Benefits
- **Response Time**: 40% faster (500ms → 300ms)
- **User Experience**: More natural conversation flow
- **Interruption Rate**: Reduced with EOU model
- **Accuracy**: Better turn detection with semantic understanding
- **Sophia's Completeness**: Should resolve truncation bug by preventing premature interruptions

### Qualitative Benefits
- **Natural Feel**: Conversations feel more human-like
- **Responsiveness**: Aria responds faster to user input
- **Reliability**: Fewer false triggers and missed inputs
- **Consistency**: All maids have optimized voice detection
- **Complete Reports**: Sophia can deliver full research without interruption

## Risk Assessment

### Low Risk
- **Basic Parameter Changes**: Well-documented LiveKit API
- **Backward Compatibility**: No breaking changes to existing functionality
- **Rollback Plan**: Easy to revert parameter changes

### Medium Risk
- **EOU Model Integration**: New technology, may need fine-tuning
- **Performance Impact**: Transformer model adds CPU overhead
- **User Adaptation**: Users may need time to adjust to faster responses

### Mitigation Strategies
- **Gradual Rollout**: Deploy basic optimization first, then advanced features
- **A/B Testing**: Compare old vs new voice detection with user feedback
- **Monitoring**: Track performance metrics and user satisfaction
- **Configuration**: Make parameters easily adjustable via environment variables

## Testing Strategy

### Unit Tests
- Voice parameter validation
- Configuration loading
- Agent initialization with voice parameters

### Integration Tests
- End-to-end voice detection timing
- Multi-agent handoff with optimized voice detection
- Memory system compatibility

### User Acceptance Tests
- Real user conversations with timing measurements
- Interruption rate analysis
- User satisfaction surveys

## Documentation Updates Required

### Technical Documentation
- [ ] Update `docs/voice-delay-research.md` with implementation details
- [ ] Create `docs/voice-optimization-guide.md` for developers
- [ ] Update API reference documentation

### User Documentation
- [ ] Update README with voice optimization features
- [ ] Create troubleshooting guide for voice issues
- [ ] Add configuration examples

### Deployment Documentation
- [ ] Update `.git-deploy.md` with new environment variables
- [ ] Add voice optimization validation steps
- [ ] Include performance monitoring commands

## Success Metrics

### Technical Metrics
- Voice detection latency < 300ms
- Interruption rate < 5%
- 99.9% uptime during voice interactions
- Memory usage increase < 10%

### User Experience Metrics
- User satisfaction score > 4.5/5
- Conversation completion rate > 95%
- Average conversation length increase
- Reduced user complaints about responsiveness

## Conclusion

This rebuild plan provides a comprehensive approach to optimizing voice detection in the Aria Maid System. The phased approach allows for gradual improvement while minimizing risk. The combination of basic parameter optimization and advanced semantic turn detection should significantly improve the user experience.

The key insight from research is that voice detection parameters belong in the `Agent` constructor, not the `AgentSession`. This correction, combined with proper parameter values and optional EOU model integration, will transform Aria from a slow-responding system to a highly responsive, natural-feeling voice assistant.

---

**Next Steps**: Begin Phase 1 implementation with basic voice delay optimization, followed by testing and gradual rollout of advanced features.

**Estimated Timeline**: 3 weeks for complete implementation
**Estimated Effort**: 40-60 hours of development and testing
**Priority**: High - directly impacts core user experience