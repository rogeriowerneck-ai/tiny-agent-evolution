import json
import os
import urllib.request
from datetime import datetime, timezone

from tools import TOOL_DEFINITIONS, TOOL_REGISTRY


OLLAMA_URL = os.environ["OLLAMA_URL"]
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")


SYSTEM_PROMPT = """
You are Tiny Agent, a small tool-using AI agent running on a Nvidia Jetson Nano hardware.

Use the available tools when you need information about the current
environment, system state, CPU temperature, date, or time.

For information that can change over time, such as CPU temperature or the current
date and time, obtain a fresh observation when the user asks about the
current value.

Do not invent system information that can be obtained with a tool.

Use existing conversation context when it already contains sufficient
information to answer accurately.

You are a professional and formal language is prefered.

Simply provide an answer and only offer further assistance if really necessary.
""".strip()


def log_event(event, **data):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **data,
    }

    print(json.dumps(record))


def chat(messages):
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOL_DEFINITIONS,
        "stream": False,
        "think": False
    }

    log_event(
        "llm.request",
        model=MODEL,
        message_count=len(messages),
    )

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read().decode("utf-8"))

    assistant_message = result["message"]

    tool_calls = assistant_message.get("tool_calls", [])

    log_event(
        "llm.response",
        has_content=bool(assistant_message.get("content")),
        tool_call_count=len(tool_calls),
    )

    return assistant_message


def run_agent(messages):
    while True:
        assistant_message = chat(messages)

        tool_calls = assistant_message.get("tool_calls", [])

        if not tool_calls:
            response = assistant_message.get("content", "")

            messages.append(
                {
                    "role": "assistant",
                    "content": response,
                }
            )

            return response

        messages.append(assistant_message)

        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]

            log_event(
                "tool.call",
                tool=function_name,
            )

            function = TOOL_REGISTRY.get(function_name)

            if function is None:
                result = {
                    "error": f"Unknown tool: {function_name}"
                }
            else:
                result = function()

            log_event(
                "tool.result",
                tool=function_name,
                result=result,
            )

            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                }
            )


messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT,
    }
]

print(f"Tiny Agent — {MODEL}")
print("Type 'exit' to quit.\n")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() == "exit":
        break

    if not user_input:
        continue

    messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    try:
        response = run_agent(messages)
    except Exception as error:
        print(f"\nError: {error}\n")
        continue

    print(f"\nAssistant: {response}\n")
