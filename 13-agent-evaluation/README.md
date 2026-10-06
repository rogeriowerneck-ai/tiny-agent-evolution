# Stage 13 — Agent Evaluation

Stage 12 made Tiny Agent measurable.

We could observe:

    LLM request latency
    tool execution latency
    total agent latency
    LLM call count
    tool call count

But observability and metrics answer questions such as:

    What happened?

    How long did it take?

They do not answer:

    Did the agent behave correctly?

Stage 13 introduces systematic agent evaluation.

## Goal

Measure Tiny Agent's behavior across repeated executions.

The evaluation framework separates several dimensions of agent behavior:

    tool selection
    tool execution
    answer correctness
    overall success

This distinction matters because an agent can select and execute the correct
tool while still producing an incorrect final answer.

## From Observability to Evaluation

The previous observability stages built the evidence required for evaluation.

Conceptually:

    user request
        |
        v
    LLM decision
        |
        v
    tool selection
        |
        v
    tool execution
        |
        v
    tool observation
        |
        v
    LLM interpretation / reasoning
        |
        v
    final answer

A failure can occur at different points in this sequence.

Without structured observations, a wrong final answer tells us very little
about where the problem occurred.

Stage 13 uses the observability foundation to separate those failure modes.

## Structured Agent Results

Before Stage 13, `run_agent()` returned only the final response string.

Stage 13 returns a structured result:

    {
        "response": response,
        "trace_id": trace_id,
        "tool_events": tool_events,
        "llm_call_count": llm_call_count,
        "tool_call_count": tool_call_count,
    }

The interactive interface still prints only:

    result["response"]

but evaluation code can inspect the additional execution evidence.

## Capturing Tool Events

Each tool execution is recorded in:

    tool_events

A recorded event contains:

    {
        "tool": function_name,
        "success": success,
        "result": result,
    }

This lets the evaluator determine:

    which tool was selected
    whether the tool succeeded
    what observation the tool returned

The evaluator therefore does not need to infer tool behavior from the final
natural-language answer or scrape the JSON logs.

## Evaluation Metrics

Each case reports four primary metrics.

### Tool Selection

Did the agent make the correct decision about tool usage?

For a tool-based case, this means selecting the expected tool.

For a no-tool case, it means correctly selecting no tool.

### Tool Execution

Did the selected tool execute successfully?

For a no-tool case, this passes when no unnecessary tool was executed.

### Answer Correctness

Did the final response contain the expected answer?

The exact correctness check depends on the evaluation case.

### Overall Success

A trial passes overall only when all required dimensions pass:

    tool selection
        AND
    tool execution
        AND
    answer correctness

Keeping these metrics separate makes the location of failures visible.

## Repeated Trials

LLM behavior is not fully deterministic.

A single successful run does not demonstrate reliable behavior.

Likewise, one failure does not necessarily describe typical behavior.

Each evaluation case is therefore executed repeatedly.

The current configuration uses:

    TRIALS = 5

For every case, Stage 13 prints individual trial results followed by aggregate
percentages.

For example:

    Tool selection:       5/5  100.0%
    Tool execution:       5/5  100.0%
    Answer correctness:   3/5   60.0%
    Overall passes:       3/5   60.0%

This makes behavioral variability directly observable.

## Evaluation Cases

Stage 13 currently contains four cases:

    current_weekday
    cpu_temperature
    system_info
    no_tool

They intentionally exercise different capabilities:

    current_weekday  -> tool use + derived reasoning
    cpu_temperature  -> tool use + single-value relay
    system_info      -> tool use + multi-value relay
    no_tool          -> direct answer without unnecessary tools

## Case 1 — Current Weekday

The first evaluation asks:

    What day of the week is it?

Expected behavior:

    1. call get_current_date_time
    2. successfully obtain the current date and time
    3. determine the weekday from the observed date
    4. return the correct weekday

This case is interesting because the tool does not directly return the answer.

For example, the tool may return:

    {
        "datetime": "2026-10-06T13:47:33.634780-03:00",
        "timezone": "UTC-03:00"
    }

The model must transform:

    2026-10-06

into:

    Tuesday

The execution therefore contains both observation and reasoning:

    get_current_date_time
            |
            v
       current date
            |
            v
       LLM reasoning
            |
            v
         weekday

### Weekday Answer Extraction

The evaluator extracts weekday names from the final response.

If several weekday names occur, the final weekday mentioned is treated as the
answer.

