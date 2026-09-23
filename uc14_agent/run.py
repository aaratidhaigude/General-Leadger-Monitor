#!/usr/bin/env python3
"""
GL Anomaly Detection Agent — CLI entrypoint.

Usage:
    python run.py                          # batch run against the dataset
    python run.py --doc 5000001 --line 1   # single posting, verbose
    python run.py --ui                     # launch the FastAPI dashboard
"""
import sys
import os
import subprocess
import argparse

# Auto-detect and forward to .venv if user ran with global Python
current_dir = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(current_dir, ".venv", "Scripts", "python.exe")
if os.path.exists(venv_python) and os.path.abspath(sys.executable).lower() != os.path.abspath(venv_python).lower():
    sys.exit(subprocess.call([venv_python] + sys.argv))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the GL Anomaly Detection Agent.")
    parser.add_argument("--doc", help="Run a single GL document (requires --line)")
    parser.add_argument("--line", help="Line item within the document", default="1")
    parser.add_argument("--ui", action="store_true", help="Launch the FastAPI dashboard instead")
    args = parser.parse_args()

    if args.ui:
        from config.settings import API_PORT
        import os, subprocess
        port = int(os.environ.get("PORT", API_PORT))
        
        # Auto-kill any zombie process holding port 8000 on Windows so it ALWAYS starts fresh on 8000
        try:
            netstat_out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, stderr=subprocess.DEVNULL).decode()
            for line in netstat_out.strip().splitlines():
                if 'LISTENING' in line:
                    pid = line.strip().split()[-1]
                    if pid != '0' and int(pid) != os.getpid():
                        os.system(f"taskkill /F /PID {pid} >nul 2>&1")
        except Exception:
            pass

        print("\n" + "=" * 55)
        print("  Starting GL Anomaly Detection Dashboard Server")
        print(f"  URL: http://localhost:{port}")
        print("=" * 55)
        print("Loading libraries (takes 2-3 seconds)... please wait.\n")
        import uvicorn
        uvicorn.run("ui.app:app", host="0.0.0.0", port=port, reload=False)
        return 0


    from agent.gl_anomaly_agent import GLAnomalyAgent
    agent = GLAnomalyAgent()
    if args.doc:
        agent.run_posting(args.doc, args.line)
    else:
        results = agent.run_all()
        print(f"\nExcel and JSON written to results/ ({len(results)} postings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
