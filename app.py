"""
Main entry point for the Travel Planner Multi-Agent System.
"""
import os
import sys

from src.ui.streamlit_app import main

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


if __name__ == "__main__":
    main()
