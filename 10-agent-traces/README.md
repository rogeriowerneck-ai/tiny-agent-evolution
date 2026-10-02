# Stage 10 — Agent Traces

Stage 09 introduced structured event logging.

Tiny Agent could now represent important actions as timestamped JSON events:

    llm.request
    llm.response
    tool.call
    tool.result

This told us what happened during execution.

But individual events did not tell us which events belonged to the same
agent run.

Stage 10 introduces agent traces.

## Goal

Correlate all events produced while Tiny Agent handles one user request.

A trace represents one complete execution of:

    run_agent()

for one user message.

Every event produced during that execution receives the same:

    trace_id

The next user request receives a new trace ID.

## The Problem

Imagine observing these events:

    llm.request
    llm.request
    tool.call
    llm.response
    tool.result
    llm.response

If multiple agent runs were happening at the same time, timestamps and event
names alone would not reliably tell us which events belonged together.

We need correlation.

## Trace ID

At the beginning of each agent run, Tiny Agent generates a UUID:

    trace_id = str(uuid4())

For example:

    f91934ba-df7f-49e5-94dc-3a705d456eb7

That identifier remains unchanged throughout the entire run.

The next invocation of run_agent() generates another UUID.

## Trace Boundary

Stage 10 also introduces two events:

    agent.start
    agent.end

These mark the successful boundaries of an agent execution.

A typical trace now looks like:

    agent.start
        |
        v
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
        |
        v
    agent.end

Every event in this sequence has the same trace ID.

## Adding the Trace ID to Events

The event logger now accepts a trace ID:

    def log_event(event, trace_id, **data):
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "trace_id": trace_id,
            **data,
        }

        print(json.dumps(record))

This makes correlation part of the event structure.

An event now looks like:

    {
        "timestamp": "2026-10-02T13:04:41.454339+00:00",
        "event": "tool.call",
        "trace_id": "f91934ba-df7f-49e5-94dc-3a705d456eb7",
        "tool": "get_cpu_temperature"
    }

## Propagating Trace Context

Generating a trace ID is not enough.

Every component producing events must know which trace it belongs to.

run_agent() therefore creates the ID:

    trace_id = str(uuid4())

and passes it to chat():

    assistant_message = chat(messages, trace_id)

chat() then includes the same ID in its LLM events.

Tool events emitted by run_agent() also use the same ID.

This is called context propagation.

The identifier is created once and propagated through the execution path.

## Example — First User Request

We asked:

    What is the current CPU temp?

Tiny Agent generated:

    trace_id =
    f91934ba-df7f-49e5-94dc-3a705d456eb7

The resulting trace was:

    agent.start
    llm.request
    llm.response
    tool.call
    tool.result
    llm.request
    llm.response
    agent.end

The tool selected was:

    get_cpu_temperature

and the observation was:

    40.5 C

Every event carried the same trace ID.

## Example — Second User Request

In the same conversation we then asked:

    What time is it now?

Tiny Agent generated a different trace ID:

    b0fca2f2-9269-4a01-b24e-d2148a5b9a0f

The agent selected:

    get_current_date_time

and again produced:

    agent.start
    llm.request
    llm.response
    tool.call
    tool.result
    llm.request
    llm.response
    agent.end

All events in the second run shared the new trace ID.

## Trace Versus Conversation

A trace is not the same thing as a conversation.

The conversation persists across multiple user turns.

Each user turn creates a new agent execution and therefore a new trace.

Conceptually:

    Conversation
        |
        +-- User request 1
        |       |
        |       +-- Trace A
        |
        +-- User request 2
        |       |
        |       +-- Trace B
        |
        +-- User request 3
                |
                +-- Trace C

The conversation provides context across turns.

The trace describes one execution within that conversation.

This distinction became visible during our test.

The first LLM request of the second trace had:

    message_count = 6

because messages from the previous turn were still part of the conversation.

The trace changed.

The conversation context did not reset.

## Events Versus Traces

Stage 09 gave us events.

An event represents one occurrence:

    tool.call

or:

    llm.response

Stage 10 groups related events into traces.

Therefore:

    event
        =
    one thing that happened

while:

    trace
        =
    related events belonging to one agent execution

A trace does not replace events.

It connects them.

## Why UUIDs?

Trace identifiers need to distinguish independent executions.

UUIDs provide identifiers that can be generated locally without requiring
a central counter or database.

For Tiny Agent we use:

    uuid4()

from Python's standard library.

This keeps the implementation simple while giving each agent run a distinct
identifier.

## Successful Completion

Currently:

    agent.end

is emitted when the agent successfully reaches its final response.

If an exception escapes run_agent(), the trace may contain:

    agent.start

without:

    agent.end

We deliberately leave richer error and completion semantics for later
observability work.

Stage 10 is focused on event correlation.

## What We Are Not Building Yet

Stage 10 intentionally does not introduce:

    span IDs
    parent-child spans
    tool durations
    LLM durations
    aggregated metrics
    distributed tracing systems
    OpenTelemetry
    evaluation
    regression tests

Those concepts would obscure the central lesson of this stage.

For now, a trace is simply a set of related events sharing one trace ID.

## Evolution So Far

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

Stage 09 answered:

    What happened?

Stage 10 adds:

    Which events belong to the same agent execution?

## What Comes Next?

We can now identify a complete agent execution.

We can also see when a tool was called and what result it returned.

But tool execution still has limited observability.

Questions remain:

    What arguments did the model provide?

    Did the tool execute successfully?

    Did it fail?

    What error occurred?

    What exactly did the tool return?

Tools are one of the most important boundaries between probabilistic model
behavior and deterministic application code.

The next stage focuses specifically on making that boundary observable.

    Stage 11 — Tool-Call Observability
