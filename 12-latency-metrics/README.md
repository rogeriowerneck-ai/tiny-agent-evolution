# Stage 12 — Latency and Metrics

Stage 11 made individual tool calls observable.

Tiny Agent could identify each tool invocation, determine whether it succeeded,
measure its execution duration, and correlate it with the surrounding agent
trace.

But tool execution is only one part of an agent run.

Stage 12 expands observability to the complete execution.

## Goal

Make latency a first-class observable property across Tiny Agent and introduce
simple per-run metrics.

For each agent execution, we now measure:

    LLM request latency
    tool execution latency
    total agent latency

We also summarize:

    number of LLM calls
    number of tool calls

This lets us answer questions such as:

    How long did the complete agent run take?

    How much time was spent waiting for the LLM?

    How much time was spent executing tools?

    How many LLM calls were required?

    How many tools were invoked?

    How much orchestration overhead remains?

## From Events to Measurements

Earlier stages told us what happened.

For example:

    agent.start
    llm.request
    llm.response
    tool.call
    tool.result
    llm.request
    llm.response
    agent.end

The timestamps allowed us to estimate durations manually.

Stage 12 makes those durations explicit.

A tool result already contains:

    duration_ms

Now an LLM response also contains:

    duration_ms

and the final agent event contains:

    duration_ms
    llm_call_count
    tool_call_count

The trace therefore contains both detailed events and a compact execution
summary.

## Measuring Elapsed Time

Tiny Agent uses:

    time.perf_counter()

to measure durations.

For example:

    start_time = time.perf_counter()

    operation()

    duration_ms = (time.perf_counter() - start_time) * 1000

`perf_counter()` is appropriate for measuring elapsed time because it is a
monotonic high-resolution performance counter.

A wall-clock timestamp answers:

    When did this happen?

A performance counter answers:

    How long did this take?

These are different observability concerns.

Tiny Agent continues to use UTC timestamps for event chronology and
`perf_counter()` for elapsed durations.

## LLM Latency

The LLM timer surrounds the HTTP operation performed against Ollama.

Conceptually:

    llm.request
        |
        |  start timer
        v
    HTTP request to Ollama
        |
        |  model processing
        |  network round trip
        |  response read
        v
    stop timer
        |
        v
    llm.response
        duration_ms

This is client-observed LLM latency.

It is not intended to isolate pure model inference time.

Instead, it measures the time Tiny Agent actually spends waiting for the LLM
operation to complete.

For example:

    {
        "event": "llm.response",
        "trace_id": "...",
        "has_content": false,
        "tool_call_count": 1,
        "duration_ms": 1126.28
    }

This tells us that the LLM request took approximately 1.13 seconds from Tiny
Agent's perspective.

## Tool Latency

Tool latency was introduced in Stage 11 and remains part of the Stage 12
latency model.

Each tool invocation has its own timer:

    tool_start_time = time.perf_counter()

The resulting `tool.result` contains:

    duration_ms

For example:

    {
        "event": "tool.result",
        "trace_id": "...",
        "tool_call_id": "...",
        "tool": "get_cpu_temperature",
        "success": true,
        "duration_ms": 0.31,
        "result": {
            "temperature_celsius": 39.0
        }
    }

This gives us operation-level latency inside the larger agent trace.

## Agent Latency

Stage 12 also measures the complete agent execution.

The timer starts when `run_agent()` begins processing the user request:

    agent_start_time = time.perf_counter()

It stops immediately before the final `agent.end` event.

Conceptually:

    agent.start
        |
        +-- LLM call
        |
        +-- tool execution
        |
        +-- LLM call
        |
        v
    agent.end
        duration_ms

For example:

    {
        "event": "agent.end",
        "trace_id": "...",
        "duration_ms": 2397.46,
        "llm_call_count": 2,
        "tool_call_count": 1
    }

This gives us end-to-end latency for one agent execution.

## Timer Scope

Stage 12 uses explicit timer names:

    llm_start_time
    tool_start_time
    agent_start_time

This is important because the timers represent different scopes.

During development, a generic variable named:

    start_time

was used for both the agent timer and the tool timer inside `run_agent()`.

The tool timer overwrote the original agent timer.

As a result, the reported agent duration incorrectly measured approximately
only the final part of the execution.

The instrumentation itself exposed the problem because:

    agent duration < sum of component durations

which is impossible for sequential execution.

Using scope-specific names makes the meaning explicit and prevents one timer
from accidentally replacing another.

## Per-Run Metrics

Stage 12 introduces two simple counters:

    llm_call_count
    tool_call_count

