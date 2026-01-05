"""
Audio Analysis and Lip Sync for Live2D Avatars

Provides real-time audio analysis to drive Live2D mouth parameters
and other audio-reactive animations for natural lip sync.
"""

import asyncio
import logging
import numpy as np
from typing import Optional, Callable, Dict, List, Union
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)

# Audio processing constants
AUDIO_DTYPE_INT16_MAX = 32768.0
DB_RANGE_MIN = -60.0
DB_RANGE_MAX = 0.0
LOG_EPSILON = 1e-10
BREATHING_CYCLE_SECONDS = 4.0
BREATHING_BASE_AMPLITUDE = 0.3
BREATHING_BASE_OFFSET = 0.7
BREATHING_SPEAKING_MULTIPLIER = 0.5


@dataclass
class AudioFrame:
    """Represents a single audio frame for analysis"""
    data: bytes
    sample_rate: int
    channels: int
    timestamp: float


@dataclass
class AudioAnalysisConfig:
    """Configuration for audio analysis parameters"""
    sample_rate: int = 48000
    frame_size: int = 1024
    voice_activity_threshold: float = 0.01
    volume_smoothing: float = 0.7
    frequency_smoothing: float = 0.8
    max_history_length: int = 120  # 2 seconds at 60fps
    
    def __post_init__(self):
        """Validate configuration parameters"""
        if self.sample_rate <= 0:
            raise ValueError("Sample rate must be positive")
        if not 0.0 <= self.volume_smoothing <= 1.0:
            raise ValueError("Volume smoothing must be between 0.0 and 1.0")
        if not 0.0 <= self.frequency_smoothing <= 1.0:
            raise ValueError("Frequency smoothing must be between 0.0 and 1.0")


@dataclass
class LipSyncConfig:
    """Configuration for lip sync parameters"""
    sensitivity: float = 1.0
    smoothing_factor: float = 0.6
    max_mouth_opening: float = 0.9
    speaking_smile_amount: float = 0.1
    speaking_threshold: float = 0.1
    mouth_opening_power: float = 0.6
    
    def __post_init__(self):
        """Validate configuration parameters"""
        if self.sensitivity <= 0:
            raise ValueError("Sensitivity must be positive")
        if not 0.0 <= self.smoothing_factor <= 1.0:
            raise ValueError("Smoothing factor must be between 0.0 and 1.0")
        if not 0.0 <= self.max_mouth_opening <= 1.0:
            raise ValueError("Max mouth opening must be between 0.0 and 1.0")


