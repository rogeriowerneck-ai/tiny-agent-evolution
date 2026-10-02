# Stage 09 — Event Logging

Stage 08 introduced behavioral policy through a system prompt.

That gave Tiny Agent instructions about when to use tools, when to obtain
fresh information, and when to reuse conversation context.

It also exposed an important problem:

    How do we know what actually happened during an agent run?

Stage 09 begins the observability arc by introducing structured event logging.

## Goal

Represent important actions inside Tiny Agent as structured, timestamped
events.

Instead of relying on human-oriented debug messages such as:

    Model selected tool: get_cpu_temperature

Tiny Agent now emits machine-readable JSON events.

For example:

    {
        "timestamp": "2026-10-02T12:39:04.546711+00:00",
        "event": "tool.call",
        "tool": "get_cpu_temperature"
    }

This gives us a consistent representation of what happens during execution.

## The Event Logger

We introduce a small logging function:

    def log_event(event, **data):
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **data,
        }

        print(json.dumps(record))

Every event contains at least:

    timestamp
    event

Additional fields depend on the type of event.

This is intentionally simple.

We are not introducing a logging framework, tracing system, metrics
collector, or external observability platform.

The purpose of this stage is to understand the basic concept first.

## Event Types

Tiny Agent currently emits four types of events:

    llm.request
    llm.response
    tool.call
    tool.result

Together they expose the major boundaries of the current agent loop.

## LLM Request

Before sending a request to Ollama, Tiny Agent emits:

    {
        "event": "llm.request",
        "model": "qwen3:8b",
        "message_count": 2
    }

We deliberately do not log the complete conversation.

At this stage we only record enough information to observe that an LLM
request occurred and understand its basic context.

## LLM Response

After Ollama returns a response, Tiny Agent emits:

    {
        "event": "llm.response",
        "has_content": false,
        "tool_call_count": 1
    }

This lets us distinguish between responses that contain a final answer and
responses that request tool execution.

## Tool Call

When the model selects a tool, Tiny Agent emits:

    {
        "event": "tool.call",
        "tool": "get_cpu_temperature"
    }

This replaces the previous human-oriented debug message.

The tool selection is now represented as structured data.

## Tool Result

After executing the tool, Tiny Agent emits:

    {
        "event": "tool.result",
        "tool": "get_cpu_temperature",
        "result": {
            "temperature_celsius": 39.5
        }
    }

The observation returned by the tool is therefore visible in the event
stream.

## Example Run

We asked:

    What is the current CPU temp?

Tiny Agent produced the following sequence:

    llm.request
        |
        v
    llm.response
        |
        v
    tool.call
        |
        v
    tool.result
        |
        v
    llm.request
        |
        v
    llm.response

The model first received the user request.

It decided that fresh information was required and selected:

    get_cpu_temperature

The tool returned:

    39.5 C

That observation was added to the conversation and sent back to the model.

The second LLM response contained the final answer.

## The Agent as an Event Stream

Before this stage, understanding an agent run required reading a mixture of
debug output and final responses.

Now the execution can be viewed as a sequence of events:

    llm.request
    llm.response
    tool.call
    tool.result
    llm.request
    llm.response

This is the beginning of observability.

The events tell us what happened and in what order.

## Why Structured Events?

Human-readable messages are useful while developing small programs.

For example:

    Tool result:
    {
        "temperature_celsius": 39.5
    }

But free-form text becomes difficult to process as a system grows.

Structured events can later be:

- searched
- filtered
- stored
- correlated
- counted
- analyzed
- visualized

JSON gives every event a predictable structure that both humans and
software can consume.

## Why UTC?

Event timestamps are recorded in UTC:

    2026-10-02T12:39:04.546711+00:00

The local machine or user may operate in another timezone.

Using UTC gives telemetry a consistent time reference across machines and
services.

Presentation layers can convert timestamps to local time when necessary.

## What We Are Not Building Yet

Stage 09 intentionally does not introduce:

    trace IDs
    run IDs
    latency measurements
    counters
    aggregated metrics
    evaluation
    regression tests

Those concepts belong to later stages.

Keeping them separate allows each stage to introduce one major idea.

## Arc 2 — Observability

Stage 09 begins the second major arc of Tiny Agent Evolution.

    ARC 1 — AGENT MECHANICS

    01  Container
    02  Simple Chat
    03  Conversation Context
    04  First Tool
    05  Tool Registry
    06  Agent Loop
    07  Multiple Tools
    08  Agent Behavior


    ARC 2 — OBSERVABILITY

    09  Event Logging
    10  Agent Traces
    11  Tool-Call Observability
    12  Latency and Metrics
    13  Agent Evaluation
    14  Regression Tests

Arc 1 focused on making the agent capable of acting.

Arc 2 focuses on understanding, measuring, and testing those actions.

## What Comes Next?

Our event stream tells us:

    what happened

and:

    when it happened

But suppose multiple users or agent runs produce events at the same time.

How do we know which events belong to the same execution?

For example:

    llm.request
    llm.request
    tool.call
    llm.response
    tool.result

Without additional context, events from different runs could become
indistinguishable.

The next stage introduces correlation between events.

That leads to:

    Stage 10 — Agent Traces
