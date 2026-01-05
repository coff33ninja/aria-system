"""Mei — The Smart Home & IoT Maid"""
import logging
from maids.base import BaseMaid
from .tools import control_lights, set_thermostat, lock_doors, get_device_status, set_scene, control_device
from .prompts import MEI_INSTRUCTION

logger = logging.getLogger("maids.mei")


class Mei(BaseMaid):
    """
    Mei — The Smart Home & IoT Maid
    
    Quiet, precise, and incredibly tech-savvy.
    She manages all smart home devices with minimal words and maximum efficiency.
    
    Voice handoff: Returns from Aria's summon_mei tool trigger on_enter()
    """
    
    name = "Mei"
    specialty = "Smart Home & IoT"
    personality = "Quiet, precise, tech-savvy"
    
    # Mei's voice: soft, technical
    voice_openai = "echo"
    voice_google = "Zephyr"  # Soft, calm female voice
    temperature = 0.6  # Precise, predictable
    
    def get_tools(self):
        return [
            control_lights,
            set_thermostat,
            lock_doors,
            get_device_status,
            set_scene,
            control_device,
        ]
    
    def get_instructions(self) -> str:
        return MEI_INSTRUCTION
    
    def get_farewell_phrase(self) -> str:
        return "Complete. Aria."
    
    async def on_enter(self) -> None:
        """Called when Mei becomes active after handoff from Aria."""
        logger.info("🎭 Mei stepping forward")
        self.memory.remember("Summoned for smart home control", category="conversations")
        
        # Mei introduces herself quietly and efficiently
        self.session.generate_reply(
            instructions=(
                "You are Mei, the smart home maid. You just stepped forward quietly. "
                "Introduce yourself with minimal words - you're quiet and precise. "
                "Say something like 'Mei here. Smart home control. What device?' "
                "Keep it very short - you don't waste words."
            )
        )
