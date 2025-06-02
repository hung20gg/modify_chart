from pydantic import BaseModel, Field
from html2image import Html2Image

import os
import sys
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..', '..'))

from llm.llm_utils import get_code_from_text_response
from pipeline.execution.env import EnvConfig, Env, random_string


HTI = Html2Image()

class HtmlEnvConfig(EnvConfig):
    """
    Configuration for the HTML environment.
    """
    module_name: str = Field(default='html_env', description="Code type: either python or html")
    cache_folder: str = Field(default=os.path.join(current_dir, '..', '..', 'temp', 'html') , description="Folder to cache HTML files")


class HtmlEnv(Env):
    """
    Represents an HTML environment that can execute actions based on the provided configuration.
    """
    config: HtmlEnvConfig

    def step(self, action: str, run_name: str = '', tag: str = '') -> str:
        """
        Perform an action in the HTML environment.

        :param action: The action to perform.
        :return: Result of the action.
        """

        if not run_name:
            run_name = random_string(10)

        html_code = get_code_from_text_response(action)[-1]
        if html_code['language'] not in ['html', 'javascript', 'html5']:
            raise ValueError(f"Unsupported language: {html_code['language']}. Expected 'html', 'javascript', or 'html5'.")
        
        os.makedirs(os.path.join(self.config.cache_folder, run_name), exist_ok=True)
        
        run_time = time.strftime("%Y%m%d-%H%M%S")
        html_file_path = os.path.join(self.config.cache_folder, 'code', run_name, f"render_{tag}_{run_time}.html")
        image_file_path = os.path.join(self.config.cache_folder, 'images', run_name, f"render_{tag}_{run_time}.png")

        code = html_code['code']
        with open(html_file_path, 'w') as f:
            f.write(code)
        HTI.screenshot(html_file=html_file_path, save_as=image_file_path)
        
        return {
            'code': code,
            'code_file_path': html_file_path,
            'image_file_path': image_file_path,
            'run_name': run_name,
        }
