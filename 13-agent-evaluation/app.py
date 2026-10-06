import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from uuid import uuid4

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

For complex calculation, such as calculating the day of the week from a given date, perform a step-by-step calculation before providing the correct answer.

Use existing conversation context when it already contains sufficient
information to answer accurately.

You are a professional and formal language is prefered.

Simply provide an answer and refrain from offering further assistance, such as 'Let me know if you need further assistance.' or similar.
""".strip()


def log_event(event, trace_id, **data):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "trace_id": trace_id,
        **data,
    }

    print(json.dumps(record))


def chat(messages, trace_id):
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOL_DEFINITIONS,
        "stream": False,
        "think": False
    }

    log_event(
        "llm.request",
        trace_id,
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

    llm_start_time = time.perf_counter()

    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read().decode("utf-8"))

    duration_ms = (time.perf_counter() - llm_start_time) * 1000

    assistant_message = result["message"]

    tool_calls = assistant_message.get("tool_calls", [])

    log_event(
        "llm.response",
        trace_id,
        has_content=bool(assistant_message.get("content")),
        tool_call_count=len(tool_calls),
        duration_ms=round(duration_ms, 2),
    )

    return assistant_message


def run_agent(messages):
    trace_id = str(uuid4())
    agent_start_time = time.perf_counter()
    llm_call_count = 0
    tool_call_count = 0
    tool_events = []

    log_event(
        "agent.start",
        trace_id,
    )

    while True:
        assistant_message = chat(messages, trace_id)
        llm_call_count += 1

        tool_calls = assistant_message.get("tool_calls", [])

        if not tool_calls:
            response = assistant_message.get("content", "")

            messages.append(
                {
                    "role": "assistant",
                    "content": response,
                }
            )

            duration_ms = (time.perf_counter() - agent_start_time) * 1000

            log_event(
                "agent.end",
                trace_id,
                duration_ms=round(duration_ms, 2),
                llm_call_count=llm_call_count,
                tool_call_count=tool_call_count,
            )

            return {
                "response": response,
                "trace_id": trace_id,
                "tool_events": tool_events,
                "llm_call_count": llm_call_count,
                "tool_call_count": tool_call_count,
            }

        messages.append(assistant_message)

        for tool_call in tool_calls:
            tool_call_count += 1
            function_name = tool_call["function"]["name"]
            tool_call_id = str(uuid4())

            log_event(
                "tool.call",
                trace_id,
                tool_call_id=tool_call_id,
                tool=function_name,
            )

            function = TOOL_REGISTRY.get(function_name)

            tool_start_time = time.perf_counter()

            if function is None:
                result = {
                    "error": f"Unknown tool: {function_name}"
                }
                success = False
            else:
                try:
                    result = function()
                    success = not (
                        isinstance(result, dict)
                        and "error" in result
                    )
                except Exception as exc:
                    result = {
                        "error": str(exc)
                    }
                    success = False

            duration_ms = (time.perf_counter() - tool_start_time) * 1000

            log_event(
                "tool.result",
                trace_id,
                tool_call_id=tool_call_id,
                tool=function_name,
                success=success,
                duration_ms=round(duration_ms, 2),
                result=result,
            )

            tool_events.append(
                {
                    "tool": function_name,
                    "success": success,
                    "result": result,
                }
            )

            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                }
            )


def main():
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
            result = run_agent(messages)
        except Exception as error:
            print(f"\nError: {error}\n")
            continue

        print(f"\nAssistant: {result['response']}\n")

if __name__ == "__main__":
    main()
