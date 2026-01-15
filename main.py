import sys
import os

# Add NL repository to path so we can import its modules
# Use Unix-style path for WSL compatibility
paper_repo_path = '../designing-a-quantum-network-protocol-artifacts'
if not os.path.exists(paper_repo_path):
    print(f"ERROR: Paper Repo directory not found at {paper_repo_path}")
    print("Please update the path in main.py to point to your Paper Repo installation")
    sys.exit(1)

sys.path.insert(0, paper_repo_path)

# Add current directory to path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print(f"Python path configured:")
print(f"  Paper Repo: {paper_repo_path}")
print(f"  Current: {current_dir}")

# Import AFTER setting paths
from demo_metrics.demo_main import main

if __name__ == "__main__":
    main()