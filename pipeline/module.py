
import os 
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))
from pydantic import Field

from agent import (
    ActorConfig,
    Actor,
    AgentConfig,
    Agent,
    CriticConfig,
    Critic,
    TextCriticConfig,
    TextCritic,
    VisionCriticConfig,
    VisionCritic
)



class ModuleConfig(AgentConfig):
    """
    Configuration for the module.
    """
    name: str = Field(default='Module Agent', description="Purpose of the agent")
    module_name: str = 'module'

class Module(Agent):
    """
    Represents a module that can perform actions based on the provided configuration.
    """
    config: ModuleConfig

    def __init__(self, config: ModuleConfig):
        super().__init__(config=config)

    def __str__(self):
        """
        String representation of the module.

        :return: String representation of the module.
        """
        return f"Module(name={self.config.name}, model_name={self.config.model_name})"