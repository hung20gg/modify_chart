import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from pipeline.module import Module, ModuleConfig
from pipeline.iterative import IterativePipeline

from agent import (
    ActorConfig,
    Actor,
    AgentConfig,
    Agent,
    CriticConfig,
    Critic,
    TextCriticConfig,
    TextCritic,
    VisionCriticConfig,
    VisionCritic
)

from pipeline.execution import HtmlEnv, HtmlEnvConfig, PythonEnv, PythonEnvConfig


if __name__ == "__main__":
    
    language = 'python'  # or 'python'
    
    if language == 'html':
        env = HtmlEnv(config=HtmlEnvConfig(name="HTML Environment"))
    elif language == 'python':
        env = PythonEnv(config=PythonEnvConfig(name="Python Environment"))
    else:
        raise ValueError(f"Unsupported language: {language}. Expected 'html' or 'python'.")
    
    code_model = 'gemini-2.0-flash-lite'
    vision_model = 'gemini-2.0-flash'

    # Create a module configuration
    actor_config = ActorConfig(name="Test Actor", model_name=code_model, code=language)
    vision_critic_config = VisionCriticConfig(name="Vision Critic", model_name=vision_model)
    text_critic_config = TextCriticConfig(name="Text Critic", model_name=vision_model, code=language)

    critic_config = CriticConfig(name="Test Critic", vision=vision_critic_config, text=text_critic_config, model_name=code_model)
    module_config = ModuleConfig(name="Test Module", actor_config=actor_config, critic_config=critic_config)
    
    module = Module(config=module_config)
    run_name = "test_run"
    # Create an iterative pipeline
    pipeline = IterativePipeline(module=module, env=env, run_name=run_name, debug=True)

    task =   """Alpha: (2000, 50,000), (2005, 60,000), (2010, 65,000), (2020, 80,000)
Beta: (2000, 30,000), (2008, 40,000), (2015, 50,000), (2020, 55,000)
Gamma: (2000, 20,000), (2004, 25,000), (2012, 35,000), (2018, 45,000)

    regenerate the chart. Change title to "Salary Over Time" with x-axis label "Year" and y-axis label "Salary".
    """
    
    image_path = os.path.join(current_dir, '..', 'example', 'actor_chart.png')

    # # Run the pipeline with a test request
    # result = pipeline.act(request=task, image=image_path)
    # print(result)
    
    image_generator = pipeline.stream_act(request=task, image=image_path)
    for image in image_generator:
        print('GENERATOR:',image)