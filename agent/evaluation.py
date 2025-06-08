from pydantic import BaseModel, Field
from typing import Union
from PIL import Image
import logging

import os
import sys 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent.base import AgentConfig, Agent
from agent.prompt.get_sys_prompt import get_sys_prompt
from utils import open_image, extract_critique_and_score
import logging
logging.basicConfig(level=logging.INFO)

class EvaluatorConfig(AgentConfig):
    """
    Configuration for the evaluator.
    """
    name: str = Field(default='Evaluator Agent', description="Purpose of the agent")
    module_name: str = 'evaluator'


class Evaluator(Agent):
    """
    Represents an evaluator that can perform actions based on the provided configuration.
    """
    config: EvaluatorConfig

    def __init__(self, config: EvaluatorConfig):
        super().__init__(config=config)

    
    def __str__(self):
        """
        String representation of the evaluator.

        :return: String representation of the evaluator.
        """
        return f"Evaluator(name={self.config.name}, model_name={self.config.model_name})"
    

    def llm_score(self, image: Image):

        messages = [
            {
                'role': 'system',
                'content': get_sys_prompt(self.config.module_name)
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
                        'text': "Please evaluate and score the quality of this chart."
                    }
                ]
            }
        ]

        response = self.llm(messages)

        return response


    def act(self, request: str, image : Union[str, Image.Image]) -> dict:
        """
        Perform an action with the given parameters.

        :param action: The action to perform.
        :return: Result of the action.
        """
        # Placeholder for action logic

        if isinstance(image, str):
            if not os.path.exists(image):
                raise ValueError(f"Image path {image} does not exist.")
            image = Image.open(image)


        return extract_critique_and_score(self.llm_score(image))