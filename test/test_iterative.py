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

from pipeline.execution import HtmlEnv, HtmlEnvConfig


if __name__ == "__main__":
    # Create a module configuration
    actor_config = ActorConfig(name="Test Actor", model_name="gpt-4.1-mini", code='html')
    vision_critic_config = VisionCriticConfig(name="Vision Critic", model_name="gpt-4o")
    text_critic_config = TextCriticConfig(name="Text Critic", model_name="gpt-4o", code='html')

    critic_config = CriticConfig(name="Test Critic", vision=vision_critic_config, text=text_critic_config, model_name="gpt-4.1-mini")
    module_config = ModuleConfig(name="Test Module", actor_config=actor_config, critic_config=critic_config)
    
    module = Module(config=module_config)
    run_name = "test_run"
    # Create an iterative pipeline
    pipeline = IterativePipeline(module=module, env=HtmlEnv(config=HtmlEnvConfig()), run_name=run_name, debug=True)

    task =   """Alpha: (2000, 50,000), (2005, 60,000), (2010, 65,000), (2020, 80,000)
Beta: (2000, 30,000), (2008, 40,000), (2015, 50,000), (2020, 55,000)
Gamma: (2000, 20,000), (2004, 25,000), (2012, 35,000), (2018, 45,000)

    regenerate the chart. Add a title "Population Growth Over Time" with x-axis label "Year" and y-axis label "Population".
    """
    
    image_path = os.path.join(current_dir, '..', 'example', 'actor_chart.png')

    env_config = HtmlEnvConfig(name="HTML Environment")
    env = HtmlEnv(config=env_config)

    # Run the pipeline with a test request
    result = pipeline.act(request=task, image=image_path)
    print(result)