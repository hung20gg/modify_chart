import pandas as pd
import copy

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


import sys 
sys.path.append("..")
from llm.llm_utils import get_code_from_text_response


def df_to_markdown(df, adjust:str = 'keep') -> str:
    if not isinstance(df, pd.DataFrame):
        return str(df)
    
    df = copy.deepcopy(df)
    num_rows = df.shape[0]
    num_cols = df.shape[1]
    
    if adjust == 'text':
        columns = df.columns
        if num_cols > 2:
            logging.warning("Too many columns, Using shrink")
            return df_to_markdown(df, adjust='shrink')
        
        if num_cols == 1:
            text_df = f"List of items *{columns[0]}*\n"
            for i, row in df.iterrows():
                text_df += f"- {row[columns[0]]}"

                # Add new line if not the last row
                if i < num_rows:
                    text_df += "\n"
            return text_df
        
        elif num_cols == 2:
            text_df = f"List of {columns[0]} with corresponding {columns[1]}\n"
            for i, row in df.iterrows():
                text_df += f"- {row[columns[0]]}: {row[columns[1]]}"

                # Add new line if not the last row
                if i < num_rows:
                    text_df += "\n"
            return text_df
        
    if adjust == 'shrink':
        
        columns = df.columns
        text_df = "| "
        for col in columns:
            text_df += f"{col} | "
        text_df = text_df[:-1] + "\n|"
        for col in columns:
            text_df += " --- |"
        text_df += "\n"

        for i, row in df.iterrows():
            text_df += "| "
            for r in row:
                text_df += f"{r} | "

            # Add new line if not the last row
            if i < num_rows:
                text_df += "\n"
        return text_df
    
    else:
        logging.warning("Adjust not supported")
        markdown = df.to_markdown(index=False)
    
    return markdown


def get_sql_code_from_text(response):
    codes = get_code_from_text_response(response)
    
    sql_code = []
    for code in codes:
        if code['language'] == 'sql':
            codes = code['code'].split(";")
            for content in codes:
                # clean the content
                if content.strip() != "":
                    sql_code.append(content)
    print(f"Extracted {len(sql_code)} SQL code snippets from response.")
    return sql_code


def is_sql_full_of_comments(sql_text):
    lines = sql_text.strip().splitlines()
    comment_lines = 0
    total_lines = len(lines)
    in_multiline_comment = False

    for line in lines:
        stripped_line = line.strip()
        
        # Check if it's a single-line comment or empty line
        if stripped_line.startswith('--') or not stripped_line:
            comment_lines += 1
            continue
        
        # Check for multi-line comments
        if stripped_line.startswith('/*'):
            in_multiline_comment = True
            comment_lines += 1
            # If it ends on the same line
            if stripped_line.endswith('*/'):
                in_multiline_comment = False
            continue
        
        if in_multiline_comment:
            comment_lines += 1
            if stripped_line.endswith('*/'):
                in_multiline_comment = False
            continue

    # Check if comment lines are the majority of lines
    return comment_lines >= total_lines  


def TIR_reasoning(response, db, verbose=False, prefix=""):
    
    execution_error = []
    execution_table = []
    
    sql_code = get_sql_code_from_text(response)
            
    for i, code in enumerate(sql_code):    
        if verbose:    
            print(f"SQL Code {i+1}: \n{code}")
        
        if not is_sql_full_of_comments(code): 
              
            table = db.query(code)
            
            # If it see an error in the SQL code
            if isinstance(table, str):
                execution_error.append(f"{prefix} SQL {i+1} Error: " + table)
                
            else:
                execution_table.append(table)
    
    
    return execution_error, execution_table