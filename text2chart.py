from pydantic import BaseModel, Field
from typing import Generator

from text2sql.text2sql_agent import SQLAgent
from text2sql.postgres_utils import PostgresDB
from PIL import Image
from pipeline.execution import Env
from pipeline.module import Module, ModuleConfig
from pipeline.iterative import IterativePipeline
from agent import (
    ActorConfig,
    Actor,
    CriticConfig,
    TextCriticConfig,
    VisionCriticConfig
)
from pipeline.execution import HtmlEnv, HtmlEnvConfig, PythonEnv, PythonEnvConfig
import logging

from utils import open_image
from llm import get_llm_wrapper
from llm.llm_utils import get_json_from_text_response

class Router(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    model_name: str = "gpt-4.1-mini"
    llm: any = Field(default_factory=lambda: get_llm_wrapper("gpt-4.1-mini"))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = get_llm_wrapper(self.model_name)

    @staticmethod
    def __flatten_response(messages: list[str]) -> str:
        """
        Flatten the messages into a single string for routing.
        """
        text = ""
        for message in messages:
            text += '### Previous Response:\n' + message + '\n'
        return text.strip()


    def router(self, request: str, last_response: list[dict], image: Image.Image = None) -> str:
        """
        Route the request to the appropriate agent based on the content of the request.
        """
        system_prompt = """
You are a routing agent, and based on the user's request and previous responses, you will determine which agent should handle the request.

You have 2 agents available:
1. SQL: Handles SQL-related questions and generates SQL queries.
2. Chart: Handles chart modification requests and generates code to modify charts.
3. Pass: If the request does not match any agent's capabilities, you will pass the request

Depend on the user's request, decide which agent should handle the request.
For example, user wants to create chart that does not have adequate data or adding new data, you will pass the request to SQLAgent to generate the SQL query to get the data first.

And the SQL Agent task should not have the part 'Create chart', it should only focus on generating the SQL query to get the data.

If no data is available for visualization, you should pass the request to the SQL agent to generate the SQL query to get the data first.
Any request that add features (new line, new data, new chart) (e.g: Thêm đường kế hoạch, Thêm tỉnh Thanh Hoá) should be passed to the SQL agent to collect additional data.

Return the agent and the corresponding task in the following format:
```json
{
    "agent": "SQL|Chart|Pass",
    "task": "The task for the agent"
}
```

Maintain the task as user's language for SQL's task, and only return the translation with Chart task.
"""

        last_response_text = self.__flatten_response(last_response).strip()

        user_prompt = ""

        if last_response_text:
            user_prompt += "### Previous Response:\n" + last_response_text + "\n"
        user_prompt += "### User Request:\n" + request + "\n"

        if image:
            messages = [
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': user_prompt.strip()
                        },
                        {
                            'type': 'image',
                            'image': image
                        }
                    ]
                }
            ]
        else:
            messages = [
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': user_prompt.strip()
                }
            ]

        response = self.llm(messages)

        try:
            response_json = get_json_from_text_response(response, new_method=True)
            return response_json
        except Exception as e:
            logging.error(f"Error occurred while getting JSON from response: {e}")
            return {"agent": "Pass", "task": "Unable to process request"}