This is intentionally a lightweight heuristic rather than a general semantic
grader.

For example, responses such as:

    Tuesday, not Wednesday.

or:

    It is Tuesday. Yesterday was Monday.

could confuse the heuristic.

That limitation is acceptable for this educational stage, but it is important
when interpreting the results.

## Case 2 — CPU Temperature

The second evaluation asks:

    What is the current CPU temperature?

Expected behavior:

    1. call get_cpu_temperature
    2. successfully obtain the current temperature
    3. report that temperature correctly

This case differs from the weekday evaluation because very little reasoning is
required.

The tool may return:

    {
        "temperature_celsius": 38.5
    }

The model primarily needs to preserve that observation in its final response.

The expected value is not hard-coded.

Instead, the evaluator obtains it from the tool event generated during the same
agent run.

Conceptually:

    tool observation
        |
        +------------------> expected value
        |
        v
    LLM response
        |
        +------------------> actual value

The evaluator compares those two values.

This is important because CPU temperature changes over time.

## Case 3 — System Information

The third evaluation asks:

    What system are you running on?

The get_system_info tool returns four fields:

    hostname
    python_version
    architecture
    system

For example:

    {
        "hostname": "d5ea79cbae5c",
        "python_version": "3.12.15",
        "architecture": "aarch64",
        "system": "Linux"
    }

The evaluator derives the expected values from the actual tool result.

It then verifies that all four observed values appear in the final response.

This case tests whether the model can preserve and communicate several
independent pieces of information from one tool observation.

The hostname belongs to the Docker container because the tool executes inside
that container.

This case is therefore more complex than the CPU temperature relay, but it
still does not require the model to derive a new fact from the observation.

## Case 4 — No Tool

The fourth evaluation asks:

    What is the capital of France?

The expected answer is:

    Paris

None of Tiny Agent's available tools are necessary for this question.

The expected behavior is therefore:

    tool calls = 0

This evaluates an important capability:

    knowing when not to use a tool

For this case:

    tool_selection = True

means that the agent correctly selected no tool.

Likewise:

    tool_execution = True

means that no unnecessary tool execution occurred.

This convention keeps the four evaluation metrics consistent across all cases.

## Comparing The Four Cases

The four cases exercise increasingly different execution paths:

    no_tool
        |
        +-- answer from model knowledge

    cpu_temperature
        |
        +-- select tool
        +-- observe one value
        +-- relay value

    system_info
        |
        +-- select tool
        +-- observe several values
        +-- relay several values

    current_weekday
        |
        +-- select tool
        +-- observe date
        +-- derive a new value
        +-- answer

This distinction became important when we examined the experimental results.

## Complete Evaluation Suite Results

The complete four-case suite was executed using:

    model:  qwen3:8b
    think:  false
    trials: 5 per case

The observed results were:

    current_weekday
        Tool selection:       5/5  100.0%
        Tool execution:       5/5  100.0%
        Answer correctness:   3/5   60.0%
        Overall passes:       3/5   60.0%

    cpu_temperature
        Tool selection:       5/5  100.0%
        Tool execution:       5/5  100.0%
        Answer correctness:   5/5  100.0%
        Overall passes:       5/5  100.0%

    system_info
        Tool selection:       5/5  100.0%
        Tool execution:       5/5  100.0%
        Answer correctness:   5/5  100.0%
        Overall passes:       5/5  100.0%

    no_tool
        Tool selection:       5/5  100.0%
        Tool execution:       5/5  100.0%
        Answer correctness:   5/5  100.0%
        Overall passes:       5/5  100.0%

The final overall summary was:

    current_weekday: 3/5   60.0%
    cpu_temperature: 5/5  100.0%
    system_info:     5/5  100.0%
    no_tool:         5/5  100.0%

Across all four cases:

    18 / 20 trials passed

or:

    90%

The aggregate percentage is useful, but it hides the most important result.

All observed failures occurred in the weekday reasoning case.

## Locating The Failure

The weekday trace showed that Tiny Agent reliably selected and executed the
correct tool.

For example:

    user
      |
      v
    LLM
      |
      v
    get_current_date_time
      |
      v
    2026-10-06
      |
      v
    LLM
      |
      v
    Tuesday or Wednesday

The correct date was available to the model in every trial.

The failure therefore did not occur during:

    tool selection

or:

    tool execution

It occurred during:

    reasoning over the tool result

