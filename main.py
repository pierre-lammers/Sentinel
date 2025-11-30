from dotenv import load_dotenv

load_dotenv()

from pipeline import model as md
from pipeline.agents import supervisor as sp

"""
.env : 

you must defined in your .env 

- GOOGLE_API_KEY 
- SRS_PATH (the pdf path)
- TESTS_PATH (the tests path)
- AGENTS_PATH (the yaml path)

"""

# Get the llm model
llm = md.get_llm()

# Create the supervisor instance
supervisor = sp.Supervisor.create(llm) 

# invoke him !
#response = supervisor.invoke("Give me the test id that deals with MSAW alerts genration when track altitude is below the Minimum Safe Altitude")
response = supervisor.invoke("Analyse the coverage of SKYRADAR-MSAW-025 !")
print(response)