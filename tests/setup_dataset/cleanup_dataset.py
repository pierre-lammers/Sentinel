"""Script to clean up Langfuse dataset by deleting items."""

import os

import requests  # type: ignore[import-untyped]
from dotenv import load_dotenv
from langfuse import Langfuse

# Load environment variables from .env file
load_dotenv()


def cleanup_dataset() -> None:
    """Delete all items from the requirements-evaluation dataset."""
    # Initialize Langfuse client
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )

    dataset_name = "requirements-evaluation"
    host = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    try:
        # Get existing dataset
        dataset = langfuse.get_dataset(dataset_name)
        print(f"Found existing dataset: {dataset_name}")

        # Get all items
        items = list(dataset.items)
        print(f"Found {len(items)} items in dataset")

        if not items:
            print("No items to delete")
            return

        # Delete each item using REST API
        for item in items:
            item_id = item.id
            url = f"{host}/api/public/dataset-items/{item_id}"

            response = requests.delete(
                url,
                auth=(public_key, secret_key),
                timeout=30,
            )

            if response.status_code == 200:
                print(f"Deleted item: {item_id}")
            else:
                print(
                    f"Failed to delete item {item_id}: {response.status_code} - {response.text}"
                )

        print("\nDataset cleanup completed!")
        print("Run: python tests/setup_dataset.py to recreate the dataset")

    except Exception as e:
        print(f"Error: {e}")
        print("\nAlternatively, delete the dataset manually from the Langfuse UI:")
        print(f"{host}/project/<your-project-id>/datasets")


if __name__ == "__main__":
    cleanup_dataset()
