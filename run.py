import sys
import os
import importlib.util
import subprocess
from pathlib import Path

def check_virtual_env():
    """Check if running in a virtual environment and exit if not."""
    
    # Check for the presence of a virtual environment
    is_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if not is_venv:
        print("ERROR: This script must be run in a virtual environment.")
        print("Please activate a virtual environment and try again.")
        sys.exit(1)
    
    print("Virtual environment detected. Continuing...")

def get_venv_path():
    """Get the path of the current virtual environment."""
    if hasattr(sys, 'real_prefix'):
        return Path(sys.real_prefix)
    elif hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
        return Path(sys.prefix)
    else:
        return None

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['pytz', 'suntime', 'PyQt5']
    missing_packages = []
    
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"ERROR: Missing required dependencies: {', '.join(missing_packages)}")
        print("Please install them using pip:")
        print(f"pip install {' '.join(missing_packages)}")
        sys.exit(1)
    
    print("All required dependencies found.")

def get_pyqt_lib_path():
    """Get the PyQt5 library path."""
    venv_path = get_venv_path()
    if venv_path:
        # Determine Python version
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        
        # Construct PyQt5 lib path
        pyqt_lib_path = venv_path / "lib" / f"python{py_version}" / "site-packages" / "PyQt5" / "Qt5" / "lib"
        
        if pyqt_lib_path.exists():
            return pyqt_lib_path
        else:
            print(f"Warning: PyQt5 lib directory not found at {pyqt_lib_path}")
    return None

def run_celesun():
    """Run the CeleSun application with proper environment setup."""
    app_path = Path.cwd() / "celesun.py"
    
    if not app_path.exists():
        print(f"ERROR: CeleSun application not found at {app_path}")
        sys.exit(1)
    
    # Only set up library path for Linux
    if os.name == 'posix' and sys.platform != 'darwin':
        pyqt_lib_path = get_pyqt_lib_path()
        if pyqt_lib_path:
            print(f"Setting up LD_LIBRARY_PATH to include: {pyqt_lib_path}")
            
            # Create a new environment with the updated LD_LIBRARY_PATH
            env = os.environ.copy()
            current_ld_path = env.get('LD_LIBRARY_PATH', '')
            env['LD_LIBRARY_PATH'] = f"{pyqt_lib_path}:{current_ld_path}" if current_ld_path else str(pyqt_lib_path)
            
            # Get the Python interpreter path
            python_exe = sys.executable
            
            print(f"Starting CeleSun application using: {python_exe} {app_path}")
            
            # Launch the application as a subprocess with the modified environment
            try:
                process = subprocess.Popen([python_exe, str(app_path)], env=env)
                process.wait()  # Wait for the application to finish
                if process.returncode != 0:
                    print(f"Application exited with code {process.returncode}")
            except Exception as e:
                print(f"Error running CeleSun: {e}")
                sys.exit(1)
        else:
            print("Could not find PyQt5 lib path. Running without environment modification.")
            run_without_env_mod(app_path)
    else:
        # Non-Linux platforms
        run_without_env_mod(app_path)

def run_without_env_mod(app_path):
    """Run the application without environment modifications."""
    python_exe = sys.executable
    print(f"Starting CeleSun application using: {python_exe} {app_path}")
    try:
        process = subprocess.Popen([python_exe, str(app_path)])
        process.wait()
        if process.returncode != 0:
            print(f"Application exited with code {process.returncode}")
    except Exception as e:
        print(f"Error running CeleSun: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_virtual_env()
    
    # Get and display virtual environment path
    venv_path = get_venv_path()
    print(f"Virtual environment path: {venv_path}")
    print(f"Current working directory: {Path.cwd()}")
    
    # Check dependencies
    check_dependencies()
    
    # Run the CeleSun application (with environment setup)
    run_celesun()