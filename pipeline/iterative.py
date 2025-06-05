import os 
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from pipeline.execution import Env
from pipeline.module import Module

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from PIL import Image

class IterativePipeline(BaseModel):
    """
    Iterative pipeline for executing modules in a sequence.
    """
    module: Module = Field(..., description="List of modules to execute in the pipeline")
    env: Env = Field(default_factory=Env, description="Environment for executing the modules")
    run_name: str = Field(default='', description="Name of the run")
    tag: str = Field(default='', description="Tag for the run")
    max_iterations: int = Field(default=5, description="Maximum number of iterations to run the pipeline")
    
    @staticmethod
    def concatenate_critiques(critique_list: Dict[str]) -> str:
        """
        Concatenate a list of critiques into a single string.
        """
        return "\n".join([f"### {key}: \n{value}\n\n" for key, value in critique_list.items()])
    
    def act(self, request: str, image: Union[str, Image.Image] = None) -> Dict[str, Any]:
        """
        Run the pipeline with the given inputs.
        """
        if inputs is None:
            inputs = {}
        
        prev_state_critique = None
        prev_state_code = None
        
        results = []
        
        for i in range(self.max_iterations):
            result = self.module.act(
                env=self.env,
                request=request,
                image=image,
                prev_state_code=prev_state_code,
                prev_state_critique=prev_state_critique,
                run_name=self.run_name,
                tag=self.tag
            )
            
            results.append(result)
            
            prev_state_code = result['actor_result']['action']
            prev_state_critique = self.concatenate_critiques({
                'vision critique': result['critic_result']['vision_critic']['critique'],
                'text critique': result['critic_result']['text_critic']['critique']
            })
            
            if result['critic_result']['text_critic']['score'] >= 4 and result['critic_result']['vision_critic']['score'] >= 4:
                break
            
        
        return results