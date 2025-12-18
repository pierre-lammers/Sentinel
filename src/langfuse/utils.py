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

def retrieve_prompt(prompt_name: str, **variables) -> str | None:
    """
    Retrieves a prompt from the local JSON file and formats its placeholders.
    """

    # 1. Extract the short name (e.g., "Coverage") to find the key in JSON
    short_name = prompt_name.split(" - ")[-1]
    
    # 2. Locate the file and read the data
    file_path = retrieve_json_path(prompt_name)
    all_prompts = read_json_file(file_path)
    
    # 3. Check if the prompt exists in our local dictionary
    if short_name not in all_prompts:
        print(f"Error: Prompt '{short_name}' not found in {file_path.name}")
        return None
    
    # 4. Get the raw template string
    prompt_template = all_prompts[short_name].get("prompt", "")

    try:
        # 5. Replace {key} with value from **variables
        # .format(**variables) automatically maps {"user": "Alice"} to {user}
        return prompt_template.format(**variables)
    except KeyError as e:
        print(f"Error: Missing variable {e} for prompt '{short_name}'")
        return prompt_template # Returns unformatted if a variable is missing
    except Exception as e:
        print(f"Formatting error: {e}")
        return None

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
                print(f"\n🗑️ Prompt '{name}' no longer exists on Langfuse. Removed from {file.name}")
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

# --- Main Execution ---

def sync_prompts_from_langfuse():       
    prompt_names = fetch_prompt_names(langfuse)
    prompt_filtered: Dict[str, List[str]] = {p_type: [] for p_type in PROMPT_TYPES}
    
    if not prompt_names:
        print("\nNo prompt names retrieved from Langfuse. Exiting.")
        langfuse.flush()
        return

    print(f"\nFound {len(prompt_names)} prompt(s) on Langfuse.")

    for prompt in prompt_names:
        parts = prompt.lower().split(" - ")
        if len(parts) >= 2:
            prefix, suffix = parts[0], parts[1]
            if prefix in prompt_filtered:
                prompt_filtered[prefix].append(suffix)
        else:
            print(f"⚠️ Skipping prompt with invalid format: {prompt}")

    for name in prompt_names:
        prompt_content = fetch_single_prompt_content(langfuse, name)
        if prompt_content:
            write_to_json_file(name, prompt_content)

    output_dir = Path(os.getenv("PROMPT_PATH", "."))
    for p_type in PROMPT_TYPES:
        file_path = output_dir / PROMPT_FILES[p_type]
        if file_path.exists():
            cleanup_local_json(file_path, prompt_filtered[p_type])

    langfuse.flush()
    print("\n✅ Sync and cleanup completed successfully.")

def test_retrieve_prompt():
    variables = {
        "output_str": "expert",
        "expected_str": "Dune 2",
    }
    pt = retrieve_prompt("Evaluator - Coverage", **variables)

    print(pt) 

if __name__ == "__main__":
    # Synchronize Langfuse prompts with local JSON files
    sync_prompts_from_langfuse()

    # Use to test the function
    #test_retrieve_prompt()