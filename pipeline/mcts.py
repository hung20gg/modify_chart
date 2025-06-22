import os 
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))
from uuid import uuid4

from pipeline.execution import Env
from pipeline.module import Module
from PIL import Image

from typing import Optional, List, Dict, Any, Union, Generator, Tuple
from pydantic import BaseModel, Field, ConfigDict
from PIL import Image
import logging
from collections import deque
import numpy as np
import copy
import random

SEARCH_POLICY = 'sampling'
MAX_CHILD = 2


class ReasoningNode(BaseModel):

    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the reasoning node")
    code: str = Field(..., description="Content of the reasoning node")
    critique: str = Field(..., description="Critique of the reasoning node")
    image: Union[str, Image.Image] = Field(None, description="Image associated with the reasoning node")
    parent: Optional['ReasoningNode'] = Field(None, description="Parent node in the reasoning tree")
    children: List['ReasoningNode'] = Field(default_factory=list, description="List of child nodes in the reasoning tree")
    rank: int = Field(0, description="Rank of the node in the reasoning tree")
    reward: List[float] = Field(default_factory=list, description="List of rewards associated with the node")
    Q: float = Field(0.0, description="Q value of the node")
    N: int = Field(0, description="Number of visits to the node")

        
    def add_child(self, node) -> None:
        node.rank = self.rank + 1
        self.children.append(node)
        node.parent = self
        
    def add_critique(self, critique:str) -> None:
        self.critique = critique
        
    def add_reward(self, reward: float):
        self.reward.append(reward)
        
        # New Q value score
        avg_reward = np.mean(self.reward)
        min_reward = np.min(self.reward)
        
        self.Q = (min_reward + avg_reward)/2
        
    


