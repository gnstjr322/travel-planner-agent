"""
Main entry point for the Travel Planner Multi-Agent System.
"""
import os
import subprocess
import sys


def run_streamlit():
    """Executes the Streamlit app using a subprocess."""
    # Ensure the script runs from the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    # Path to the streamlit app script
    streamlit_app_path = os.path.join("src", "ui", "streamlit_app.py")

    # Command to run streamlit with fixed port
    command = [
        sys.executable, "-m", "streamlit", "run", streamlit_app_path,
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ]

    try:
        print(f"Running command: {' '.join(command)}")
        print("http://localhost:8501")
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print("Error: 'streamlit' command not found.")
        print("Please make sure Streamlit is installed (`pip install streamlit`).")
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit app: {e}")


if __name__ == "__main__":
    run_streamlit()
