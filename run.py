#!/usr/bin/env python3
"""
Run the kort.ing development server.

Usage:
    python run.py [--host HOST] [--port PORT] [--reload]

Examples:
    python run.py                    # Run on localhost:8000
    python run.py --port 3000        # Run on localhost:3000
    python run.py --host 0.0.0.0     # Allow external connections
"""

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run the kort.ing server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    print(f"""
    +---------------------------------------------------+
    |                                                   |
    |     kort.ing - Nederlandse Deals                  |
    |                                                   |
    |     Server: http://{args.host}:{args.port:<5}                 |
    |     Reload: {'enabled' if args.reload else 'disabled':<8}                         |
    |                                                   |
    |     Press CTRL+C to stop                          |
    |                                                   |
    +---------------------------------------------------+
    """)

    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