This is exactly the kind of distinction that becomes possible when evaluation
is built on top of observability.

## Relay Tasks Versus Reasoning Tasks

The experiments reveal a useful distinction between different agent tasks.

CPU temperature is primarily:

    observe
      |
      v
    relay one value

System information is primarily:

    observe
      |
      v
    relay several values

Current weekday is:

    observe
      |
      v
    transform / reason
      |
      v
    derive a new value

In the complete suite, the relay cases achieved:

    cpu_temperature: 5/5
    system_info:     5/5

while the reasoning case achieved:

    current_weekday: 3/5

Reliable tool usage therefore does not imply reliable reasoning over a tool
result.

## Earlier Weekday Baseline

The weekday case was exercised more extensively during development.

An earlier repeated baseline using:

    think: false

produced:

    Tool selection:       25/25
    Tool execution:       25/25
    Answer correctness:    8/25
    Overall passes:        8/25

The answer correctness rate was therefore:

    32%

Additional five-trial batches produced results including:

    1/5
    3/5
    2/5
    3/5

The exact percentage varies substantially between small batches.

The qualitative pattern, however, remains stable:

    tool selection     -> reliable
    tool execution     -> reliable
    weekday reasoning  -> unstable

This illustrates why repeated evaluation is more informative than a single
successful demonstration.

## Thinking Experiment

The weekday evaluator was also tested with:

    "think": True

Five trials were executed.

Observed result:

    5 / 5 correct

In this small experiment, enabling thinking improved observed weekday
correctness compared with the non-thinking samples.

However, latency increased dramatically.

Approximate agent durations were:

     60 seconds
    230 seconds
     80 seconds
    725 seconds
    167 seconds

The average was approximately:

    252 seconds

or:

    4.2 minutes per question

One trial required approximately twelve minutes.

Because this experiment contained only five trials, it does not establish that
thinking mode is perfectly reliable.

It does demonstrate a significant engineering trade-off:

    higher observed reasoning accuracy
                  |
                  v
           much higher latency

After the experiment, Tiny Agent was returned to:

    "think": False

This remains the Stage 13 baseline.

## Latency Observations

Stage 12's latency measurements become especially useful when combined with
Stage 13 evaluation.

During the complete suite, typical execution times were approximately:

    no_tool          0.4 - 0.5 seconds
    cpu_temperature  1.7 - 1.8 seconds
    system_info      3.1 seconds
    current_weekday  roughly 2 - 6 seconds

The no-tool case normally requires:

    1 LLM call
    0 tool calls

A normal tool-based case requires:

    2 LLM calls
    1 tool call

Conceptually:

    no-tool request

        user
          |
          v
        LLM
          |
          v
        answer


    tool-based request

        user
          |
          v
        LLM
          |
          v
        tool
          |
          v
        LLM
          |
          v
        answer

The weekday experiments also showed that longer execution time does not
necessarily imply a correct answer.

Some slower reasoning attempts were wrong while faster attempts were correct.

Latency alone is therefore not a measure of reasoning quality.

## Why Dynamic Expected Values Matter

Changing system values should not normally be hard-coded into an evaluator.

For example:

    expected_temperature = 38.0

would be fragile because the CPU temperature may change before the next run.

Instead, Stage 13 derives expected values from the tool observation generated
during that particular trial.

Conceptually:

    tool result
        |
        +--------> expected value
        |
        v
    model response
        |
        +--------> actual value

The evaluator then compares expected and actual behavior.

This pattern is used for the dynamic tool-based cases.

## Evaluation Is Not Regression Testing

Stage 13 asks:

    How well does this agent configuration behave?

The evaluator collects empirical evidence through repeated executions.

A result such as:

    3 / 5 correct

is useful information.

It does not necessarily mean that the evaluation process itself should terminate
with an error.

Regression testing serves a different purpose.

A regression test asks:

    Did behavior that we previously depended on stop working?

Regression tests normally define explicit expectations that can produce a
deterministic pass or fail signal for development workflows.

This distinction is important.

Stage 13 measures behavior.

Stage 14 will protect selected behavior from regression.

## Running Tiny Agent

From the Stage 13 directory:

    cd ~/tiny-agent-evolution/13-agent-evaluation

Build the image:

    docker compose build

Run Tiny Agent interactively:

    docker compose run --rm \
      -e OLLAMA_URL=http://192.168.15.30:11434/api/chat \
      tiny-agent

