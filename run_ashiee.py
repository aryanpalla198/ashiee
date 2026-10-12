"""
Direct Convenience Launcher for Ashiee.
Run with:
  py run_ashiee.py              -> Starts the interactive terminal CLI
  py run_ashiee.py serve        -> Starts the Desktop Canvas web server
  py run_ashiee.py run "..."    -> Executes a single autonomous command
"""

import sys
from pathlib import Path

# Add current repository to sys.path
root_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(root_dir))

from ashiee.cli.main import cli

if __name__ == "__main__":
    cli()
