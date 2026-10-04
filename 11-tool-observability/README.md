# Stage 11 — Tool-Call Observability

Stage 10 introduced agent traces.

Tiny Agent could now correlate all events produced while handling one user
request by assigning them the same:

    trace_id

This told us which events belonged to the same agent execution.

But tool execution itself still had limited observability.

Stage 11 makes individual tool calls observable.

## Goal

Observe each tool invocation as a distinct operation.

For every tool call, Tiny Agent now records:

    tool_call_id
    tool name
    success or failure
    execution duration
    result

The trace identifies the complete agent execution.

The tool call ID identifies one particular tool invocation inside that trace.

## The Problem

Stage 10 produced tool events such as:

    {
        "event": "tool.call",
        "trace_id": "...",
        "tool": "get_cpu_temperature"
    }

and:

    {
        "event": "tool.result",
        "trace_id": "...",
        "tool": "get_cpu_temperature",
        "result": {
            "temperature_celsius": 39.0
        }
    }

This told us that a tool was called and what it returned.

But several questions remained:

    Which result belongs to which specific invocation?

    Did the tool succeed?

    Did it fail?

    How long did it take?

    What happened if the tool raised an exception?

Stage 11 answers those questions.

## Tool Call ID

Each tool invocation now receives its own UUID:

    tool_call_id = str(uuid4())

For example:

    24b88d90-35a9-4068-a80a-b650c9c6d2e7

The same ID is attached to both:

    tool.call
    tool.result

Conceptually:

    tool_call_id = A
        |
        +-- tool.call
        |
        +-- tool.result

A second invocation receives another ID:

    tool_call_id = B

even if it calls the same tool.

## Trace ID Versus Tool Call ID

The two identifiers describe different levels of execution.

A trace ID identifies one complete agent run:

    trace_id
        |
        +-- llm.request
        +-- llm.response
        +-- tool.call
        +-- tool.result
        +-- llm.request
        +-- llm.response

A tool call ID identifies one tool invocation inside that run:

    trace_id
        |
        +-- tool_call_id A
        |       |
        |       +-- tool.call
        |       +-- tool.result
        |
        +-- tool_call_id B
                |
                +-- tool.call
                +-- tool.result

Therefore:

    trace_id
        =
    agent execution identity

while:

    tool_call_id
        =
    tool invocation identity

## Why Not Use the Timestamp?

Every event already has a timestamp.

For Tiny Agent's current sequential execution model, timestamps and event
ordering are often enough to understand which call produced which result.

But timestamps answer:

    When did this happen?

They are not intended to answer:

    Which logical operation does this event belong to?

A tool call ID gives the invocation a stable identity independent of timing.

This becomes especially useful for:

    repeated calls to the same tool
    retries
    long-running tools
    parallel tool execution
    asynchronous execution
    log searches
    metrics
    debugging

## Tool Call Context

The tool call ID belongs to the agent runtime.

It is not passed into the tool function itself.

Tiny Agent still executes:

    result = function()

rather than:

    result = function(tool_call_id)

The runtime keeps the relationship between the ID and the invocation.

This keeps tool implementation separate from observability concerns.

The tool only needs to perform its task.

Tiny Agent is responsible for identifying, measuring, and logging the
execution.

## Sequential Execution

Tiny Agent currently executes tools synchronously and sequentially.

For two calls to the same tool, execution looks like:

    tool.call    ID=A
    tool.result  ID=A

    tool.call    ID=B
    tool.result  ID=B

The first function call completes before the loop moves to the second one.

Because of this, results cannot currently arrive out of order.

If Tiny Agent later introduces parallel execution, the tool call ID will need
to travel with each execution context so that results remain associated with
the correct invocation even when they complete in a different order.

## Measuring Tool Duration

Stage 11 measures tool execution using:

    time.perf_counter()

Immediately before execution:

    start_time = time.perf_counter()

After execution:

    duration_ms = (time.perf_counter() - start_time) * 1000

The result event records:

    duration_ms

For example:

    "duration_ms": 0.31

A monotonic performance counter is used because elapsed-time measurement
should not depend on changes to the system clock.

## Success and Failure

Each tool result now includes:

    success

A normal tool result produces:

    "success": true

An error produces:

    "success": false

Tiny Agent currently recognizes three failure paths.

### Unknown Tool

If the requested function does not exist in the tool registry:

    {
        "error": "Unknown tool: ..."
    }

and:

    success = False

### Tool Raises an Exception

Tool execution is protected by:

    try:
        result = function()
    except Exception as exc:
        ...

An exception is converted into an error result and recorded as:

    success = False

This prevents a tool exception from escaping before the result event can be
recorded.

### Tool Returns an Error

Some Tiny Agent tools already handle their own exceptions and return:

    {
        "error": "..."
    }

instead of raising an exception.

Stage 11 therefore treats a dictionary containing an "error" key as a failed
tool execution.

This is a Tiny Agent convention.

It gives the observability layer a consistent success/failure signal even
when individual tools represent errors differently.

## Example

We asked:

    What's the current CPU temperature?

The tool call event was:

    {
        "event": "tool.call",
        "trace_id": "fee61ab9-85e3-4e53-a550-cebd2ec5653a",
        "tool_call_id": "24b88d90-35a9-4068-a80a-b650c9c6d2e7",
        "tool": "get_cpu_temperature"
    }

The result event was:

    {
        "event": "tool.result",
        "trace_id": "fee61ab9-85e3-4e53-a550-cebd2ec5653a",
        "tool_call_id": "24b88d90-35a9-4068-a80a-b650c9c6d2e7",
        "tool": "get_cpu_temperature",
        "success": true,
        "duration_ms": 0.31,
        "result": {
            "temperature_celsius": 39.0
        }
    }

The same:

    trace_id

connects the events to the agent run.

The same:

    tool_call_id

connects the call to its result.

## Repeated Calls

We then asked for the CPU temperature again.

The second agent run received a new trace ID.

The second invocation of the same tool also received a new tool call ID.

This demonstrated two levels of identity:

    request 1
        trace A
            tool call A

    request 2
        trace B
            tool call B

The tool name was the same.

The invocation identity was different.

## Observability Boundary

Stage 11 reinforces an important architectural boundary.

Tools are responsible for performing operations:

    get_cpu_temperature()
    get_system_info()
    get_current_date_time()

The agent runtime is responsible for observing those operations:

    identify the invocation
    record the call
    execute the tool
    measure duration
    classify success or failure
    record the result

This keeps observability concerns out of individual tool implementations.

## What We Are Not Building Yet

Stage 11 intentionally does not introduce:

    parallel tool execution
    asynchronous execution
    retries
    tool arguments
    LLM latency measurement
    total agent latency measurement
    aggregated metrics
    persistence
    distributed tracing
    OpenTelemetry
    evaluation
    regression tests

The goal of this stage is specifically to make individual tool executions
observable.

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

Stage 10 added:

    Which events belong to the same agent execution?

Stage 11 adds:

    Which individual tool invocation is this?

    Did it succeed?

    How long did it take?

    What did it return?

## What Comes Next?

We can now observe individual tool executions.

Our runtime test also revealed something important.

The CPU temperature tool itself completed in approximately:

    0.31 ms

while the surrounding LLM requests took seconds.

We can infer this from event timestamps, but latency is not yet represented
explicitly for the rest of the agent.

The next stage will make execution time a first-class observable property
across the agent and begin turning individual observations into metrics.

    Stage 12 — Latency and Metrics
