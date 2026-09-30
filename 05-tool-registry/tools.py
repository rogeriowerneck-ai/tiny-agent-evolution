import platform
import socket
import sys


def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "python_version": sys.version.split()[0],
        "architecture": platform.machine(),
        "system": platform.system(),
    }


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": (
                "Get information about the system where the application "
                "is currently running."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }
]


TOOL_REGISTRY = {
    "get_system_info": get_system_info,
}
