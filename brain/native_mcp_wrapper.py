"""Diagnostic wrapper: logs MCP server startup/exit to a file."""
import sys, os, time, json, traceback
from pathlib import Path

LOG = Path(os.environ.get("AITP_MCP_STARTUP_LOG", str(Path(__file__).with_name("_mcp_startup.log"))))

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} [{os.getpid()}] {msg}\n")

log(f"wrapper started, python={sys.executable}, cwd={os.getcwd()}")
log(f"args={sys.argv}")

try:
    log("importing native_mcp...")
    # Add brain/ parent to path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    # Check if warnings are being filtered before we go further
    import warnings
    log(f"warnings filters before: {[str(f) for f in warnings.filters[:3]]}")

    # Run the actual main
    from brain.native_mcp import main
    log("imports complete, entering main loop")
    main()
except SystemExit as e:
    log(f"SystemExit: {e}")
except Exception as e:
    log(f"FATAL: {type(e).__name__}: {e}")
    log(traceback.format_exc())
finally:
    log("process exiting")
