
import os 
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))
from pydantic import Field

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

from pipeline.execution import Env
from pipeline.utils import merge_images

class ModuleConfig(AgentConfig):
    """
    Configuration for the module.
    """
    name: str = Field(default='Module Agent', description="Purpose of the agent")
    module_name: str = 'module'
    actor_config: ActorConfig = Field(default_factory=ActorConfig, description="Configuration for the actor module")
    critic_config: CriticConfig = Field(default_factory=CriticConfig, description="Configuration for the critic module")

class Module(Agent):
    """
    Represents a module that can perform actions based on the provided configuration.
    """
    config: ModuleConfig
    actor = Actor
    critic = Critic

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

        transition = env.step(action, run_name=run_name, tag=tag)

        combined_image = merge_images([image, transition['image_file_path']],
                                      titles=['Input Image', 'Transition Image'],
                                        run_name=run_name, tag=tag
                                      )
        action_code = transition.get('code', None)
        critic_result = self.critic.act(request, 
                                        action_code=action_code,
                                        action_image=combined_image)


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
        return f"Module(name={self.config.name}, model_name={self.config.model_name})"
    

if __name__ == "__main__":

    actor_config = ActorConfig(name="Test Actor", module_name="module")
    critic_config = CriticConfig(name="Test Critic", module_name="module")
    module_config = ModuleConfig(name="Test Module", actor_config=actor_config, critic_config=critic_config)
    module = Module(config=module_config)
    print(module)
