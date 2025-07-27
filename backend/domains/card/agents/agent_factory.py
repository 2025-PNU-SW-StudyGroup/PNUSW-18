from typing import Callable, List
from langchain_core.language_models import BaseChatModel
from langchain.agents import create_react_agent



def init_saving_search_node(llm: BaseChatModel, tools: List[Callable], prompt: str):

    agent = create_react_agent(llm, tools, prompt=prompt)

    def node(state):

        
