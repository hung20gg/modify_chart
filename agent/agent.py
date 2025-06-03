from pydantic import BaseModel, Field
from typing import Optional, List

import os
import sys 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from llm import get_llm_wrapper, get_rotate_llm_wrapper

class AgentConfig(BaseModel):
    """
    Configuration for the agent.
    """
    name: str = Field(..., description="Purpose of the agent")
    model_name: str = Field(..., description="Model to be used by the agent")
    debug: bool = Field(default=False, description="Enable debug mode for the agent")

class Agent(BaseModel):
    """
    Represents an agent that can perform actions based on the provided configuration.
    """
    config: AgentConfig
    llm: Optional[object] = Field(default=None, description="Language model used by the agent")

    def __init__(self, config: AgentConfig):
        """
        Initialize the agent with the given configuration.

        :param config: Configuration for the agent.
        """
        super().__init__(config=config)
        self.llm = get_llm_wrapper(config.model_name, multimodal = True)


    def act(self, action: str) -> str:
        """
        Perform an action with the given parameters.

        :param action: The action to perform.
        :param parameters: Optional parameters for the action.
        :return: Result of the action.
        """
        # Placeholder for action logic

        messages = [
            {
                'role': 'user',
                'content': action
            }
        ]

        return self.llm(messages)
    

    def __str__(self):
        """
        String representation of the agent.

        :return: String representation of the agent.
        """
        return f"Agent(name={self.config.name}, model_name={self.config.model_name})"
    
    def __repr__(self):
        """
        String representation of the agent for debugging.
        :return: String representation of the agent.
        """
        return f"Agent(name={self.config.name}, model_name={self.config.model_name})"
    

if __name__ == "__main__":
    # Example usage
    agent_config = AgentConfig(name="Test Agent", model_name="gpt-4o")
    agent = Agent(config=agent_config)
    print(agent)
    
    action_result = agent.act("What is the capital of Vietnam?")
    print(action_result)