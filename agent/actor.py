from pydantic import BaseModel, Field
from typing import Union
from PIL import Image
import os
import sys 
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

# import dotenv
# dotenv.load_dotenv(os.path.join(current_dir, '..', '.env'))

from agent.prompt.get_sys_prompt import get_sys_prompt
from agent.base import AgentConfig, Agent
from utils import open_image

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

    def get_sys_prompt(self) -> str:
        
        code_snippet = ""
        if self.config.code == 'python':
            code_snippet = "### Code sample for python chart:\n\n"
            
            with open(os.path.join(current_dir, '..', 'example', 'chart.py'), 'r') as f:
                code_snippet += '```python\n' + f.read() + '\n```'
        elif self.config.code == 'html':
            code_snippet = "### Code sample for html chart:"
            
            with open(os.path.join(current_dir, '..', 'example', 'chart.html'), 'r') as f:
                code_snippet += '```html\n' + f.read() + '\n```'
        else:
            raise ValueError(f"Unsupported code type: {self.config.code}")
        
        
        return get_sys_prompt(self.config.module_name) + f"\n\n{code_snippet}"

    def python_prompt(self, action:str, prev_state_code: str = None, prev_state_critique: str = None):

        """
        Generate a Python prompt based on the action and previous state.

        :param action: The action to perform.
        :param prev_state_code: Previous state code.
        :param prev_state_critique: Previous state critique.
        :return: Formatted Python prompt.
        """
        prev_state_code = f"### Previous code for chart: \n\n{prev_state_code}\n"
        prev_state_critique = f"### Previous critique on the chart: \n\n{prev_state_critique}\n" if prev_state_critique else ""
        
        return f"""
<image>
### Code language: python

### Task: 
{action}

{ prev_state_code if prev_state_code else "" }
{ prev_state_critique if prev_state_critique else "" }"""


    def html_prompt(self, action: str, prev_state_code: str = None, prev_state_critique: str = None):

        prev_state_code = f"### Previous code for chart: \n\n{prev_state_code}\n"
        prev_state_critique = f"### Previous critique on the chart: \n\n{prev_state_critique}\n" if prev_state_critique else ""

        return f"""
<image>
### Code language: html

### Task: 
{action}

{ prev_state_code if prev_state_code else "" }
{ prev_state_critique if prev_state_critique else "" }"""


    def act(self, 
            request: str, 
            image : Union[str, Image.Image] = None, 
            prev_state_code: str = None, 
            prev_state_critique: str = None,
            run_name: str = None,
            tag: str = None) -> dict:
        """
        Perform an action with the given parameters.

        :param request: The action to perform.
        :return: Result of the action.
        """

        if isinstance(image, Image.Image) and self.config.image_path:
            raise ValueError("Image should be a path string, since force use image_path is set to True.")

        # Placeholder for action logic
        if isinstance(image, str):
            image_path = image
            if os.path.exists(image):
                image = open_image(image)
            else:
                raise ValueError(f"Image path {image} does not exist.")
        else:
            image_path = None

        sys_prompt = self.get_sys_prompt()

        if self.config.code == 'html':
            user_prompt = self.html_prompt(request, prev_state_code, prev_state_critique)
        else:
            user_prompt = self.python_prompt(request, prev_state_code, prev_state_critique)

        content = []
        if isinstance(image, Image.Image):
            content.append({
                'type': 'image',
                'image': image
            })
        content.append({
            'type': 'text',
            'text': user_prompt.strip()
        })

        messages = [
            {
                'role': 'system',
                'content': sys_prompt
            },
            {
                'role': 'user',
                'content': content
            }
        ]

        action = self.llm(messages, run_name=run_name, tag=f'Actor_{tag}', images_path=image_path)

        if self.config.debug:
            print(f"Action: {action}")

        return {
            'action': action
        }

    def act_with_prev_state(self, *args, **kwargs) -> dict:
        return self.act(*args, **kwargs)

    def __str__(self):
        """
        String representation of the actor.

        :return: String representation of the actor.
        """
        return f"Actor(name={self.config.name}, model_name={self.config.model_name})"
    

if __name__ == "__main__":
    actor_config = ActorConfig(name="Test Actor", model_name='gpt-4.1-mini')
    actor = Actor(config=actor_config)
    print(actor)
    
    task =   """Alpha: (2000, 50,000), (2005, 60,000), (2010, 65,000), (2020, 80,000)
Beta: (2000, 30,000), (2008, 40,000), (2015, 50,000), (2020, 55,000)
Gamma: (2000, 20,000), (2004, 25,000), (2012, 35,000), (2018, 45,000)

    Change line graph to bar chart, and add a title "Population Growth Over Time" with x-axis label "Year" and y-axis label "Population".
    """
    
    image_path = os.path.join(current_dir, '..', 'example', 'actor_chart.png')

    result = actor.act(task, image=image_path, prev_state_code=None, prev_state_critique=None)
    print(result['action'])