"""
Healthcare CRL Framework Command Line Interface
"""

import sys
from pathlib import Path

# Add src to path

from main import main as main_func

def main():
    """CLI entry point"""
    main_func()

if __name__ == "__main__":
    main()