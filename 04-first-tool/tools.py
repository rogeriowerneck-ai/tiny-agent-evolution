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
