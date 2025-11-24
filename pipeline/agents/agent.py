from langchain.agents import create_agent
import warnings

warnings.filterwarnings("ignore", message=".*Google will stop supporting.*")

class Agent():
    def __init__(self, llm: str, tools, sw_prompt=None, middleware=None):

        if middleware is None:
            self.agent = create_agent(llm, tools=tools, system_prompt=sw_prompt)
        else:
           self.agent = create_agent(llm, tools=tools, system_prompt=sw_prompt, middleware=middleware)

    def invoke(self, query: str):
        if self.agent is None:
                return "Error: The agent is not initialized !"  
        response = self.agent.invoke({"messages": [("user", query)]})
        content = response["messages"][-1].content

        if isinstance(content, str):
            return content
        
        elif isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and "text" in content[0]:
                return content[0]["text"]
                
        return str(content)
    
    def get_agent(self):
        return self.agent