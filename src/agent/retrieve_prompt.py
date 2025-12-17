import os
import json
from langfuse import get_client
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any, List

# --- Configuration and Initialization ---
# Load environment variables (including LANGFUSE_* and PROMPT_PATH)
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Initialize Langfuse client (should be done once)
langfuse = get_client()


def retrieve_prompt(name: str, **variables) -> str | None:
    """
    Retrieves a single prompt template from Langfuse, formats it with variables, 
    and returns the final string.
    (Kept separate as it serves a different purpose than the bulk export)
    """
    print("Retrieving Langfuse prompt:", name)
    
    try:
        prompt_object = langfuse.get_prompt(name, label="latest")
        prompt_template_string = prompt_object.prompt
    except Exception as e:
        print(f"Error retrieving prompt '{name}' from Langfuse: {e}")
        return None
    
    # Format the template with dynamic variables
    return prompt_template_string.format(**variables)


def fetch_prompt_names(client) -> List[str]:
    """
    Retrieves only the list of all prompt names (metadata) from Langfuse API.
    """
    try:
        print("Fetching prompt names list via client.api.prompts.list()...")
        prompt_list_response = client.api.prompts.list(limit=100) 
        
    except AttributeError:
        print("Error: The attribute 'api.prompts.list' is not available. Please check your Langfuse SDK version.")
        return []
    except Exception as e:
        print(f"Error connecting to Langfuse to list prompts: {e}")
        return []

    # The result data is usually under the 'data' field
    return [p.name for p in prompt_list_response.data]


def fetch_single_prompt_content(client, name: str) -> Dict[str, Any] | None:
    """
    Fetches the full content (template, config, version) for a single prompt name.
    """
    try:
        prompt_object = client.get_prompt(name, label="latest")
        
        return {
            "name": name,
            "version": prompt_object.version,
            "prompt": prompt_object.prompt
        }
    except Exception as e:
        print(f"  -> Error retrieving content for '{name}': {e}")
        return None

def retrieve_json_path(name: str):
    output_directory_str = os.getenv("PROMPT_PATH")
    output_dir = Path(output_directory_str)

    file_name = ""

    if name.lower().startswith("evaluator"):
        file_name = "evaluator.json"
    else:
        file_name = "production.json"

    return Path(output_dir) / Path(file_name)

def read_file(file_path: Path):
    data = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Erreur de lecture : {e}")

    return data

def write_to_json_file(prompt_name: str, prompt_data: Dict[str, Any]):
    prompt_version = prompt_data.get("version")
    file_path = retrieve_json_path(prompt_name)
    data = {}

    # 1. Préparation des données (Lecture ou initialisation)
    if file_path.exists():
        data = read_file(file_path)
        
        if prompt_name not in data:
            print(f"-> Adding new prompt {prompt_name} to existing file {file_path.name}.")
            data[prompt_name] = prompt_data
        
        
        elif data[prompt_name].get("version", 0) < int(prompt_version): 
            print(f"-> Updating {prompt_name} to v{prompt_version}")
            data[prompt_name] = prompt_data
        else:
            print(f"-> {prompt_name} is already up to date")
            return 

    else: 
        print(f"-> Creating file {file_path.name} and adding {prompt_name}")
        data[prompt_name] = prompt_data

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            print(f"Writing to {file_path.name}...")
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erreur d'écriture dans {file_path.name} : {e}")

if __name__ == "__main__":
  
  # 1. Fetch all prompt names
  prompt_names = fetch_prompt_names(langfuse)
  
  if not prompt_names:
    print("\nNo prompt names retrieved from Langfuse. Exiting.")
    langfuse.flush()
    exit()

  for name in prompt_names:
    prompt_data = fetch_single_prompt_content(langfuse, name)
    
    if prompt_data:
      write_to_json_file(name, prompt_data)
    
  langfuse.flush()