class Text2Chart(BaseModel):

    model_config = {"arbitrary_types_allowed": True}
    router: Router = Field(default_factory=Router)
    sql_agent: SQLAgent = Field(default_factory=SQLAgent)
    actor: Actor = Field(default = None)
    iterative_pipeline: IterativePipeline = Field(default_factory=lambda: IterativePipeline(name="Iterative Chart Pipeline"))
    images: list[Image.Image] = Field(default_factory=list)
    max_iterations: int = 3
    debug: bool = False
    messages: list[dict] = Field(default_factory=list)
    prev_requests: list[str] = Field(default_factory=list)
    env: Env = Field(default = None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.actor is None or self.env is None:
            self.env = self.iterative_pipeline.env
            self.actor = self.iterative_pipeline.module.actor

        self.reset()

    def reset(self):
        """
        Reset the state of the Text2Chart instance.
        """
        self.messages = [{
            'role': 'system',
            'content': 'You are a helpful assistant'
        }]
        self.images = []
        self.prev_requests = []

    def process_request_single(self, request: str, image: Image.Image = None) -> Generator[dict, None, None]:
        """
        Process a single request and return the response.
        """

        last_response = self.prev_requests[:-4].copy()

        if not image:
            image = self.images[-1] if self.images else None

        # Route the request
        routing_result = self.router.router(request, last_response, image)
        agent = routing_result.get("agent", "Pass")
        task = routing_result.get("task", "")

        yield {
            'type': 'text',
            "status": "routing",
            "message": f"Routing request to agent: {agent} with task: {task}"
        }

        if agent == "Pass":

            yield {
                'type': 'text',
                "status": "pass",
                "message": "Request passed to the next agent or no action taken."
            }

            return

        if agent == "SQL":
            # Use SQL Agent to generate SQL query
            table = self.sql_agent.generate_sql(self.sql_agent.db, task, to_markdown=True)

            yield {
                'type': 'table',
                "status": "table",
                "message": "SQL query generated successfully.",
                "content": table
            }

            request += f"\n\n### SQL Query Result:\n{table}\n"



        if len(self.prev_requests) != 0:
            temp_request = '### Previous Request:\n' + self.prev_requests[-1] + '\n' + request
        else:
            temp_request = request
        self.prev_requests.append(request)

        action = self.actor.act(
            request=temp_request,
            image=image,
            run_name=f"Text2Chart_{self.router.model_name}",
            tag="single_text2chart"
        )

        print(f"Action generated by actor: {action}")

        action = action['action']
        if not action:
            yield {
                'type': 'text',
                "status": "error",
                "message": "No action generated by the actor."
            }
            return
        
        transition = self.env.step(
            action=action,
            run_name=f"Text2Chart_{self.router.model_name}",
            tag="single_text2chart"
        )

        self.images.append(open_image(transition.get('image_file_path', None)))

        yield {
            'type': 'code',
            'code': action,
            'language': self.actor.config.code,
            'status': 'completed',
            'image_file_path': transition.get('image_file_path', None),
            'message': "Action executed successfully.",
        }


    def process_request(self, request: str, image: Image.Image = None) -> Generator[dict, None, None]:
        """
        Process a request and return the response.
        """
        last_response = self.prev_requests[:-4].copy()

        if not image:
            image = self.images[-1] if self.images else None

        # Route the request
        routing_result = self.router.router(request, last_response, image)
        agent = routing_result.get("agent", "Pass")
        task = routing_result.get("task", "")

        if agent == "Pass":

            yield {
                'type': 'text',
                "status": "pass",
                "message": "Request passed to the next agent or no action taken."
            }

            return

        if agent == "SQL":
            # Use SQL Agent to generate SQL query
            table = self.sql_agent.generate_sql(self.sql_agent.db, task, to_markdown=True)

            if self.debug:
                print(f"Generated SQL query:\n{table}")

            yield {
                'type': 'table',
                "status": "table",
                "message": "SQL query generated successfully.",
                "content": table
            }

            request += f"\n\n### SQL Query Result:\n{table}\n"



        if len(self.prev_requests) != 0:
            temp_request = '### Previous Request:\n' + self.prev_requests[-1] + '\n' + request
        else:
            temp_request = request

        if self.debug:
            logging.debug(f"Processing request: {temp_request}")

        self.prev_requests.append(request)

        image_generator = self.iterative_pipeline.stream_act(
            request=temp_request,
            image=image,
        )

        for chunk in image_generator:
            yield chunk



if __name__ == "__main__":

    code_model = "gpt-4.1-mini"
    vision_model = "gpt-4.1-mini"
    sql_model = "gpt-4.1"
    router_model = "gpt-4.1-mini"

    actor_config = ActorConfig(name="Actor", model_name=code_model, code='python', debug=True)
    vision_critic_config = VisionCriticConfig(name="Vision Critic", model_name=vision_model, debug=True)
    text_critic_config = TextCriticConfig(name="Text Critic", model_name=vision_model, code='python', debug=True)
    critic_config = CriticConfig(name="Critic", vision=vision_critic_config, text=text_critic_config, model_name=code_model)
    module_config = ModuleConfig(name="Module", actor_config=actor_config, critic_config=critic_config, code='python', debug=True)
    module = Module(config=module_config)
    env = PythonEnv(config=PythonEnvConfig(name="Python Environment"))

    iterative_pipeline = IterativePipeline(module=module, env=env, max_iterations=3, debug=True)
    router = Router(model_name=router_model)
    db = PostgresDB(host='localhost', database='postgres', user='postgres', password='12345678', port='5432')
    sql_agent = SQLAgent(db=db, model_name="gpt-4.1")
    text2chart = Text2Chart(
        router=router,
        sql_agent=sql_agent,
        iterative_pipeline=iterative_pipeline,
        actor=module.actor,
        env=env,
        debug=True
    )

    request = 'Vẽ biểu đồ thực hiện lũy kế Tiêu dùng thực di động các ngày trong tháng 3 năm 2025 của Quảng Trị'
    image = None  # Replace with an actual image if needed
    for response in text2chart.process_request_single(request, image):
        print(response)