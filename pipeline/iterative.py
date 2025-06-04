import os 
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from pipeline.execution import Env
from pipeline.module import Module

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class IterativePipeline(BaseModel):
    """
    Iterative pipeline for executing modules in a sequence.
    """
    modules: List[Module] = Field(default_factory=list, description="List of modules to execute in the pipeline")
    env: Env = Field(default_factory=Env, description="Environment for executing the modules")
    run_name: str = Field(default='', description="Name of the run")
    tag: str = Field(default='', description="Tag for the run")
    max_iterations: int = Field(default=5, description="Maximum number of iterations to run the pipeline")