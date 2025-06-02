from pydantic import BaseModel, Field

import os
import sys 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent.agent import AgentConfig, Agent
from agent.prompt.get_sys_prompt import get_sys_prompt

class VisionCriticConfig(AgentConfig):
    """
    Configuration for the visual critic.
    """
    name: str = Field(default='Vision Critic Agent', description="Purpose of the agent")
    module_name: str = 'vision_critic'


class TextCriticConfig(AgentConfig):
    """
    Configuration for the text critic.
    """
    name: str = Field(default='Text Critic Agent', description="Purpose of the agent")
    module_name: str = 'text_critic'


class CriticConfig(AgentConfig):
    """
    Configuration for the critic, containing both vision and text critic configs.
    """
    name: str = Field(default='Critic Agent', description="Purpose of the agent")
    module_name: str = 'critic'

    vision: VisionCriticConfig = Field(default_factory=VisionCriticConfig)
    text: TextCriticConfig = Field(default_factory=TextCriticConfig)


class VisionCritic(Agent):
    """
    Vision Critic Agent that evaluates visual inputs.
    """
    def __init__(self, config: VisionCriticConfig):
        super().__init__(config)
        self.sys_prompt = get_sys_prompt('vision_critic')


class TextCritic(Agent):
    """
    Text Critic Agent that evaluates text inputs.
    """
    def __init__(self, config: TextCriticConfig):
        super().__init__(config)
        self.sys_prompt = get_sys_prompt('text_critic')


class Critic(Agent):

    """
    Critic Agent that combines both vision and text critics.
    """
    def __init__(self, config: CriticConfig):
        super().__init__(config)
        self.vision_critic = VisionCritic(config.vision)
        self.text_critic = TextCritic(config.text)
        self.sys_prompt = get_sys_prompt('critic')