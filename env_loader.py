"""
Environment variable loader for ClassicsOnScreen project.
This module loads environment variables from a secure location outside the project directory.
"""

import os
import sys
import platform
from pathlib import Path

def convert_value(name: str, value) -> str:
    """
    Convert environment variable values to the appropriate type based on the variable name.
    """
    # Boolean variables
    if name in {'DEBUG', 'EMAIL_USE_TLS'}:
        # Convert Python boolean or string to string 'True' or 'False'
        return str(str(value).lower() == 'true')
    
    # All other variables should be strings
    return str(value)

def parse_env_file(file_path: Path) -> dict:
    """
    Parse an environment file that uses KEY=value format.
    """
    env_vars = {}
    try:
        with open(file_path) as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                # Split on first = only
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error parsing environment file: {e}")
    return env_vars

def load_environment_variables() -> bool:
    """
    Load environment variables from a secure location outside the project directory.
    Works in both development and production environments.
    """
    # Define the environment file path
    env_path = Path('/etc/classicsonscreen/env.py')
    
    # Check if the environment file exists
    if not env_path.exists():
        print(f"Warning: Environment file not found at {env_path}")
        return False
    
    try:
        # First try to parse as KEY=value format
        env_vars = parse_env_file(env_path)
        
        if not env_vars:
            # If that fails, try to load as a Python module
            sys.path.insert(0, str(env_path.parent))
            try:
                env_module = __import__(env_path.stem)
                # Get all variables that don't start with _ and aren't callable
                env_vars = {
                    name: getattr(env_module, name)
                    for name in dir(env_module)
                    if not name.startswith('_') and not callable(getattr(env_module, name))
                }
            except ImportError:
                print("Failed to load environment file in both formats")
                return False
            finally:
                # Clean up sys.path
                if str(env_path.parent) in sys.path:
                    sys.path.remove(str(env_path.parent))
        
        # Update environment with converted values
        for name, value in env_vars.items():
            os.environ[name] = convert_value(name, value)
        
        print(f"Loaded environment variables from {env_path}")
        return True
        
    except Exception as e:
        print(f"Error loading environment variables: {e}")
        return False 