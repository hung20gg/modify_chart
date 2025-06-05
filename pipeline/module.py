
import os 
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))
from pydantic import Field, BaseModel
from typing import Optional

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

from pipeline.execution import Env, PythonEnv, PythonEnvConfig
from utils import merge_images

class ModuleConfig(BaseModel):
    """
    Configuration for the module.
    """
    name: str = Field(default='Module Agent', description="Purpose of the agent")
    module_name: str = 'module'
    actor_config: ActorConfig = Field(default_factory=ActorConfig, description="Configuration for the actor module")
    critic_config: CriticConfig = Field(default_factory=CriticConfig, description="Configuration for the critic module")

class Module(BaseModel):
    """
    Represents a module that can perform actions based on the provided configuration.
    """
    config: ModuleConfig
    actor: Optional[Actor] = None
    critic: Optional[Critic] = None
    debug: bool = Field(default=False, description="Enable debug mode for the module")
    

    def __init__(self, config: ModuleConfig):
        super().__init__(config=config)
        self.actor = Actor(config=config.actor_config)
        self.critic = Critic(config=config.critic_config)


    def act(self,
            env: Env,
            request: str, 
            image=None, 
            prev_state_code=None, 
            prev_state_critique=None, 
            run_name: str = '', 
            tag: str = '') -> dict:
        
        """
        Perform an action with the given parameters.

        :param action: The action to perform.
        :param image: Optional image input for the actor.
        :param prev_state_code: Optional previous state code for the actor.
        :param prev_state_critique: Optional previous state critique for the critic.
        :return: Result of the action.
        """
        # Delegate action to actor and critic
        actor_result = self.actor.act(request, image, prev_state_code, prev_state_critique)
        action = actor_result.get('action', request)

        if self.debug:
            print(f"Actor action: {action}")

        transition = env.step(action, run_name=run_name, tag=tag)

        combined_image = merge_images([image, transition['image_file_path']],
                                       titles=['Input Image', 'Transition Image'],
                                       run_name=run_name, 
                                       tag=tag,
                                       save_folder=env.config.cache_folder,
                                       )

        action_code = transition.get('code', None)
        critic_result = self.critic.act(request,
                                         action_code=action_code,
                                         action_image=combined_image)

        if self.debug:
            print(f"Critic result: {critic_result}")

        return {
            "actor_result": actor_result,
            "critic_result": critic_result
        }
    

    def act_with_prev_state(self,
            env: Env, 
            request: str, 
            image=None, 
            prev_state_code=None, 
            prev_state_critique=None, 
            run_name: str = '', 
            tag: str = '') -> dict:
        """
        Perform an action with the given parameters, considering previous state.

        :param request: The action to perform.
        :param image: Optional image input for the actor.
        :param prev_state_code: Optional previous state code for the actor.
        :param prev_state_critique: Optional previous state critique for the critic.
        :return: Result of the action.
        """
        pass

    def __str__(self):
        """
        String representation of the module.

        :return: String representation of the module.
        """
        return f"Module(name={self.config.name})"
    

if __name__ == "__main__":

    actor_config = ActorConfig(name="Test Actor", model_name="gpt-4.1-mini", code='python')
    vision_critic_config = VisionCriticConfig(name="Vision Critic", model_name="gpt-4o")
    text_critic_config = TextCriticConfig(name="Text Critic", model_name="gpt-4o", code='python')

    critic_config = CriticConfig(name="Test Critic", vision=vision_critic_config, text=text_critic_config, model_name="gpt-4.1-mini")
    module_config = ModuleConfig(name="Test Module", actor_config=actor_config, critic_config=critic_config)
    module = Module(config=module_config)
    print(module)

    task =   """Alpha: (2000, 50,000), (2005, 60,000), (2010, 65,000), (2020, 80,000)
Beta: (2000, 30,000), (2008, 40,000), (2015, 50,000), (2020, 55,000)
Gamma: (2000, 20,000), (2004, 25,000), (2012, 35,000), (2018, 45,000)

    Change line graph to bar chart, and add a title "Population Growth Over Time" with x-axis label "Year" and y-axis label "Population".
    """
    
    image_path = os.path.join(current_dir, '..', 'example', 'actor_chart.png')
    
    env_config = PythonEnvConfig(name="Python Environment")
    env = PythonEnv(config=env_config)
    result = module.act(env, task, image=image_path, prev_state_code=None, prev_state_critique=None)
    print(result['actor_result']['action'])
    print(result['critic_result'])