class AudioAnalyzer:
    """
    Analyzes audio streams for Live2D parameter extraction.
    
    Extracts:
    - Volume levels for mouth opening
    - Frequency analysis for mouth shapes
    - Voice activity detection
    - Breathing patterns
    """
    
    def __init__(self, config: Optional[AudioAnalysisConfig] = None):
        self.config = config or AudioAnalysisConfig()
        
        # Audio analysis state
        self.volume_history: List[float] = []
        self.frequency_history: List[float] = []
        
        # Current analysis results
        self.current_volume = 0.0
        self.current_frequency = 0.0
        self.is_voice_active = False
        
        logger.info(f"🎤 Audio analyzer initialized (sample_rate={self.config.sample_rate}, frame_size={self.config.frame_size})")
    
    async def analyze_frame(self, audio_data: bytes) -> float:
        """
        Analyze a single audio frame and return mouth opening value.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            float: Mouth opening value (0.0 to 1.0)
        """
        try:
            # Convert bytes to numpy array
            audio_array = self._bytes_to_numpy(audio_data)
            
            if audio_array is None or len(audio_array) == 0:
                return 0.0
            
            # Calculate volume (RMS)
            volume = self._calculate_rms_volume(audio_array)
            
            # Smooth volume changes
            self.current_volume = self._smooth_value(
                self.current_volume, volume, self.config.volume_smoothing
            )
            
            # Update voice activity
            self.is_voice_active = self.current_volume > self.config.voice_activity_threshold
            
            # Convert volume to mouth opening (0.0 to 1.0)
            mouth_opening = self._volume_to_mouth_opening(self.current_volume)
            
            # Add to history for pattern analysis
            self._update_history(volume)
            
            return mouth_opening
            
        except Exception as e:
            logger.error(f"❌ Audio analysis error: {e}")
            return 0.0
    
    def _bytes_to_numpy(self, audio_data: bytes) -> Optional[np.ndarray]:
        """Convert audio bytes to numpy array"""
        try:
            # Assume 16-bit PCM audio
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Normalize to [-1.0, 1.0]
            audio_array = audio_array.astype(np.float32) / AUDIO_DTYPE_INT16_MAX
            
            return audio_array
            
        except Exception as e:
            logger.error(f"❌ Audio conversion error: {e}")
            return None
    
    def _calculate_rms_volume(self, audio_array: np.ndarray) -> float:
        """Calculate RMS (Root Mean Square) volume"""
        if len(audio_array) == 0:
            return 0.0
        
        # Calculate RMS
        rms = np.sqrt(np.mean(audio_array ** 2))
        
        # Apply logarithmic scaling for better mouth movement
        if rms > 0:
            # Convert to dB and normalize
            db = 20 * np.log10(rms + LOG_EPSILON)  # Add small value to avoid log(0)
            # Normalize from typical range to [0, 1]
            normalized = max(0.0, min(1.0, (db - DB_RANGE_MIN) / (DB_RANGE_MAX - DB_RANGE_MIN)))
            return normalized
        
        return 0.0
    
    def _smooth_value(self, current: float, new: float, smoothing: float) -> float:
        """Apply exponential smoothing to reduce jitter"""
        return current * smoothing + new * (1.0 - smoothing)
    
    def _volume_to_mouth_opening(self, volume: float) -> float:
        """
        Convert volume level to mouth opening parameter.
        
        Uses a curve that provides natural-looking mouth movement:
        - Low volumes: closed mouth
        - Medium volumes: natural opening
        - High volumes: wide open mouth
        """
        if volume <= 0.0:
            return 0.0
        
        # Apply power curve for more natural mouth movement
        # Lower power = more sensitive to quiet sounds
        # Higher power = less sensitive, more dramatic for loud sounds
        power = 0.5
        mouth_opening = math.pow(volume, power)
        
        # Clamp to valid range
        return max(0.0, min(1.0, mouth_opening))
    
    def _update_history(self, volume: float) -> None:
        """Update volume history for pattern analysis"""
        self.volume_history.append(volume)
        
        # Keep only recent history
        if len(self.volume_history) > self.config.max_history_length:
            self.volume_history = self.volume_history[-self.config.max_history_length:]
    
    def get_breathing_pattern(self) -> float:
        """
        Generate breathing pattern based on audio activity.
        
        Returns:
            float: Breathing parameter (0.0 to 1.0)
        """
        current_time = asyncio.get_event_loop().time()
        
        # Base breathing cycle
        base_breathing = (math.sin(current_time * math.pi / BREATHING_CYCLE_SECONDS) * 
                         BREATHING_BASE_AMPLITUDE + BREATHING_BASE_OFFSET)
        
        # Modify breathing based on voice activity
        if self.is_voice_active:
            # Reduce breathing when speaking
            return base_breathing * BREATHING_SPEAKING_MULTIPLIER
        else:
            # Normal breathing when idle
            return base_breathing
    
    def get_voice_activity(self) -> bool:
        """Check if voice is currently active"""
        return self.is_voice_active
    
    def get_current_volume(self) -> float:
        """Get current smoothed volume level"""
        return self.current_volume
    
    def get_volume_statistics(self) -> Dict[str, float]:
        """Get volume statistics for debugging and optimization"""
        if not self.volume_history:
            return {"min": 0.0, "max": 0.0, "avg": 0.0, "current": self.current_volume}
        
        return {
            "min": min(self.volume_history),
            "max": max(self.volume_history),
            "avg": sum(self.volume_history) / len(self.volume_history),
            "current": self.current_volume,
            "samples": len(self.volume_history)
        }


