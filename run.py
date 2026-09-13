"""
Run the Naukri AI Support Agent services.

Usage:
    python run.py
        Start both FastAPI and MCP servers.

    python run.py api
        Start only FastAPI.

    python run.py mcp
        Start only MCP.

FastAPI:
    http://127.0.0.1:8000
    http://127.0.0.1:8000/docs

MCP:
    http://127.0.0.1:8001/mcp
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent

API_HOST = "127.0.0.1"
API_PORT = "8000"

MCP_HOST = "127.0.0.1"
MCP_PORT = "8001"


def start_api() -> subprocess.Popen:
    """Start the FastAPI application using Uvicorn."""

    print(
        f"[START] FastAPI -> "
        f"http://{API_HOST}:{API_PORT}"
    )

    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "agent.api.app:app",
            "--host",
            API_HOST,
            "--port",
            API_PORT,
        ],
        cwd=ROOT,
    )


def start_mcp() -> subprocess.Popen:
    """Start the MCP server."""

    print(
        f"[START] MCP -> "
        f"http://{MCP_HOST}:{MCP_PORT}/mcp"
    )

    return subprocess.Popen(
        [
            sys.executable,
            "mcp_server.py",
            "--host",
            MCP_HOST,
            "--port",
            MCP_PORT,
        ],
        cwd=ROOT,
    )


def stop_process(process: subprocess.Popen | None) -> None:
    """Terminate a child process cleanly."""

    if process is None:
        return

    if process.poll() is None:
        process.terminate()

        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def run_api_only() -> None:
    process = start_api()

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n[STOP] Stopping FastAPI...")
    finally:
        stop_process(process)


def run_mcp_only() -> None:
    process = start_mcp()

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n[STOP] Stopping MCP...")
    finally:
        stop_process(process)


def run_both() -> None:
    api_process = None
    mcp_process = None

    try:
        print("=" * 70)
        print("NAUKRI AI SUPPORT AGENT")
        print("=" * 70)
        print()

        api_process = start_api()

        # Give Uvicorn a moment to bind its port before starting MCP.
        time.sleep(1)

        mcp_process = start_mcp()

        print()
        print("=" * 70)
        print("SERVICES RUNNING")
        print("=" * 70)
        print()
        print("FastAPI:")
        print(f"  http://{API_HOST}:{API_PORT}")
        print(f"  http://{API_HOST}:{API_PORT}/docs")
        print()
        print("MCP:")
        print(f"  http://{MCP_HOST}:{MCP_PORT}/mcp")
        print()
        print("Press Ctrl+C to stop both services.")
        print()

        while True:
            api_exit = api_process.poll()
            mcp_exit = mcp_process.poll()

            if api_exit is not None:
                print(
                    f"[ERROR] FastAPI stopped "
                    f"with exit code {api_exit}."
                )
                break

            if mcp_exit is not None:
                print(
                    f"[ERROR] MCP server stopped "
                    f"with exit code {mcp_exit}."
                )
                break

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[STOP] Shutting down services...")

    finally:
        stop_process(mcp_process)
        stop_process(api_process)

        print("[STOP] All services stopped.")


def main() -> None:
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "both"

    if mode == "api":
        run_api_only()
    elif mode == "mcp":
        run_mcp_only()
    elif mode == "both":
        run_both()
    else:
        print(
            "Usage:\n"
            "  python run.py        # FastAPI + MCP\n"
            "  python run.py api    # FastAPI only\n"
            "  python run.py mcp    # MCP only"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()