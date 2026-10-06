from datetime import datetime, timezone, timedelta
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


def get_cpu_temperature():
    thermal_file = "/sys/class/thermal/thermal_zone0/temp"

    try:
        with open(thermal_file) as file:
            temperature = int(file.read().strip()) / 1000

        return {
            "temperature_celsius": temperature,
        }
    except Exception as error:
        return {
            "error": str(error),
        }


def get_current_date_time():
    brasilia_timezone = timezone(timedelta(hours=-3))
    now = datetime.now(brasilia_timezone)

    return {
        "datetime": now.isoformat(),
        "timezone": "UTC-03:00",
    }


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": (
                "Get information about the system where the application "
                "is currently running, including hostname, Python version, "
                "architecture, and operating system."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cpu_temperature",
            "description": (
                "Get the current CPU temperature of the machine where "
                "the application is running."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_date_time",
            "description": (
                "Get the current date and time in the application's "
                "local timezone."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


TOOL_REGISTRY = {
    "get_system_info": get_system_info,
    "get_cpu_temperature": get_cpu_temperature,
    "get_current_date_time": get_current_date_time,
}