class LipSyncController:
    """
    Controls Live2D mouth parameters for realistic lip sync.
    
    Manages multiple mouth parameters:
    - ParamMouthOpenY: Vertical mouth opening
    - ParamMouthForm: Mouth shape (smile/frown)
    - ParamMouthOpenX: Horizontal mouth opening (optional)
    """
    
    def __init__(self, config: Optional[LipSyncConfig] = None):
        self.config = config or LipSyncConfig()
        
        # Current mouth parameters
        self.mouth_open_y = 0.0
        self.mouth_form = 0.0
        self.mouth_open_x = 0.0
        
        # Mouth shape patterns for different sounds (future enhancement)
        self.phoneme_shapes = {
            'a': {'open_y': 0.8, 'form': 0.0, 'open_x': 0.2},
            'e': {'open_y': 0.4, 'form': 0.3, 'open_x': 0.6},
            'i': {'open_y': 0.2, 'form': 0.5, 'open_x': 0.8},
            'o': {'open_y': 0.6, 'form': -0.2, 'open_x': 0.0},
            'u': {'open_y': 0.3, 'form': -0.4, 'open_x': -0.2},
        }
        
        logger.info(f"👄 Lip sync controller initialized (sensitivity={self.config.sensitivity})")
    
    async def update_mouth_parameters(self, volume_level: float) -> Dict[str, float]:
        """
        Update mouth parameters based on audio volume.
        
        Args:
            volume_level: Audio volume (0.0 to 1.0)
            
        Returns:
            Dict of parameter names and values
        """
        # Apply sensitivity scaling
        scaled_volume = volume_level * self.config.sensitivity
        
        # Calculate mouth opening with natural curve
        target_open_y = self._calculate_mouth_opening(scaled_volume)
        
        # Smooth parameter changes
        self.mouth_open_y = self._smooth_parameter(
            self.mouth_open_y, target_open_y, self.config.smoothing_factor
        )
        
        # Calculate mouth form (slight smile when speaking)
        if scaled_volume > self.config.speaking_threshold:
            target_form = self.config.speaking_smile_amount  # Slight smile when speaking
        else:
            target_form = 0.0  # Neutral when silent
        
        self.mouth_form = self._smooth_parameter(
            self.mouth_form, target_form, self.config.smoothing_factor * 0.5
        )
        
        return {
            'ParamMouthOpenY': self.mouth_open_y,
            'ParamMouthForm': self.mouth_form,
            'ParamMouthOpenX': self.mouth_open_x
        }
    
    def _calculate_mouth_opening(self, volume: float) -> float:
        """Calculate natural mouth opening based on volume"""
        if volume <= 0.0:
            return 0.0
        
        # Use a curve that provides natural mouth movement
        # Starts opening at low volumes, reaches full opening at high volumes
        opening = math.pow(volume, self.config.mouth_opening_power) * self.config.max_mouth_opening
        
        return max(0.0, min(self.config.max_mouth_opening, opening))
    
    def _smooth_parameter(self, current: float, target: float, smoothing: float) -> float:
        """Smooth parameter transitions"""
        return current * smoothing + target * (1.0 - smoothing)
    
    def set_phoneme_shape(self, phoneme: str) -> Dict[str, float]:
        """
        Set mouth shape for specific phoneme (future enhancement).
        
        Args:
            phoneme: Phoneme character ('a', 'e', 'i', 'o', 'u')
            
        Returns:
            Dict of parameter names and values
        """
        if phoneme.lower() in self.phoneme_shapes:
            shape = self.phoneme_shapes[phoneme.lower()]
            
            self.mouth_open_y = shape['open_y']
            self.mouth_form = shape['form']
            self.mouth_open_x = shape['open_x']
            
            return {
                'ParamMouthOpenY': self.mouth_open_y,
                'ParamMouthForm': self.mouth_form,
                'ParamMouthOpenX': self.mouth_open_x
            }
        
        return {}
    
    def reset_mouth(self) -> Dict[str, float]:
        """Reset mouth to neutral position"""
        self.mouth_open_y = 0.0
        self.mouth_form = 0.0
        self.mouth_open_x = 0.0
        
        return {
            'ParamMouthOpenY': 0.0,
            'ParamMouthForm': 0.0,
            'ParamMouthOpenX': 0.0
        }
    
    def get_current_parameters(self) -> Dict[str, float]:
        """Get current mouth parameter values"""
        return {
            'ParamMouthOpenY': self.mouth_open_y,
            'ParamMouthForm': self.mouth_form,
            'ParamMouthOpenX': self.mouth_open_x
        }


