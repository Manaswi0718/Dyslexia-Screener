"""
Deploy Word Wizards to a Hugging Face Space (Docker).

Usage:  python tools/deploy_hf.py <your-hf-username>
It creates the Space (if needed) and uploads the project. Run it again any time to update the live app.
"""
import getpass, os, sys
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parent.parent
if len(sys.argv) < 2:
    sys.exit("Usage: python tools/deploy_hf.py <your-hf-username>")
repo_id = f"{sys.argv[1]}/word-wizards"

token = os.environ.get("HF_TOKEN", "").strip()
if not token:
    print("Tip: if pasting does not work, right-click in the window, or run:  set HF_TOKEN=hf_...  first.")
    token = getpass.getpass("Paste your Hugging Face access token (input is hidden): ").strip()
api = HfApi(token=token)
print("Logged in as:", api.whoami()["name"])

api.create_repo(repo_id, repo_type="space", space_sdk="docker", exist_ok=True)
print("Uploading… (first time takes 1-2 minutes)")
api.upload_folder(
    folder_path=str(ROOT), repo_id=repo_id, repo_type="space",
    ignore_patterns=["venv/*", "data/*", ".git/*", "**/__pycache__/*", "*.pyc", ".env", "docs/*"],
    commit_message="Deploy Word Wizards",
)
print(f"\nDone! Build logs + app:  https://huggingface.co/spaces/{repo_id}")
print(f"Direct app link (after the build finishes):  https://{repo_id.replace('/', '-').lower()}.hf.space")
