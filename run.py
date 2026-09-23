#!/usr/bin/env python3
import os
import sys
import subprocess

current_dir = os.path.dirname(os.path.abspath(__file__))
subfolder = os.path.join(current_dir, "uc14_agent")

if os.path.exists(subfolder):
    os.chdir(subfolder)
    sys.path.insert(0, subfolder)
    run_script = os.path.join(subfolder, "run.py")
    venv_python = os.path.join(subfolder, ".venv", "Scripts", "python.exe")
    python_bin = venv_python if os.path.exists(venv_python) else sys.executable
    sys.exit(subprocess.call([python_bin, run_script] + sys.argv[1:]))
else:
    print("Error: uc14_agent folder not found.")