The interactive interface remains available even though `run_agent()` now
returns structured execution information internally.

## Running The Evaluation Suite

From:

    ~/tiny-agent-evolution/13-agent-evaluation

run:

    docker compose run --rm \
      -e OLLAMA_URL=http://192.168.15.30:11434/api/chat \
      -v "$PWD:/app" \
      tiny-agent \
      python eval.py

The bind mount exposes the current Stage 13 source files inside the container.

This is useful while developing the evaluator because changes to `eval.py` do
not require rebuilding the image before every run.

The suite executes every registered evaluation case and prints:

    individual trial results
    per-case summaries
    final overall summary

## Stage 13 Architecture

Tiny Agent has now evolved from a simple LLM call into an observable and
measurable agent.

Conceptually:

    User
      |
      v
    Tiny Agent
      |
      +----------------------+
      |                      |
      v                      v
    Ollama                 Tools
      |                      |
      +----------+-----------+
                 |
                 v
          Agent Execution
                 |
                 v
          Observability
                 |
          +------+------+
          |             |
          v             v
        Traces        Metrics
          |             |
          +------+------+
                 |
                 v
            Evaluation
                 |
        +--------+---------+
        |        |         |
        v        v         v
      tool     answer    repeated
     behavior  quality     trials

The observability work from Stages 09 through 12 now provides evidence that can
be consumed programmatically by the evaluator.

## Observability And Evaluation

The progression can now be summarized as:

    Stage 09
        |
        v
    What happened?

    Stage 10
        |
        v
    Which events belong to the same execution?

    Stage 11
        |
        v
    What happened during each tool invocation?

    Stage 12
        |
        v
    How long did the execution take?

    Stage 13
        |
        v
    Did the agent behave correctly?

This is why evaluation was introduced after observability rather than before
it.

A final answer by itself provides only the end result.

A trace provides evidence about how the agent reached that result.

## Key Lessons

Stage 13 demonstrates several important properties of agent systems.

### A Successful Tool Call Does Not Guarantee A Correct Answer

The weekday experiments repeatedly demonstrated this.

The tool returned the correct date, but the model sometimes derived the wrong
weekday.

### Tool Selection And Reasoning Are Separate Capabilities

Tiny Agent consistently selected `get_current_date_time` even when its final
weekday answer was incorrect.

### Repeated Trials Matter

A single successful demonstration can give a misleading impression of
reliability.

The weekday result varied substantially across small batches.

### Expected Values Should Follow The Observation

Dynamic values such as CPU temperature should be evaluated against the value
observed during the same execution.

### Not Using A Tool Is Also A Decision

The no-tool case explicitly evaluates whether the model can avoid unnecessary
tool calls.

### Relay And Reasoning Tasks Behave Differently

Relaying an observed value proved substantially more reliable than deriving a
new fact from an observation.

### Observability Makes Evaluation More Diagnostic

Instead of merely recording:

    wrong answer

we can distinguish:

    wrong tool
    failed tool
    correct observation
    incorrect reasoning
    incorrect final answer

### Accuracy Can Have A Performance Cost

The thinking experiment improved observed weekday accuracy in a small sample,
but latency increased dramatically.

Agent quality therefore cannot be represented by a single metric.

## What We Are Not Building Yet

Stage 13 intentionally does not introduce:

    pytest-based regression tests
    CI quality gates
    fixed reliability thresholds
    benchmark databases
    evaluation result persistence
    statistical confidence intervals
    semantic LLM judges
    external evaluation frameworks
    model comparison infrastructure
    dashboards

Those are separate concerns.

The purpose of this stage is to understand the mechanics and meaning of agent
evaluation before adding more infrastructure.

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


    ARC 2 — OBSERVABILITY AND QUALITY

    09  Event Logging
    10  Agent Traces
    11  Tool-Call Observability
    12  Latency and Metrics
    13  Agent Evaluation
    14  Regression Tests

Stage 13 establishes a basic behavioral evaluation layer.

Tiny Agent can now tell us not only what it did and how long it took, but also
whether selected aspects of its behavior matched our expectations.

## What Comes Next?

Evaluation revealed which behaviors are reliable and which are variable.

The next question is:

    Which behaviors should we protect from accidental regression?

That leads to:

    Stage 14 — Regression Tests

Stage 14 will convert selected stable expectations into automated checks while
keeping probabilistic evaluation separate from deterministic software
regression testing.
