import json
import os
import urllib.request

from tools import TOOL_DEFINITIONS, TOOL_REGISTRY


OLLAMA_URL = os.environ["OLLAMA_URL"]
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")


def chat(messages):
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOL_DEFINITIONS,
        "stream": False,
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["message"]


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

            print(f"\nModel selected tool: {function_name}")

            function = TOOL_REGISTRY.get(function_name)

            if function is None:
                result = {
                    "error": f"Unknown tool: {function_name}"
                }
            else:
                result = function()

            print("Tool result:")
            print(json.dumps(result, indent=2))

            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                }
            )


messages = []

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
