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
    
    code_model = 'google:gemma-3-4b-it'
    vision_model = 'gemini-2.5-flash-preview-05-20'

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

    task =   """Change the chart type to bar chart and change the title to 'Financial Sector Performance'.
    """
    
    image_path = os.path.join(current_dir, '..', 'example', '112026.png')

    # # Run the pipeline with a test request
    # result = pipeline.act(request=task, image=image_path)
    # print(result)
    
    image_generator = pipeline.stream_act(request=task, image=image_path)
    for image in image_generator:
        print('GENERATOR:',image)