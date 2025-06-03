from pydantic import BaseModel, Field
from typing import Union
from PIL import Image

import os
import sys 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent.agent import AgentConfig, Agent
from agent.prompt.get_sys_prompt import get_sys_prompt


def extract_critique_and_score(raw_response: str) -> str:
    """
    Extracts the critique and score from the raw response.

    :param raw_response: The raw response string.
    :return: A tuple containing the critique and score.
    """
    # Assuming the response is formatted as "Critique: <critique> Score: <score>"
    critique = raw_response
    final_score = 0

    if '## Critique:' in raw_response and '## Score:' in raw_response:
        critique = raw_response.split('## Critique:')[1].split('## Score:')[0].strip()
        score = raw_response.split('## Score:')[1].strip()
        
        if score.isdigit():
            final_score = int(score)
        
        elif '\\boxed{' in score:
            score = score.split('\\boxed{')[1].split('}')[0]
            if score.isdigit():
                final_score = int(score)
        
        return {
            'critique': critique,
            'score': final_score
        }


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

    vision: VisionCriticConfig = Field(default_factory=VisionCriticConfig)
    text: TextCriticConfig = Field(default_factory=TextCriticConfig)


class VisionCritic(Agent):
    """
    Vision Critic Agent that evaluates visual inputs.
    """
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

        if action_image:
            vision_critique = self.vision_critic.act(request, action_image)

        if action_code:
            text_critique = self.text_critic.act(request, action_code)

        return {
            'vision_critique': vision_critique,
            'text_critique': text_critique
        }
    
    def act_with_prev_state(self, request: str, action_image: Union[str, Image.Image] = None, action_code: str = None, prev_vision_critique: str = None, prev_text_critique: str = None) -> dict:
        """
        Perform an action with the given parameters, considering previous critiques.
        :param request: The action to perform.
        :param
        action_image: Image input for the critic.
        :param action_code: Code input for the critic.
        :param prev_vision_critique: Previous critique on the image.    
        :param prev_text_critique: Previous critique on the code.
        :return: Result of the action.
        """
        vision_critique = None
        text_critique = None

        if action_image:
            vision_critique = self.vision_critic.act_with_prev_state(request, action_image, prev_vision_critique)

        if action_code:
            text_critique = self.text_critic.act_with_prev_state(request, action_code, prev_text_critique)

        return {
            'vision_critique': vision_critique,
            'text_critique': text_critique
        }