They are initialized when an agent run begins:

    llm_call_count = 0
    tool_call_count = 0

Every call to `chat()` increments:

    llm_call_count

Every tool invocation processed by the agent increments:

    tool_call_count

The final `agent.end` event therefore summarizes the execution.

A request requiring one tool typically produces:

    llm_call_count = 2
    tool_call_count = 1

because the agent first asks the LLM what to do, executes the requested tool,
and then asks the LLM to produce the final answer.

A request requiring no tool typically produces:

    llm_call_count = 1
    tool_call_count = 0

These are per-run metrics rather than global process counters.

## Detailed Events and Summary Metrics

The detailed events remain useful:

    llm.response
    tool.result

They tell us about individual operations.

The final:

    agent.end

provides a summary of the complete run.

Conceptually:

    trace_id
        |
        +-- llm.response
        |       duration_ms
        |
        +-- tool.result
        |       duration_ms
        |
        +-- llm.response
        |       duration_ms
        |
        +-- agent.end
                duration_ms
                llm_call_count
                tool_call_count

This gives us both operation-level and trace-level observability.

## Timing Reconciliation

Because Tiny Agent currently executes these operations sequentially, we can
compare total agent latency with the sum of the measured components.

For a tool-using request:

    component time =
        first LLM latency
        + tool latency
        + second LLM latency

Then:

    orchestration overhead =
        agent latency
        - component time

One validated run produced approximately:

    LLM #1        1126.28 ms
    Tool             0.31 ms
    LLM #2        1268.50 ms
                  ----------
    Components     2395.09 ms

    Agent          2397.46 ms
                  ----------
    Overhead          2.37 ms

The measurements therefore reconcile closely.

The small difference includes work such as:

    event logging
    UUID generation
    message manipulation
    Python control flow
    JSON processing outside timed regions

## No-Tool Validation

The no-tool execution path was also tested.

A simple greeting produced approximately:

    LLM             983.43 ms
    Agent           984.08 ms

with:

    llm_call_count = 1
    tool_call_count = 0

The difference was approximately:

    0.65 ms

This confirms that the counters and total timer also behave correctly when the
agent does not invoke a tool.

## What the Metrics Reveal

The measurements already reveal an important characteristic of Tiny Agent.

The CPU temperature tool typically executes in well under:

    1 ms

while an LLM request takes roughly:

    1 second or more

For the tested interaction, almost all meaningful latency comes from the LLM
calls rather than tool execution or Python orchestration.

This distinction would have been difficult to quantify reliably from the user
experience alone.

Observability turns that intuition into measurable evidence.

## Why Not Aggregate Globally Yet?

Stage 12 intentionally keeps metrics attached to individual traces.

We are not yet calculating process-wide values such as:

    average latency
    minimum latency
    maximum latency
    p50 latency
    p95 latency
    p99 latency
    total requests
    requests per second
    tool success rate

Those require decisions about storage, aggregation windows, process lifetime,
and persistence.

Introducing those concerns now would mix several concepts into one stage.

Instead, Stage 12 establishes the raw measurements from which those metrics
could later be derived.

## Observability Layers

Tiny Agent now has several complementary observability levels.

Stage 09 introduced events:

    What happened?

Stage 10 introduced traces:

    Which events belong to the same agent execution?

Stage 11 introduced tool-call observability:

    Which particular tool invocation is this?

    Did it succeed?

    How long did it take?

Stage 12 introduces broader latency and per-run metrics:

    How long did the LLM take?

    How long did the whole agent take?

    How many LLM calls were required?

    How many tools were invoked?

Together:

    event
        |
        v
    trace
        |
        v
    operation
        |
        v
    measurement
        |
        v
    metric

Each stage builds on the previous one.

## What We Are Not Building Yet

Stage 12 intentionally does not introduce:

    metrics persistence
    global aggregation
    dashboards
    Prometheus
    Grafana
    OpenTelemetry
    distributed tracing
    parallel execution
    asynchronous execution
    retries
    agent evaluation
    regression tests

The goal is to understand and validate the measurements before introducing
infrastructure around them.

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

Stage 12 completes the basic runtime observability foundation.

Tiny Agent can now explain not only what it did, but also how long the major
parts of the execution took and how much work was required.

## What Comes Next?

We can now observe and measure an agent execution.

The next question is different:

    Did the agent behave correctly?

Latency tells us how fast the agent was.

Tracing tells us what the agent did.

Neither tells us whether its decisions and answers were good.

The next stage introduces that new concern:

    Stage 13 — Agent Evaluation
