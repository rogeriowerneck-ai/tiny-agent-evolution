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


messages = []

print(f"Tiny Chat — {MODEL}")
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
        assistant_message = chat(messages)
    except Exception as error:
        print(f"\nError: Could not reach the LLM: {error}\n")
        messages.pop()
        continue

    tool_calls = assistant_message.get("tool_calls", [])

    if tool_calls:
        tool_call = tool_calls[0]
        function_name = tool_call["function"]["name"]

        print(f"\nModel selected tool: {function_name}")

        function = TOOL_REGISTRY.get(function_name)

        if function is None:
            print(f"Unknown tool: {function_name}\n")
            continue

        result = function()

        print("Tool result:")
        print(json.dumps(result, indent=2))
        print()

        continue

    response = assistant_message.get("content", "")

    messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )

    print(f"\nAssistant: {response}\n")
