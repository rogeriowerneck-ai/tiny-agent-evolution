import json
import os
import urllib.request


OLLAMA_URL = os.environ["OLLAMA_URL"]
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")


def chat(messages):
    payload = {
        "model": MODEL,
        "messages": messages,
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

    return result["message"]["content"]


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
        response = chat(messages)
    except Exception as error:
        print(f"\nError: Could not reach the LLM: {error}\n")
        messages.pop()
        continue

    messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )

    print(f"\nAssistant: {response}\n")
