import app


def test_no_tool_response(monkeypatch):
    def fake_chat(messages, trace_id):
        return {
            "role": "assistant",
            "content": "Paris",
        }

    monkeypatch.setattr(app, "chat", fake_chat)

    messages = [
        {
            "role": "system",
            "content": app.SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": "What is the capital of France?",
        },
    ]

    result = app.run_agent(messages)

    assert result["response"] == "Paris"
    assert result["tool_events"] == []
    assert result["llm_call_count"] == 1
    assert result["tool_call_count"] == 0
    assert result["trace_id"]


def test_tool_call_loop(monkeypatch):
    chat_calls = []

    def fake_chat(messages, trace_id):
        chat_calls.append(list(messages))

        if len(chat_calls) == 1:
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "get_system_info",
                            "arguments": {},
                        }
                    }
                ],
            }

        return {
            "role": "assistant",
            "content": "The system information was retrieved.",
        }

    def fake_system_info():
        return {
            "hostname": "tiny-agent-test",
            "python_version": "3.12.0",
            "architecture": "aarch64",
            "system": "Linux",
        }

    monkeypatch.setattr(app, "chat", fake_chat)
    monkeypatch.setitem(
        app.TOOL_REGISTRY,
        "get_system_info",
        fake_system_info,
    )

    messages = [
        {
            "role": "system",
            "content": app.SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": "What system are you running on?",
        },
    ]

    result = app.run_agent(messages)

    assert result["response"] == "The system information was retrieved."
    assert result["llm_call_count"] == 2
    assert result["tool_call_count"] == 1

    assert len(result["tool_events"]) == 1

    tool_event = result["tool_events"][0]

    assert tool_event["tool"] == "get_system_info"
    assert tool_event["success"] is True
    assert tool_event["result"] == {
        "hostname": "tiny-agent-test",
        "python_version": "3.12.0",
        "architecture": "aarch64",
        "system": "Linux",
    }

    assert len(chat_calls) == 2

    second_call_messages = chat_calls[1]

    assert second_call_messages[-1]["role"] == "tool"
    assert "tiny-agent-test" in second_call_messages[-1]["content"]


def test_unknown_tool_fails_safely(monkeypatch):
    chat_calls = []

    def fake_chat(messages, trace_id):
        chat_calls.append(list(messages))

        if len(chat_calls) == 1:
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "nonexistent_tool",
                            "arguments": {},
                        }
                    }
                ],
            }

        return {
            "role": "assistant",
            "content": "The requested tool is unavailable.",
        }

    monkeypatch.setattr(app, "chat", fake_chat)

    messages = [
        {
            "role": "system",
            "content": app.SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": "Use the nonexistent tool.",
        },
    ]

    result = app.run_agent(messages)

    assert result["response"] == "The requested tool is unavailable."
    assert result["llm_call_count"] == 2
    assert result["tool_call_count"] == 1

    assert len(result["tool_events"]) == 1

    tool_event = result["tool_events"][0]

    assert tool_event["tool"] == "nonexistent_tool"
    assert tool_event["success"] is False
    assert tool_event["result"] == {
        "error": "Unknown tool: nonexistent_tool"
    }

    second_call_messages = chat_calls[1]

    assert second_call_messages[-1]["role"] == "tool"
    assert "Unknown tool: nonexistent_tool" in (
        second_call_messages[-1]["content"]
    )


def test_tool_exception_fails_safely(monkeypatch):
    chat_calls = []

    def fake_chat(messages, trace_id):
        chat_calls.append(list(messages))

        if len(chat_calls) == 1:
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "get_system_info",
                            "arguments": {},
                        }
                    }
                ],
            }

        return {
            "role": "assistant",
            "content": "The tool failed.",
        }

    def failing_tool():
        raise RuntimeError("simulated tool failure")

    monkeypatch.setattr(app, "chat", fake_chat)
    monkeypatch.setitem(
        app.TOOL_REGISTRY,
        "get_system_info",
        failing_tool,
    )

    messages = [
        {
            "role": "system",
            "content": app.SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": "What system are you running on?",
        },
    ]

    result = app.run_agent(messages)

    assert result["response"] == "The tool failed."
    assert result["llm_call_count"] == 2
    assert result["tool_call_count"] == 1

    assert len(result["tool_events"]) == 1

    tool_event = result["tool_events"][0]

    assert tool_event["tool"] == "get_system_info"
    assert tool_event["success"] is False
    assert tool_event["result"] == {
        "error": "simulated tool failure"
    }

    second_call_messages = chat_calls[1]

    assert second_call_messages[-1]["role"] == "tool"
    assert "simulated tool failure" in (
        second_call_messages[-1]["content"]
    )
