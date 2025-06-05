from pydantic import BaseModel, Field
from typing import Union
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

import os
import sys 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent.base import AgentConfig, Agent
from agent.prompt.get_sys_prompt import get_sys_prompt
from utils import open_image, extract_critique_and_score
import logging
logging.basicConfig(level=logging.INFO)

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
    code: str = Field(default='python', description="Code type: either python or html")

class CriticConfig(AgentConfig):
    """
    Configuration for the critic, containing both vision and text critic configs.
    """
    name: str = Field(default='Critic Agent', description="Purpose of the agent")
    module_name: str = 'critic'
    model_name: str = Field(default=None, description="Model to be used by the critic")

    vision: VisionCriticConfig = Field(default_factory=VisionCriticConfig)
    text: TextCriticConfig = Field(default_factory=TextCriticConfig)

    def __init__(self, **data):
        """
        Initialize the CriticConfig with the given parameters.
        """
        super().__init__(**data)
        if not self.model_name:
            text_model = self.text.model_name
            vision_model = self.vision.model_name

            if text_model != vision_model:
                logging.warning(
                    f"Text model {text_model} and Vision model {vision_model} are different. "
                    "This may lead to inconsistent behavior in the Critic Agent."
                )
            self.model_name = vision_model
                


class VisionCritic(Agent):
    """
    Vision Critic Agent that evaluates visual inputs.
    """
    sys_prompt: str = None

    def __init__(self, config: VisionCriticConfig):
        super().__init__(config)
        self.sys_prompt = get_sys_prompt('vision_critic')


    def act_with_prev_state(self, 
                            request: str, 
                            action_image : Union[str, Image.Image] = None, 
                            prev_vision_critique: str = None) -> dict:
        """
        Perform an action with the given parameters, Given previous state critique.

        :param request: The action to perform.
        :param image: Image input for the critic.
        :param prev_state_critique: Previous critique on the image.
        :return: Result of the action.
        """

        if isinstance(image, str):
            if os.path.exists(image):
                image = open_image(image)
            else:
                raise ValueError(f"Image path {image} does not exist.")


        # Implement the logic for vision critique here
        sys_prompt = get_sys_prompt(self.config.module_name)

        user_prompt = f"""
<image>

### Task:
{request}

{ f"### Previous critique on the image: \n\n{prev_vision_critique}\n" if prev_vision_critique else "" }
"""

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
                        'image': action_image
                    },
                    {
                        'type': 'text',
                        'text': user_prompt
                    }
                ]
            }
        ]

        raw_response = self.llm(messages)

        if self.config.debug:
            print(f"Raw response from Vision Critic: {raw_response}")

        return extract_critique_and_score(raw_response)


    def act(self, 
            request: str, 
            action_image: Union[str, Image.Image] = None) -> dict:
        
        sys_prompt = get_sys_prompt(self.config.module_name)

        user_prompt = f"""
<image>

### Task:
{request}
"""

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
                        'image': action_image
                    },
                    {
                        'type': 'text',
                        'text': user_prompt
                    }
                ]
            }
        ]

        raw_response = self.llm(messages)

        if self.config.debug:
            print(f"Raw response from Vision Critic: {raw_response}")

        return extract_critique_and_score(raw_response)

class TextCritic(Agent):
    """
    Text Critic Agent that evaluates text inputs.
    """
    sys_prompt: str = None

    def __init__(self, config: TextCriticConfig):
        super().__init__(config)
        self.sys_prompt = get_sys_prompt('text_critic')

    def act_with_prev_state(self, request: str, action_code: str = None, prev_code: str = None, prev_code_critique: str = None) -> dict:

        sys_prompt = get_sys_prompt(self.config.module_name)
        sys_prompt += f"\n\n### Code language: {self.config.code}\n"

        user_prompt = f"""
### Task:
{request}

{ f"### Code: \n\n```{self.config.code}\n{action_code}\n```" if action_code else "" }

{ f"### Previous code: \n\n```{self.config.code}\n{prev_code}\n```" if prev_code else "" }

{ f"### Previous critique on the code: \n\n{prev_code_critique}\n" if prev_code_critique else "" }
"""

        messages = [
            {
                'role': 'system',
                'content': sys_prompt
            },
            {
                'role': 'user',
                'content': user_prompt
            }
        ]

        raw_response = self.llm(messages)

        if self.config.debug:
            print(f"Raw response from Text Critic: {raw_response}")

        return extract_critique_and_score(raw_response)
    

    def act(self, request: str, action_code: str = None) -> dict:

        sys_prompt = get_sys_prompt(self.config.module_name)
        sys_prompt += f"\n\n### Code language: {self.config.code}\n"

        user_prompt = f"""
### Task:
{request}

{ f"### Code: \n\n```{self.config.code}\n{action_code}\n```" if action_code else "" }
"""

        messages = [
            {
                'role': 'system',
                'content': sys_prompt
            },
            {
                'role': 'user',
                'content': user_prompt
            }
        ]

        raw_response = self.llm(messages)

        if self.config.debug:
            print(f"Raw response from Text Critic: {raw_response}")

        return extract_critique_and_score(raw_response)


class Critic(Agent):

    """
    Critic Agent that combines both vision and text critics.
    """
    vision_critic: VisionCritic = None
    text_critic: TextCritic = None

    def __init__(self, config: CriticConfig):
        super().__init__(config)
        self.vision_critic = VisionCritic(config.vision)
        self.text_critic = TextCritic(config.text)


    def act(self, request: str, action_image: Union[str, Image.Image] = None, action_code: str = None) -> dict:
        """
        Perform an action with the given parameters.

        :param request: The action to perform.
        :param action_image: Image input for the critic.
        :param action_code: Code input for the critic.
        :return: Result of the action.
        """
        vision_critique = None
        text_critique = None

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            vision_future = executor.submit(self.vision_critic.act, request, action_image)
            text_future = executor.submit(self.text_critic.act, request, action_code)
            
            # Get results
            vision_critique = vision_future.result()
            text_critique = text_future.result()

        return {
            'vision_critic': vision_critique,
            'text_critic': text_critique
        }
    
    def act_with_prev_state(self, request: str, action_image: Union[str, Image.Image] = None, action_code: str = None, prev_vision_critique: str = None, prev_text_critique: str = None) -> dict:
        """
        Perform an action with the given parameters, considering previous critiques.
        :param request: The action to perform.
        :param action_image: Image input for the critic.
        :param action_code: Code input for the critic.
        :param prev_vision_critique: Previous critique on the image.    
        :param prev_text_critique: Previous critique on the code.
        :return: Result of the action.
        """
        vision_critique = None
        text_critique = None

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            vision_future = executor.submit(self.vision_critic.act_with_prev_state, request, action_image, prev_vision_critique)
            text_future = executor.submit(self.text_critic.act_with_prev_state, request, action_code, prev_text_critique)
            
            # Get results
            vision_critique = vision_future.result()
            text_critique = text_future.result()
            
        return {
            'vision_critic': vision_critique,
            'text_critic': text_critique
        }