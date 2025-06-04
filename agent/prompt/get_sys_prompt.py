import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CURRENT_DIR, '..', '..'))

def get_sys_prompt(module_name: str) -> str:
    """
    Get the system prompt for the specified module.

    :param module_name: Name of the module to get the system prompt for.
    :return: System prompt string.
    """
    sys_prompt = f"You are a helpful assistant"

    if module_name == "actor":
        with open(os.path.join(CURRENT_DIR, 'actor_prompt.md'), 'r') as f:
            sys_prompt = f.read()
    
    elif module_name == "text_critic":
        with open(os.path.join(CURRENT_DIR, 'text_critic_prompt.md'), 'r') as f:
            sys_prompt = f.read()
    
    elif module_name == "vision_critic":
        with open(os.path.join(CURRENT_DIR, 'vision_critic_prompt.md'), 'r') as f:
            sys_prompt = f.read()

    elif module_name == "evaluator":
        with open(os.path.join(CURRENT_DIR, 'evaluator_prompt.md'), 'r') as f:
            sys_prompt = f.read()

    return sys_prompt.strip()