import os 
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))
from uuid import uuid4

from pipeline.execution import Env
from pipeline.module import Module

from typing import Optional, List, Dict, Any, Union, Generator
from pydantic import BaseModel, Field
from PIL import Image
import logging

class IterativePipeline(BaseModel):
    """
    Iterative pipeline for executing modules in a sequence.
    """
    module: Module = Field(..., description="List of modules to execute in the pipeline")
    env: Env = Field(default_factory=Env, description="Environment for executing the modules")
    tag: str = Field(default='', description="Tag for the run")
    max_iterations: int = Field(default=5, description="Maximum number of iterations to run the pipeline")
    debug: bool = Field(default=False, description="Enable debug mode for the pipeline")
    run_name: str = Field(default=str(uuid4()), description="Name of the run")


    def __init__(self, **data):
        """
        Initialize the iterative pipeline with the given configuration.
        """
        super().__init__(**data)
        
        if self.debug:
            logging.info(f"Initialized IterativePipeline with run_name: {self.run_name} and tag: {self.tag}")
            self.module.debug = True


    @staticmethod
    def concatenate_critiques(critique_list: Dict[str, str]) -> str:
        """
        Concatenate a list of critiques into a single string.
        """
        return "\n".join([f"### {key}: \n{value}\n\n" for key, value in critique_list.items()])
    
    def act(self, request: str, image: Union[str, Image.Image] = None) -> Dict[str, Any]:
        """
        Run the pipeline with the given inputs.
        """
        
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
                tag=f"{self.tag}_iteration_{i + 1}"
            )

            if self.debug:
                print(f"Iteration {i + 1}: {result}")

            results.append(result)

            prev_state_code = result['actor_result']['action']
            prev_state_critique = self.concatenate_critiques({
                'Vision critique': result['critic_result']['vision_critic']['critique'],
                'Text critique': result['critic_result']['text_critic']['critique']
            })
            
            if result['critic_result']['score'] >= 4:
                break
            
        
        return results
    
    
    def stream_act(self, request: str, image: Union[str, Image.Image] = None) -> Generator[str, None, None]:
        """
        Run the pipeline with the given inputs in a streaming manner.
        """
        
        prev_state_critique = None
        prev_state_code = None
        
        results = []
        
        for i in range(self.max_iterations):
            if self.debug:
                print(f"Starting iteration {i + 1}")
            
            result = None
            error_occurred = False
            
            for chunk in self.module.stream_act(
                env=self.env,
                request=request,
                image=image,
                prev_state_code=prev_state_code,
                prev_state_critique=prev_state_critique,
                run_name=self.run_name,
                tag=f"stream_{self.tag}_iteration_{i + 1}"
            ):
                # Handle error cases
                if chunk.get('status') == 'error':
                    error_occurred = True
                    yield {
                        'iteration': i + 1,
                        'status': 'error',
                        'error': chunk.get('error'),
                        'message': chunk.get('message'),
                        'language': chunk.get('language', 'python')
                    }
                    break
                
                # Store the final result when it contains critic_result
                elif chunk.get('status') == 'completed':
                    result = chunk
                    results.append(chunk)
                    # Yield the complete iteration result
                    yield {
                        'iteration': i + 1,
                        'status': 'iteration_completed',
                        'result': chunk,
                        'language': chunk.get('language', 'python'),
                        'image_file_path': chunk.get('output_image'),
                        'html_code': chunk.get('html_code'),
                        'score': chunk['critic_result']['score']
                    }
                else:
                    # Yield intermediate status updates
                    yield {
                        'iteration': i + 1,
                        'status': chunk.get('status', 'processing'),
                        'language': chunk.get('language', 'python'),
                        'image_file_path': chunk.get('image_file_path'),
                        'html_code': chunk.get('html_code')
                    }

            if self.debug:
                print(f"Iteration {i + 1}: {result}")

            # Break if error occurred or no result
            if error_occurred or result is None:
                if self.debug:
                    if error_occurred:
                        print(f"Error occurred in iteration {i + 1}, stopping pipeline")
                    else:
                        print(f"No result from iteration {i + 1}, breaking")
                break

            prev_state_code = result['actor_result']['action']
            prev_state_critique = self.concatenate_critiques({
                'Vision critique': result['critic_result']['vision_critic']['critique'],
                'Text critique': result['critic_result']['text_critic']['critique']
            })
            
            # Check if we've reached a good enough score
            if result['critic_result']['score'] >= 4:
                if self.debug:
                    print(f"Score threshold reached: {result['critic_result']['score']}")
                break
            
        yield {
            'status': 'finished',
            'total_iterations': len(results),
            'results': results
        }
    
    
    def act_with_prev_state(self, request: str, image: Union[str, Image.Image] = None, prev_state_code: str = None, prev_state_critique: str = None) -> Dict[str, Any]:
        """
        Run the pipeline with the given inputs and previous state.
        """
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
                tag=f"{self.tag}_iteration_{i + 1}"
            )

            if self.debug:
                print(f"Iteration {i + 1}: {result}")

            results.append(result)

            prev_state_code = result['actor_result']['action']
            prev_state_critique = self.concatenate_critiques({
                'Vision critique': result['critic_result']['vision_critic']['critique'],
                'Text critique': result['critic_result']['text_critic']['critique']
            })
            
            if result['critic_result']['score'] >= 4:
                break
            
        
        return results