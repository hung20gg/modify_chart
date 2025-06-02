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
    code: str = Field(default='python', description="Code type: either python or html")

class Actor(Agent):
    """
    Represents an actor that can perform actions based on the provided configuration.
    """
    config: ActorConfig

    def __init__(self, config: ActorConfig):
        super().__init__(config=config)


    def python_prompt(self, action:str, prev_state_code: str = None, prev_state_critique: str = None):

        """
        Generate a Python prompt based on the action and previous state.

        :param action: The action to perform.
        :param prev_state_code: Previous state code.
        :param prev_state_critique: Previous state critique.
        :return: Formatted Python prompt.
        """
        return f"""
        <image>

        ### Task: 
        {action}

        { f"### Previous code for chart: \n\n```{self.config.code}\n{prev_state_code}\n```" if prev_state_code else "" }
        { f"### Previous critique on the chart: \n\n{prev_state_critique}\n" if prev_state_critique else "" }
        """


    def html_prompt(self, action: str, prev_state_code: str = None, prev_state_critique: str = None):

        pass


    def act(self, request: str, image : Union[str, Image] = None, prev_state_code: str = None, prev_state_critique: str = None) -> dict:
        """
        Perform an action with the given parameters.

        :param request: The action to perform.
        :return: Result of the action.
        """
        # Placeholder for action logic
        if isinstance(image, str):
            if os.path.exists(
                image):
                image = Image.open(image)
            else:
                raise ValueError(f"Image path {image} does not exist.")

        sys_prompt = get_sys_prompt(self.config.module_name)
        sys_prompt += f"\n\n### Code language: {self.config.code}\n"

        if self.config.code == 'html':
            user_prompt = self.html_prompt(request, prev_state_code, prev_state_critique)
        else:
            user_prompt = self.python_prompt(request, prev_state_code, prev_state_critique)


        messages = [
            {
                'role': 'system',
                'content': sys_prompt
            },
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'image',
                        'image': image
                    },
                    {
                        'type': 'text',
                        'text': user_prompt
                    }
                ]
            }
        ]

        action = self.llm(messages)

        if self.config.debug:
            print(f"Action: {action}")

        return {
            'action': action
        }
    
    def act_with_prev_state(self, request: str, image : Union[str, Image] = None, prev_state_code: str = None, prev_state_critique: str = None) -> dict:
        return self.act(request, image, prev_state_code, prev_state_critique)

    def __str__(self):
        """
        String representation of the actor.

        :return: String representation of the actor.
        """
        return f"Actor(name={self.config.name}, model_name={self.config.model_name})"
    
