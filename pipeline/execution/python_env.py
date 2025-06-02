from pydantic import BaseModel, Field

import os
import sys 
import time
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..', '..'))

from llm.llm_utils import get_code_from_text_response
from pipeline.execution.env import EnvConfig, Env, random_string


# From @github.com/metal-chart-generation/metal/blob/main/src/agents/utils.py#L62
def extract_validate_run_code(code, code_file, output_name):
      
    # if "plt.show()" in code:
    #     code = code.replace("plt.show()", "")
    # if "plt.tight_layout()" not in code:
    #     code += "\nplt.tight_layout()"
    # if "plt.savefig" not in code:
    #     code += f"\nplt.savefig('{output_name}')"
    # else:
    #     lines_to_be_deleted = []
    #     lines = code.split("\n")
    #     for i, line in enumerate(lines):
    #         if "plt.savefig" in line:
    #             lines_to_be_deleted.append(i)
    #     lines = [line for i, line in enumerate(lines) if i not in lines_to_be_deleted]
    #     lines.append(f"plt.savefig('{output_name}')")
    #     code = "\n".join(lines)
    
    # with open(code_file, "w") as f:
    #     f.write(code)
      
    evaluate_code = (
    "try:\n"
    + "\n".join("    " + line for line in code.strip().splitlines())
    + "\nexcept Exception as e:\n"
    + "    import matplotlib.pyplot as plt\n"
    + "    plt.savefig('{output_name}')\n".format(output_name=output_name)
    + "    with open('{output_name}_error.txt', 'w') as f:\n".format(output_name=output_name)
    + "        f.write(str(e))\n"
    + "    pass\n"
    )
    
    with open(code_file, "w") as f:
        f.write(evaluate_code)
        
    try: 
        os.system(f"python3 {code_file}")
    except Exception as e:
        import matplotlib.pyplot as plt
        plt.savefig(output_name)
        with open(f"{output_name}_error.txt", "w") as f:
            f.write(str(e))
        pass
    
    
    return {
        'code_file_path': code_file,
        'image_file_path': output_name,
    }


class PythonEnvConfig(EnvConfig):
    """
    Configuration for the Python environment.
    """
    module_name: str = Field(default='python_env', description="Code type: either python or html")
    cache_folder: str = Field(default=os.path.join(current_dir, '..', '..', 'temp', 'python') , description="Folder to cache Python files")


class PythonEnv(Env):
    """
    Represents a Python environment that can execute actions based on the provided configuration.
    """
    config: PythonEnvConfig

    def step(self, action: str, run_name: str = '', tag: str = '') -> str:
        """
        Perform an action in the Python environment.

        :param action: The action to perform.
        :return: Result of the action.
        """
        if not run_name:
            run_name = random_string(10)

        html_code = get_code_from_text_response(action)[-1]
        if html_code['language'] not in ['python', 'python3']:
            raise ValueError(f"Unsupported language: {html_code['language']}. Expected 'html', 'javascript', or 'html5'.")
        
        os.makedirs(os.path.join(self.config.cache_folder, run_name), exist_ok=True)
        
        run_time = time.strftime("%Y%m%d-%H%M%S")
        
        python_file_path = os.path.join(self.config.cache_folder, 'code', run_name, f"render_{tag}_{run_time}.py")
        image_file_path = os.path.join(self.config.cache_folder, 'images', run_name, f"render_{tag}_{run_time}.png")

        code = html_code['code']

        extract_validate_run_code(code, python_file_path, image_file_path)
        
        return {
            'code': code,
            'code_file_path': python_file_path,
            'image_file_path': image_file_path,
            'run_name': run_name,
        }