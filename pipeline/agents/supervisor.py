from langchain_core.tools import Tool
from pipeline.agents import agent
import yaml
from pipeline.agents import agent_factory
import os

sw_prompt = "Tu es un Superviseur d'Agents. Ton rôle est de rediriger la requête de l'utilisateur vers le meilleur agent spécialisé disponible. " \
"NE RÉPONDS JAMAIS TOI-MÊME. Si aucun outil ne convient, déclare ton incapacité. Si plusieurs questions sont posées en même temps, réponds y de manière séquentielle, l'une à la suite de l'autre de manière à répondre au plus grand nombre de questions possible"

class Supervisor(agent.Agent):
    
    def __init__(self, llm: str, tools: list):
        super().__init__(llm, tools, sw_prompt)
        print("Supervisor Agent ready !")

    @classmethod
    def create(cls, llm: str):
      """
      Factory Method Synchrone : Load dynamically all specialized agents.
      """
      supervisor_tools = []
      
      try:
          with open(os.getenv("AGENTS_PATH"), 'r') as f:
              config = yaml.safe_load(f)['active_agents']
      except FileNotFoundError:
          print("Error: The current file does not exist. None agent loaded !.")
          config = []

      for agent_config in config:
        # create an new instance for every agent defined in agents.yaml
        agent_instance = agent_factory.AgentFactory.create_agent_instance(llm, agent_config)
          
        supervisor_tools.append(
            Tool(
                name=agent_config['name'],
                func=agent_instance.invoke, 
                coroutine=agent_instance.invoke,
                description=agent_config['description'] 
            )
        )
          
      return cls(llm, supervisor_tools)