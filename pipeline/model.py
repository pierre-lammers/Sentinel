import os
import warnings
from langchain.chat_models import init_chat_model

warnings.filterwarnings("ignore", message=".*Google will stop supporting.*")


#os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

llm_model = "gemini-2.5-flash"
llm = init_chat_model(llm_model, model_provider="google_genai")


def get_llm():
    """Retourne l'instance du modèle."""
    return llm

def invoke(prompt: str) -> str:
    """Envoie une question au modèle."""
    if llm is None:
        return "Erreur : Le modèle n'a pas été initialisé. Lancez create_model d'abord."
    
    response = llm.invoke(prompt)
    return response.content