class VoiceActivityDetector:
    """
    Detects voice activity for triggering expression changes.
    
    Helps determine when to switch between idle and speaking expressions.
    """
    
    def __init__(self, threshold: float = 0.02, min_duration: float = 0.1):
        self.threshold = threshold
        self.min_duration = min_duration
        
        # State tracking
        self.is_speaking = False
        self.speaking_start_time = 0.0
        self.silence_start_time = 0.0
        
        # Callbacks
        self.on_speech_start: Optional[Callable] = None
        self.on_speech_end: Optional[Callable] = None
        
        logger.info(f"🗣️ Voice activity detector initialized (threshold={threshold})")
    
    def update(self, volume_level: float) -> bool:
        """
        Update voice activity detection.
        
        Args:
            volume_level: Current audio volume
            
        Returns:
            bool: True if currently speaking
        """
        current_time = asyncio.get_event_loop().time()
        
        if volume_level > self.threshold:
            # Voice detected
            if not self.is_speaking:
                # Start of speech
                self.speaking_start_time = current_time
                
                # Check minimum duration before confirming speech
                if current_time - self.silence_start_time > self.min_duration:
                    self.is_speaking = True
                    if self.on_speech_start:
                        asyncio.create_task(self.on_speech_start())
        else:
            # Silence detected
            if self.is_speaking:
                # Potential end of speech
                if self.silence_start_time == 0.0:
                    self.silence_start_time = current_time
                
                # Check minimum silence duration before confirming end
                if current_time - self.silence_start_time > self.min_duration:
                    self.is_speaking = False
                    self.silence_start_time = 0.0
                    if self.on_speech_end:
                        asyncio.create_task(self.on_speech_end())
            else:
                # Continue silence
                if self.silence_start_time == 0.0:
                    self.silence_start_time = current_time
        
        return self.is_speaking
    
    def set_callbacks(self, on_start: Callable = None, on_end: Callable = None) -> None:
        """Set callbacks for speech start/end events"""
        self.on_speech_start = on_start
        self.on_speech_end = on_end
    
    def reset(self) -> None:
        """Reset voice activity state"""
        self.is_speaking = False
        self.speaking_start_time = 0.0
        self.silence_start_time = 0.0


# Utility functions
def create_audio_analyzer(config: Optional[AudioAnalysisConfig] = None) -> AudioAnalyzer:
    """Factory function to create an audio analyzer"""
    return AudioAnalyzer(config=config)


def create_lip_sync_controller(config: Optional[LipSyncConfig] = None) -> LipSyncController:
    """Factory function to create a lip sync controller"""
    return LipSyncController(config=config)


def create_voice_activity_detector(threshold: float = 0.02) -> VoiceActivityDetector:
    """Factory function to create a voice activity detector"""
    return VoiceActivityDetector(threshold=threshold)