import os
import json
from langfuse import get_client
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any, List

# --- Configuration and Initialization ---
# Load environment variables (including LANGFUSE_* and PROMPT_PATH)
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Initialize Langfuse client
langfuse = get_client()

PROMPT_TYPES: List[str] = ["evaluator", "production"]
PROMPT_FILES: Dict[str, str] = {p: f"{p}.json" for p in PROMPT_TYPES}


def retrieve_prompt(name: str, **variables) -> str | None:
    """
    Retrieves a single prompt template from Langfuse, formats it with variables, 
    and returns the final string.
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
    Retrieves the list of all prompt names from Langfuse API.
    """
    try:
        print("Fetching prompt names list via client.api.prompts.list()...")
        prompt_list_response = client.api.prompts.list(limit=100) 
        return [p.name for p in prompt_list_response.data]
    except AttributeError:
        print("Error: The attribute 'api.prompts.list' is not available. Please check your Langfuse SDK version.")
        return []
    except Exception as e:
        print(f"Error connecting to Langfuse to list prompts: {e}")
        return []


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


def retrieve_json_path(name: str) -> Path:
    """
    Determines the target file path based on the prompt name.
    """
    output_directory_str = os.getenv("PROMPT_PATH", ".")
    output_dir = Path(output_directory_str)

    prefix = name.lower().split(" - ")[0]

    return output_dir / PROMPT_FILES[prefix]


def read_json_file(file_path: Path) -> Dict[str, Any]:
    """
    Reads and parses a JSON file.
    """
    data = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Read error: {e}")
    return data


def write_to_json_file(prompt_name: str, prompt_data: Dict[str, Any]):
    """
    Updates or creates a JSON file with the new prompt data if the version is newer.
    """
    prompt_version = prompt_data.get("version")
    short_name = prompt_name.split(" - ")[-1]

    prompt_data["name"] = short_name

    file_path = retrieve_json_path(prompt_name)
    data = {}

    # 1. Data Preparation (Read or initialize)
    if file_path.exists():
        data = read_json_file(file_path)
        
        # If the prompt doesn't exist in the file
        if short_name not in data:
            print(f"-> Adding new prompt {short_name} to existing file {file_path.name}.")
            data[short_name] = prompt_data
        
        # If the prompt is not up to date, update it
        elif data[short_name].get("version", 0) < int(prompt_version): 
            print(f"-> Updating {short_name} to v{prompt_version}")
            data[short_name] = prompt_data
        else:
            print(f"-> {short_name} is already up to date, no action taken.")
            return 

    else: 
        print(f"-> Creating file {file_path.name} and adding {short_name}")
        data[short_name] = prompt_data

    # 2. Disk Write
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            print(f"Writing to {file_path.name}...")
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Write error in {file_path.name}: {e}")


def cleanup_local_json(file: Path, remote_names: List[str]):
    """
    Removes prompts from local JSON files that are no longer present on Langfuse.
    """
    data = read_json_file(file)
    prompts_to_remove = []

    # Create a new list with all names in lowercase
    remote_names_lower = [n.lower() for n in remote_names]

    # Retrieve old prompt to remove from JSON file
    if len(data) > len(remote_names):
        for name in data: 
            if name.lower() not in remote_names_lower:
                print(f"🗑️ Prompt '{name}' no longer exists on Langfuse. Removed from {file.name}")
                prompts_to_remove.append(name)

        for prompt in prompts_to_remove:
            del data[prompt]
        
        try: 
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Successfully cleaned up {file.name}")
        except Exception as e:
            print(f"Write error in {file.name}: {e}")
            
    else:
        print("No need to clean up")


if __name__ == "__main__":
    # 1. Fetch all prompt names from Langfuse
    prompt_names = fetch_prompt_names(langfuse)
    prompt_filtered: Dict[str, List[str]] = {p_type: [] for p_type in PROMPT_TYPES}
    
    if not prompt_names:
        print("\nNo prompt names retrieved from Langfuse. Exiting.")
        langfuse.flush()
        exit()

    print(f"\nFound {len(prompt_names)} prompt(s) on Langfuse.")

    # Filter the prompts by their type 
    for prompt in prompt_names:
        prefix, suffix = prompt.lower().split(" - ")
        if prefix in prompt_filtered:
            prompt_filtered[prefix].append(suffix)

    # 2. Process each prompt
    for name in prompt_names:
        prompt_content = fetch_single_prompt_content(langfuse, name)
        if prompt_content:
            write_to_json_file(name, prompt_content)

    # 3. Cleanup local JSON files
    output_directory_str = os.getenv("PROMPT_PATH", ".")
    for file in Path(output_directory_str).glob("*.json"):
        cleanup_local_json(file, prompt_filtered[file.name.split(".")[0]])

    
    langfuse.flush()
    print("\n✅ Sync and cleanup completed successfully.")