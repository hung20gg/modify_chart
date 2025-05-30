from pydantic import BaseModel, Field
from typing import Union
from PIL import Image
import os
import sys 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent.agent import AgentConfig, Agent
from agent.prompt.get_sys_prompt import get_sys_prompt

class ActorConfig(AgentConfig):
    """
    Configuration for the actor.
    """
    name: str = Field(default='Actor Agent', description="Purpose of the agent")
    module_name: str = 'actor'

class Actor(Agent):
    """
    Represents an actor that can perform actions based on the provided configuration.
    """
    config: ActorConfig

    def __init__(self, config: ActorConfig):
        super().__init__(config=config)

    def act(self, image : Union[str, Image], action: str, prev_state_code: str = None, prev_state_critique: str = None) -> dict:
        """
        Perform an action with the given parameters.

        :param action: The action to perform.
        :return: Result of the action.
        """
        # Placeholder for action logic

        sys_prompt = get_sys_prompt(self.config.module_name)

        user_prompt = f"""
        You are an actor agent. Your task is to perform the following action:
        """

        messages = [
            {
                'role': 'system',
                'content': sys_prompt
            },
            {
                'role': 'user',
                'content': action
            }
        ]

        return self.llm(messages)
    

    def __str__(self):
        """
        String representation of the actor.

        :return: String representation of the actor.
        """
        return f"Actor(name={self.config.name}, model_name={self.config.model_name})"
    
