"""
Live2D Avatar Session for LiveKit Integration

Manages Live2D model lifecycle, parameter updates, and real-time synchronization
with LiveKit voice agents. Each maid gets their own avatar session with unique
expressions and personality-driven animations.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

from livekit import rtc
from .expressions import MaidExpressions, ExpressionManager
from .audio_sync import AudioAnalyzer, LipSyncController

logger = logging.getLogger(__name__)


@dataclass
class Live2DModelConfig:
    """Configuration for a Live2D model"""
    model_path: str
    maid_name: str
    personality: str
    default_expression: str = "idle"
    expressions: Dict[str, Dict[str, float]] = None
    animation_speed: float = 1.0
    lip_sync_sensitivity: float = 1.0


class Live2DAvatarSession:
    """
    Manages a Live2D avatar session for a specific maid.
    
    Handles:
    - Model loading and initialization
    - Real-time parameter updates
    - Audio synchronization for lip sync
    - Expression changes based on context
    - Smooth animations between states
    """
    
    def __init__(self, config: Live2DModelConfig):
        self.config = config
        self.participant_identity = f"live2d-{config.maid_name.lower()}"
        
        # Core components
        self.expression_manager = ExpressionManager(config.maid_name, config.expressions)
        self.audio_analyzer = AudioAnalyzer()
        self.lip_sync = LipSyncController(sensitivity=config.lip_sync_sensitivity)
        
        # State management
        self.current_expression = config.default_expression
        self.is_speaking = False
        self.model_loaded = False
        self.session = None
        self.room = None
        
        # Animation state
        self._animation_tasks: List[asyncio.Task] = []
        self._parameter_cache: Dict[str, float] = {}
        
        logger.info(f"🎭 Live2D Avatar Session created for {config.maid_name}")
    
    async def start(self, session, room: rtc.Room) -> None:
        """
        Initialize the Live2D avatar in the LiveKit room.
        
        Args:
            session: LiveKit agent session
            room: LiveKit room instance
        """
        self.session = session
        self.room = room
        
        try:
            # Send model initialization data to frontend
            await self._initialize_model()
            
            # Set up audio stream monitoring
            await self._setup_audio_monitoring()
            
            # Start idle animations
            await self._start_idle_animations()
            
            # Set initial expression
            await self.set_expression(self.config.default_expression)
            
            self.model_loaded = True
            logger.info(f"✨ {self.config.maid_name} Live2D avatar started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start Live2D avatar for {self.config.maid_name}: {e}")
            raise
    
    async def stop(self) -> None:
        """Clean up the avatar session"""
        # Cancel all animation tasks
        for task in self._animation_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self._animation_tasks:
            await asyncio.gather(*self._animation_tasks, return_exceptions=True)
        
        self.model_loaded = False
        logger.info(f"🎭 {self.config.maid_name} Live2D avatar stopped")
    
    async def _initialize_model(self) -> None:
        """Send model initialization data to frontend"""
        model_data = {
            "type": "live2d_init",
            "maid_name": self.config.maid_name,
            "model_path": self.config.model_path,
            "participant_identity": self.participant_identity,
            "expressions": self.expression_manager.get_all_expressions(),
            "animation_speed": self.config.animation_speed
        }
        
        # Send via LiveKit data channel (implementation depends on LiveKit setup)
        await self._send_to_frontend(model_data)
        logger.debug(f"📤 Sent model initialization for {self.config.maid_name}")
    
    async def _setup_audio_monitoring(self) -> None:
        """Set up real-time audio analysis for lip sync"""
        if not self.room:
            return
        
        # Monitor audio tracks for lip sync
        self.room.on("track_subscribed", self._on_audio_track)
        self.room.on("track_unsubscribed", self._on_audio_track_end)
        
        logger.debug(f"🎤 Audio monitoring setup for {self.config.maid_name}")
    
    def _on_audio_track(self, track: rtc.Track, participant: rtc.RemoteParticipant) -> None:
        """Handle new audio track for lip sync"""
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            # Start lip sync analysis
            asyncio.create_task(self._process_audio_stream(track))
    
    def _on_audio_track_end(self, track: rtc.Track, participant: rtc.RemoteParticipant) -> None:
        """Handle audio track ending"""
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            self.is_speaking = False
            asyncio.create_task(self._update_speaking_state(False))
    
    async def _process_audio_stream(self, track: rtc.Track) -> None:
        """Process audio stream for real-time lip sync"""
        try:
            async for frame in track:
                if not self.model_loaded:
                    continue
                
                # Analyze audio for lip sync parameters
                audio_data = frame.data
                lip_sync_value = await self.audio_analyzer.analyze_frame(audio_data)
                
                # Update lip sync parameters
                await self.lip_sync.update_mouth_parameters(lip_sync_value)
                
                # Send parameter updates to frontend
                await self._send_parameter_update("ParamMouthOpenY", lip_sync_value)
                
                # Update speaking state
                is_speaking = lip_sync_value > 0.1
                if is_speaking != self.is_speaking:
                    self.is_speaking = is_speaking
                    await self._update_speaking_state(is_speaking)
                    
        except Exception as e:
            logger.error(f"❌ Audio processing error for {self.config.maid_name}: {e}")
    
    async def set_expression(self, expression_name: str, duration: float = 0.5) -> None:
        """
        Change the maid's facial expression.
        
        Args:
            expression_name: Name of the expression to set
            duration: Animation duration in seconds
        """
        if not self.model_loaded:
            logger.warning(f"⚠️ Model not loaded, cannot set expression for {self.config.maid_name}")
            return
        
        expression_params = self.expression_manager.get_expression(expression_name)
        if not expression_params:
            logger.warning(f"⚠️ Unknown expression '{expression_name}' for {self.config.maid_name}")
            return
        
        # Animate to new expression
        await self._animate_to_parameters(expression_params, duration)
        self.current_expression = expression_name
        
        logger.debug(f"😊 {self.config.maid_name} expression changed to '{expression_name}'")
    
    async def _animate_to_parameters(self, target_params: Dict[str, float], duration: float) -> None:
        """Smoothly animate parameters to target values"""
        if not target_params:
            return
        
        # Create animation task
        animation_task = asyncio.create_task(
            self._parameter_animation(target_params, duration)
        )
        self._animation_tasks.append(animation_task)
        
        # Clean up completed tasks
        self._animation_tasks = [task for task in self._animation_tasks if not task.done()]
    
    async def _parameter_animation(self, target_params: Dict[str, float], duration: float) -> None:
        """Animate parameters over time"""
        start_time = asyncio.get_event_loop().time()
        start_params = self._parameter_cache.copy()
        
        while True:
            current_time = asyncio.get_event_loop().time()
            elapsed = current_time - start_time
            
            if elapsed >= duration:
                # Animation complete, set final values
                for param_name, target_value in target_params.items():
                    await self._send_parameter_update(param_name, target_value)
                    self._parameter_cache[param_name] = target_value
                break
            
            # Interpolate parameters
            progress = elapsed / duration
            # Use easing function for smooth animation
            eased_progress = self._ease_in_out_cubic(progress)
            
            for param_name, target_value in target_params.items():
                start_value = start_params.get(param_name, 0.0)
                current_value = start_value + (target_value - start_value) * eased_progress
                
                await self._send_parameter_update(param_name, current_value)
                self._parameter_cache[param_name] = current_value
            
            # Wait for next frame (60 FPS)
            await asyncio.sleep(1/60)
    
    def _ease_in_out_cubic(self, t: float) -> float:
        """Cubic easing function for smooth animations"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    async def _start_idle_animations(self) -> None:
        """Start continuous idle animations (breathing, blinking)"""
        # Breathing animation
        breathing_task = asyncio.create_task(self._breathing_animation())
        self._animation_tasks.append(breathing_task)
        
        # Blinking animation
        blinking_task = asyncio.create_task(self._blinking_animation())
        self._animation_tasks.append(blinking_task)
        
        logger.debug(f"💫 Idle animations started for {self.config.maid_name}")
    
    async def _breathing_animation(self) -> None:
        """Continuous breathing animation"""
        import math
        
        while self.model_loaded:
            try:
                current_time = asyncio.get_event_loop().time()
                # Slow breathing cycle (4 seconds)
                breath_value = math.sin(current_time * math.pi / 2) * 0.3 + 0.7
                
                await self._send_parameter_update("ParamBreath", breath_value)
                await asyncio.sleep(1/30)  # 30 FPS for breathing
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Breathing animation error: {e}")
                await asyncio.sleep(1)
    
    async def _blinking_animation(self) -> None:
        """Random blinking animation"""
        import random
        
        while self.model_loaded:
            try:
                # Random blink interval (2-6 seconds)
                await asyncio.sleep(random.uniform(2.0, 6.0))
                
                if not self.model_loaded:
                    break
                
                # Quick blink animation
                await self._send_parameter_update("ParamEyeLOpen", 0.0)
                await self._send_parameter_update("ParamEyeROpen", 0.0)
                await asyncio.sleep(0.1)
                await self._send_parameter_update("ParamEyeLOpen", 1.0)
                await self._send_parameter_update("ParamEyeROpen", 1.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Blinking animation error: {e}")
                await asyncio.sleep(1)
    
    async def _update_speaking_state(self, is_speaking: bool) -> None:
        """Update avatar state when speaking starts/stops"""
        if is_speaking:
            # Switch to speaking expression if in idle
            if self.current_expression == "idle":
                await self.set_expression("speaking", duration=0.2)
        else:
            # Return to idle expression
            if self.current_expression == "speaking":
                await self.set_expression("idle", duration=0.3)
    
    async def _send_parameter_update(self, param_name: str, value: float) -> None:
        """Send parameter update to frontend"""
        update_data = {
            "type": "live2d_parameter",
            "maid_name": self.config.maid_name,
            "parameter": param_name,
            "value": value
        }
        
        await self._send_to_frontend(update_data)
    
    async def _send_to_frontend(self, data: Dict[str, Any]) -> None:
        """Send data to frontend via LiveKit data channel"""
        # This would be implemented based on your LiveKit setup
        # For now, we'll log the data that would be sent
        logger.debug(f"📤 Frontend data: {json.dumps(data, indent=2)}")
        
        # TODO: Implement actual data channel sending
        # Example:
        # if self.room:
        #     await self.room.local_participant.publish_data(
        #         json.dumps(data).encode(),
        #         destination_sids=[participant.sid for participant in self.room.participants]
        #     )


# Factory function for easy maid avatar creation
def create_maid_avatar_session(maid_name: str, model_path: str, personality: str) -> Live2DAvatarSession:
    """
    Create a Live2D avatar session for a specific maid.
    
    Args:
        maid_name: Name of the maid (aria, sophia, luna, etc.)
        model_path: Path to the Live2D model files
        personality: Personality description for expression mapping
        
    Returns:
        Configured Live2DAvatarSession
    """
    config = Live2DModelConfig(
        model_path=model_path,
        maid_name=maid_name,
        personality=personality,
        expressions=MaidExpressions.get_maid_expressions(maid_name)
    )
    
    return Live2DAvatarSession(config)