class MCTSPipeline(BaseModel):
    """
    Monte Carlo Tree Search (MCTS) pipeline for executing modules in a sequence.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    module: Module = Field(..., description="List of modules to execute in the pipeline")
    env: Env = Field(default_factory=Env, description="Environment for executing the modules")
    tag: str = Field(default='', description="Tag for the run")
    max_iterations: int = Field(default=5, description="Maximum number of iterations to run the pipeline")
    debug: bool = Field(default=False, description="Enable debug mode for the pipeline")
    run_name: str = Field(default=str(uuid4()), description="Name of the run")

    def __init__(self, **data):
        """
        Initialize the MCTS pipeline with the given configuration.
        """
        super().__init__(**data)
        
        if self.debug:
            logging.info(f"Initialized MCTSPipeline with run_name: {self.run_name} and tag: {self.tag}")
            self.module.debug = True

    @staticmethod
    def concatenate_critiques(critique_list: Dict[str, str]) -> str:
        """
        Concatenate a list of critiques into a single string.
        """
        return "\n".join([f"### {key}: \n{value}\n\n" for key, value in critique_list.items()])

    # Check the UCB value
    @staticmethod
    def UCB(node: ReasoningNode, c = 1, epsilon = 1e-6) -> float: # AlphaGo UCB
        if node.parent is not None:
            ucb = node.Q + c * np.sqrt(2 * np.log(node.parent.N +1) / (node.N + epsilon))
            return ucb
        else:
            return 10000
        

    @staticmethod
    def backward_Q_value(node: ReasoningNode) -> None:
        # Backward update the Q value
        parent = node.parent
        while parent is not None:
            parent.N += 1
            maxQ = max([child.Q for child in parent.children])
            
            # Check the formula 
            parent.Q = (parent.Q + maxQ)/2
            parent = parent.parent


    @staticmethod
    def fully_expanded(node: ReasoningNode, max_child: int = MAX_CHILD) -> bool:
    
        flag = False
        # If the children of the node is greater than max child
        if len(node.children) >= max_child:
            flag |= True
            
        # If Q value of child > current node
        for child in node.children:
            if child.Q > node.Q:
                flag |= True 
                break
            
        return flag
        
    def select_node(self, node: ReasoningNode, search_policy: str = 'sampling') -> ReasoningNode:
        
        # Get the root node
        while node.parent is not None:
            node = node.parent
            
        # Select the candidate note for search
        candidate = []
        bfs_node = deque([node])
        
        while bfs_node:
            current_node = bfs_node.popleft()
            if not self.fully_expanded(current_node):
                candidate.append(current_node)
            bfs_node.extend(current_node.children)
            
        if not candidate:
            return node 
        
        if search_policy.lower() == 'greedy': # Get node with highest UCB score
            return max(candidate, key= lambda x: self.UCB(x))
        
        elif search_policy.lower() == 'sampling':
            ucbs = [self.UCB(x) for x in candidate]
            choice = random.choices(
                range(len(candidate)), weights=ucbs, k=1
            )[0]
            return candidate[choice]
        else:
            raise ValueError("Invalid Search Policy")
        

    def act(self, request: str, image: Union[str, Image.Image] = None) -> Dict[str, Any]:


        prev_state_critique = None
        prev_state_code = None

        initial_result = self.module.act(
            env=self.env,
            request=request,
            image=image,
            prev_state_code=prev_state_code,
            prev_state_critique=prev_state_critique,
            run_name=self.run_name,
            tag=f"{self.tag}_iteration_1"
        )

        critique = self.concatenate_critiques({
            'Vision critique': initial_result['critic_result']['vision_critic']['critique'],
            'Text critique': initial_result['critic_result']['text_critic']['critique']
        })
        code = initial_result['actor_result']['action']
        score = initial_result['critic_result']['score']
        output_image = initial_result['output_image']

        initial_node = ReasoningNode(
            code=code,
            critique=critique,
            rank=0,
            Q=score,
            N=1,
            image=output_image
        )

        number_of_4 = score >= 4

        for _ in range(self.max_iterations):

            # Select node based on UCB
            selected_node = self.select_node(initial_node, search_policy=SEARCH_POLICY)


            if self.debug:
                logging.info(f"Selected Node: {selected_node.id}, Q: {selected_node.Q}, N: {selected_node.N}")

            # Act on the selected node
            result = self.module.act(
                env=self.env,
                request=request,
                image=image,
                prev_state_code=selected_node.code,
                prev_state_critique=selected_node.critique,
                run_name=self.run_name,
                tag=f"{self.tag}_iteration_{selected_node.rank + 1}"
            )

            critique = self.concatenate_critiques({
                'Vision critique': result['critic_result']['vision_critic']['critique'],
                'Text critique': result['critic_result']['text_critic']['critique']
            })
            code = result['actor_result']['action']
            score = result['critic_result']['score']

            if score == 0:
                if self.debug:
                    logging.info(f"Score is 0, skipping node: {selected_node.id}")
                break
            output_image = result['output_image']

            # Create a new node
            new_node = ReasoningNode(
                code=code,
                critique=critique,
                rank=selected_node.rank + 1,
                Q=score,
                N=1,
                image=output_image
            )

            # Add the new node to the selected node
            selected_node.add_child(new_node)

            # Update the Q value of the selected node
            selected_node.add_reward(score)
            
            # Backward update the Q value of the parent nodes
            self.backward_Q_value(selected_node)

            if self.debug:
                logging.info(f"New Node: {new_node.id}, Q: {new_node.Q}, N: {new_node.N}")
                logging.info(f"Selected Node after update: {selected_node.id}, Q: {selected_node.Q}, N: {selected_node.N}")
            if score >= 4:
                number_of_4 += 1
                if self.debug:
                    logging.info(f"Score >= 4: {score}, Number of 4s: {number_of_4}")
                if number_of_4 >= 3:
                    break

        # return the final result
        best_node = None
        best_q = -float('inf')
        stack = deque([initial_node])

        while stack:
            node = stack.pop()
            if node.Q > best_q:
                best_q = node.Q
                best_node = node
            for child in node.children:
                stack.append(child)

        return [
            {
                'output_image': best_node.image,
                'code': best_node.code,
                'score': best_node.Q,
            }
        ]
