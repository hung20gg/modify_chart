import os
import sys 

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from text2sql.postgres_utils import PostgresDB
from text2sql.text2sql_utils import TIR_reasoning, df_to_markdown
from llm import get_llm_wrapper, get_rotate_llm_wrapper

from pydantic import BaseModel, Field
from typing import List, Optional

prompt = """
You are a SQL agent that can answer questions about a database.

Here is the database schema:
{schema}

Your task is to generate a SQL query based on the user's question.
The SQL query should be valid and executable on the database.

You must generate/regenerate SQL
"""



class SQLAgent(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    db: PostgresDB = Field(default_factory=PostgresDB)
    model_name: str = "gpt-4.1-mini"
    llm: Optional[any] = None  # Placeholder for LLM wrapper

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = get_llm_wrapper(self.model_name)


    def generate_sql(self, db: PostgresDB, question: str, previous_query: str = None, to_markdown: bool = False) -> str:
        """
        Generate a SQL query based on the user's question.
        """
        schema = self.db.get_schema()
        prompt_with_schema = prompt.format(schema=schema)

        if previous_query:
            question = "### Previous Query:\n" + previous_query + "\n### New question:\n" + question

        messages = [
            {"role": "system", "content": prompt_with_schema},
            {"role": "user", "content": question}
        ]

        response = self.llm(messages)

        print("LLM Response:", response)

        errors, tables = TIR_reasoning(response, db, verbose=False)

        if to_markdown:
            table_string = ""
            for table in tables:
                table = df_to_markdown(table)
                table_string += table + "\n"
            return table_string

        return tables


if __name__ == "__main__":
    # Example usage
    db = PostgresDB(host='localhost', database='postgres', user='postgres', password='12345678', port='5432')
    agent = SQLAgent(db=db, model_name="gpt-4.1")

    question = "thực hiện và kế hoạch Thuê bao Register tăng thêm của Vĩnh Phúc trong nửa cuối năm 2023"
    previous_query = None  # Optional, can be used to provide context

    table = agent.generate_sql(db, question, previous_query)

    print("Query Results:\n", df_to_markdown(table))

