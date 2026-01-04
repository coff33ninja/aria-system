"""Mei — The Smart Home & IoT Maid"""
from maids.base import BaseMaid
from .tools import control_lights, set_thermostat, lock_doors, get_device_status, set_scene, control_device
from .prompts import MEI_INSTRUCTION


class Mei(BaseMaid):
    """
    Mei — The Smart Home & IoT Maid
    
    Quiet, precise, and incredibly tech-savvy.
    She manages all smart home devices with minimal words and maximum efficiency.
    """
    
    name = "Mei"
    specialty = "Smart Home & IoT"
    personality = "Quiet, precise, tech-savvy"
    
    # Mei's voice: soft, technical
    voice_openai = "echo"
    voice_google = "Puck"
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
