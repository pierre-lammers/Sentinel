import importlib
from langchain_core.tools import Tool
from pipeline.agents import agent
from pipeline.agents import tools


class AgentFactory:
    
    @staticmethod
    def _get_tools_by_names(tool_names: list) -> list:
        """ Retrieve every tools for every agent in agents.yaml, defined with decorator 'tool' """
        available_tools = []
        for name in tool_names:
            try:
                tool_function = getattr(tools, name)
                if isinstance(tool_function, Tool):
                    available_tools.append(tool_function)
            except AttributeError:
                print(f"Warning : Tool '{name}' not found in tools.py.")
        return available_tools

    @staticmethod
    def _get_function_by_name(func_name: str):
        """ Retrieve every dynamic prompt for every agent in agents.yaml, defined with decorator 'dynamic_prompt' """
        try:
            return getattr(tools, func_name)
        except AttributeError:
            raise ValueError(f"Warning : Function '{func_name}' not found in tools.py.")


    @classmethod
    def create_agent_instance(cls, llm: str, config: dict) -> agent.Agent:
        """
        Creates an instance of the base Agent synchronously, 
        managing static or dynamic prompts (middleware).

        :param llm: The Large Language Model instance.
        :param config: The agent's configuration dictionary (YAML).
        :return: An instance of the Agent class.
        """
        
        # 1. Load tools (if defined)
        tool_names = config.get("tools", [])
        agent_tools = cls._get_tools_by_names(tool_names) # retrieve tools
        
        # 2.Handle dynamic prompt
        sw_prompt = config.get("system_prompt")
        middleware = []
        
        middleware_func_name = config.get("middleware_func")
        
        if middleware_func_name:
            middleware_func = cls._get_function_by_name(middleware_func_name)
            middleware.append(middleware_func)
            sw_prompt = None # Le middleware prend le dessus sur le prompt statique
            print(f"-> Creating {config['name']} with middleware: {middleware_func_name}")
        else:
            print(f"-> Creating {config['name']} with {len(agent_tools)} tools (Static Prompt)...")

        
        # 3. Create and return the agent
        return agent.Agent(llm, agent_tools, sw_prompt, middleware=middleware)