# Stage 14 — Regression Tests

Stage 14 adds deterministic regression testing to Tiny Agent.

Previous stages made the agent observable and measurable.

Stage 13 then introduced behavioral evaluation:

    How well does this agent configuration behave?

Stage 14 asks a different question:

    Did behavior that we depend on stop working?

This stage uses pytest to protect selected deterministic properties of the
agent implementation.

The LLM itself is not used during these regression tests. Instead, the LLM
boundary is replaced with controlled responses so that the agent loop can be
tested deterministically.

---

## Goal

The goal of Stage 14 is to protect important Tiny Agent behavior from accidental
regression.

The regression suite verifies:

    direct responses without tool calls
    successful tool execution
    tool-event recording
    LLM call counts
    tool call counts
    tool results returned to the conversation
    unknown-tool handling
    exceptions raised by registered tools

A regression test has a binary result:

    PASS
    FAIL

A failure also produces a nonzero process exit code, making regression tests
suitable for automated development workflows.

---

## From Evaluation to Regression Testing

Stage 13 introduced repeated behavioral evaluation.

For example:

    run a case 5 times
        |
        v
    measure tool selection
        |
        v
    measure tool execution
        |
        v
    measure answer correctness
        |
        v
    report reliability

A result such as:

    4 / 5 correct

is useful evaluation information.

It describes how the agent behaved across repeated trials.

Regression testing has a different purpose.

A regression test defines an invariant:

    expected behavior
        |
        v
    run implementation
        |
        v
    compare with expectation
        |
        +---- match ----> PASS
        |
        +---- mismatch -> FAIL

If an invariant that previously held becomes false, the test suite should fail.

---

## Why The Live LLM Is Not Used

LLM behavior is probabilistic.

Even with the same prompt and configuration, generated behavior may vary.

A regression suite that directly depends on live model behavior could therefore
become flaky:

    same code
        |
        +---- run 1 -> PASS
        |
        +---- run 2 -> FAIL
        |
        +---- run 3 -> PASS

That would make it difficult to distinguish:

    implementation regression

from:

    normal model variation

Stage 14 therefore isolates the deterministic agent machinery from the
probabilistic LLM boundary.

The tests replace:

    chat()

with controlled test implementations.

This allows the tests to specify exactly what the simulated LLM returns.

The real `run_agent()` implementation still executes normally.

---

## pytest

Stage 14 introduces pytest.

The Docker image installs it with:

    RUN pip install --no-cache-dir pytest

The test suite lives in:

    test_agent.py

The Dockerfile also copies the test module into the image:

    COPY test_agent.py .

No production dependencies or application behavior are changed.

---

## monkeypatch

pytest's `monkeypatch` fixture allows tests to temporarily replace parts of the
running application.

For example:

    monkeypatch.setattr(app, "chat", fake_chat)

temporarily replaces the real Ollama-backed `chat()` function.

The test can then control the simulated LLM response.

Similarly:

    monkeypatch.setitem(
        app.TOOL_REGISTRY,
        "get_system_info",
        fake_system_info,
    )

temporarily replaces a registered tool.

These changes exist only for the duration of the test.

The production source code is not modified.

---

## Test 1 — Direct Response

The first regression test protects the simplest agent path.

The simulated LLM returns:

    Paris

without requesting a tool.

The expected execution is:

    user message
        |
        v
    fake LLM
        |
        v
    direct response
        |
        v
    run_agent() returns

The test verifies:

    response == "Paris"
    tool_events == []
    llm_call_count == 1
    tool_call_count == 0
    trace_id exists

This protects the no-tool completion path.

---

## Test 2 — Successful Tool Loop

The second test protects the central tool-using agent loop.

The first simulated LLM call requests:

    get_system_info

The tool registry contains a controlled test implementation returning:

    hostname
    Python version
    architecture
    operating system

The execution path becomes:

    LLM call 1
        |
        v
    request get_system_info
        |
        v
    execute tool
        |
        v
    record tool event
        |
        v
    append tool result
        |
        v
    LLM call 2
        |
        v
    final response

The test verifies:

    two LLM calls occurred
    one tool call occurred
    one tool event was recorded
    the correct tool was executed
    the tool execution succeeded
    the expected result was recorded
    the tool result was passed back into the conversation

This protects the core Tiny Agent execution loop.

---

## Test 3 — Unknown Tool

An LLM may request a tool that does not exist in the registry.

Tiny Agent handles this condition without crashing.

The implementation produces:

    {
        "error": "Unknown tool: nonexistent_tool"
    }

and records:

    success = False

The error is then passed back into the conversation so that the LLM can respond
appropriately.

The regression test verifies that this behavior remains intact.

This protects the missing-tool failure path.

---

## Test 4 — Tool Exception

A tool may exist in the registry but fail while executing.

The test installs a controlled tool that raises:

    RuntimeError("simulated tool failure")

Tiny Agent catches the exception and converts it into:

    {
        "error": "simulated tool failure"
    }

The tool event records:

    success = False

The agent then continues instead of crashing.

This protects the tool-exception boundary.

---

## Regression Suite

The Stage 14 regression suite contains four tests:

    test_no_tool_response
    test_tool_call_loop
    test_unknown_tool_fails_safely
    test_tool_exception_fails_safely

Together they protect the principal branches of `run_agent()`:

                        run_agent()
                            |
                +-----------+-----------+
                |                       |
            no tool call             tool call
                |                       |
                v                       v
          direct response          lookup tool
                                        |
                              +---------+---------+
                              |                   |
                            found              missing
                              |                   |
                              v                   v
                         execute tool          error result
                              |
                        +-----+-----+
                        |           |
                     success     exception
                        |           |
                        v           v
                   result event   error event

The suite is intentionally small.

The objective is not maximum test count.

The objective is to protect meaningful behavioral invariants.

---

## Running The Regression Suite

Build the Stage 14 image:

    cd ~/tiny-agent-evolution/14-regression-tests

    docker compose build

Run the regression tests:

    docker compose run --rm \
      tiny-agent \
      python -m pytest -v test_agent.py

A successful run produces:

    collected 4 items

    test_agent.py::test_no_tool_response PASSED
    test_agent.py::test_tool_call_loop PASSED
    test_agent.py::test_unknown_tool_fails_safely PASSED
    test_agent.py::test_tool_exception_fails_safely PASSED

    4 passed

The process exits with:

    0

---

## Exit Codes

Regression testing provides a machine-readable success signal.

When all tests pass:

    exit code 0

When at least one test fails:

    nonzero exit code

This property is important because it allows the suite to participate in future
automation such as:

    shell scripts
    pre-commit workflows
    CI pipelines
    deployment gates

Stage 14 does not build those systems yet.

It establishes the testing foundation they would depend on.

---

## Proving The Tests Detect A Regression

A test suite is useful only if it can detect broken behavior.

During Stage 14 development, a deliberate regression was introduced into a
temporary copy of `app.py`.

The normal success calculation:

    success = not (
        isinstance(result, dict)
        and "error" in result
    )

was temporarily replaced with:

    success = False

The production Stage 14 source file was not modified.

The same four regression tests were then executed against the deliberately
broken implementation.

The result was:

    test_no_tool_response PASSED
    test_tool_call_loop FAILED
    test_unknown_tool_fails_safely PASSED
    test_tool_exception_fails_safely PASSED

    1 failed, 3 passed

The process returned:

    exit code 1

The failure identified the violated invariant:

    assert tool_event["success"] is True

The test observed:

    False

This demonstrated that the suite could detect the specific regression.

---

## Why Only One Test Failed

The deliberate bug affected successful tool execution.

Therefore:

    test_tool_call_loop

failed.

The other tests exercised behavior that was not broken by the change.

This is desirable.

A useful regression suite should help localize failures rather than simply
produce a large number of unrelated failures.

The result demonstrated that the tests correspond to distinct behavioral
properties.

---

## Red And Green

The experiment produced two important states.

Normal implementation:

    4 passed
    exit code 0

Deliberately broken implementation:

    3 passed
    1 failed
    exit code 1

After removing the temporary broken implementation, the real Stage 14 code was
tested again:

    4 passed
    exit code 0

This is the basic regression-testing cycle:

    GREEN
      |
      v
    introduce or discover change
      |
      v
    RED
      |
      v
    identify violated invariant
      |
      v
    fix or restore behavior
      |
      v
    GREEN

---

## Production Code Remains Unchanged

A deliberate design choice in Stage 14 is that regression testing does not
require changing the agent implementation.

Compared with Stage 13:

    app.py              unchanged
    tools.py            unchanged
    eval.py             unchanged
    docker-compose.yml  unchanged

Stage 14 adds:

    pytest
    test_agent.py

and updates the Docker image so the tests can run inside the same environment.

This separation demonstrates an important engineering principle:

    testing behavior does not necessarily require changing behavior

---

## Evaluation And Regression Testing Together

Evaluation and regression testing solve complementary problems.

Stage 13 evaluation asks:

    How reliably does the complete agent behave?

It includes the real LLM and therefore observes probabilistic behavior.

Stage 14 regression testing asks:

    Does the deterministic agent machinery still satisfy selected invariants?

It isolates the LLM boundary and therefore produces deterministic results.

Together:

    live agent
        |
        +---- evaluation ------> behavioral quality
        |
        +---- regression ------> implementation stability

Neither replaces the other.

---

## What Regression Tests Protect

Regression tests are especially appropriate for deterministic properties such
as:

    data structures
    control flow
    error handling
    tool dispatch
    counters
    state transitions
    serialization
    contracts between components

These properties should behave consistently.

If they change unexpectedly, a regression test should fail.

---

## What Evaluation Still Protects

Evaluation remains appropriate for probabilistic properties such as:

    whether the LLM selects the correct tool
    whether the LLM interprets a tool result correctly
    whether an answer is semantically correct
    how often a reasoning task succeeds
    how model configuration affects reliability

Those questions cannot always be reduced to deterministic assertions.

That is why `eval.py` remains part of Stage 14.

---

## Stage 14 Architecture

The Stage 14 architecture now contains two quality paths:

    User / Evaluation Case
             |
             v
          app.py
             |
             +----------------------+
             |                      |
             v                      v
        real chat()            mocked chat()
             |                      |
             v                      v
           Ollama                 pytest
             |                      |
             v                      v
      behavioral evaluation   regression checks
             |                      |
             v                      v
          eval.py              test_agent.py

The same agent implementation supports both.

---

## Running Tiny Agent

The interactive application remains unchanged.

From the Stage 14 directory:

    cd ~/tiny-agent-evolution/14-regression-tests

    docker compose run --rm tiny-agent

The configured Ollama endpoint is read from the project environment.

---

## Running Behavioral Evaluation

Stage 13's evaluation capability remains available:

    docker compose run --rm \
      tiny-agent \
      python eval.py

This executes the live agent and measures its behavior across repeated trials.

---

## Running Regression Tests

The deterministic regression suite is:

    docker compose run --rm \
      tiny-agent \
      python -m pytest -v test_agent.py

Unlike the behavioral evaluator, this suite does not require successful LLM
inference because the LLM boundary is mocked.

---

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

The progression across Arc 2 is:

    What happened?
        |
        v
    Event Logging

    Which events belong together?
        |
        v
    Agent Traces

    What exactly happened during tool execution?
        |
        v
    Tool-Call Observability

    How expensive was the execution?
        |
        v
    Latency and Metrics

    Did the agent behave correctly?
        |
        v
    Agent Evaluation

    Did behavior we depend on stop working?
        |
        v
    Regression Tests

---

## Key Lessons

### Evaluation And Regression Testing Are Different

Evaluation measures behavior.

Regression testing protects invariants.

Both are necessary for different reasons.

### Deterministic Tests Need Controlled Boundaries

Replacing the probabilistic LLM boundary with a controlled fake makes the
agent machinery deterministic and testable.

### Test Behavior, Not Implementation Details

The tests focus on externally meaningful properties:

    response
    tool events
    call counts
    error handling
    conversation flow

They do not attempt to reproduce the internal implementation line by line.

### Failure Paths Deserve Tests

Correct behavior includes handling failures predictably.

Unknown tools and tool exceptions are therefore first-class regression cases.

### A Test Suite Should Prove It Can Fail

The deliberate regression experiment demonstrated that the suite detects broken
behavior and returns a nonzero exit code.

A permanently green test suite that cannot detect a meaningful defect provides
little protection.

### Small Suites Can Be Valuable

Four carefully selected tests protect the major branches of Tiny Agent's
execution loop.

Coverage should follow meaningful behavior rather than arbitrary test counts.

---

## What We Are Not Building

Stage 14 intentionally does not introduce:

    CI/CD pipelines
    GitHub Actions
    coverage thresholds
    large fixture frameworks
    benchmark databases
    semantic LLM judges
    external evaluation platforms
    deployment gates
    extensive integration-test infrastructure

Those are natural extensions of the foundation built here, but they are not
required to understand regression testing itself.

---

## Completion

Stage 14 completes the original Tiny Agent evolution sequence.

Tiny Agent began as a Python process running inside a container.

It gradually acquired:

    conversation with an LLM
    conversation context
    tools
    a tool registry
    an agent loop
    multiple tools
    explicit agent behavior
    structured event logging
    trace identifiers
    tool-call observability
    latency metrics
    behavioral evaluation
    deterministic regression tests

The project now contains both:

    an executable agent

and:

    the engineering mechanisms needed to observe, evaluate, and protect it

This provides a foundation for future work without requiring that future work
continue the numbered tutorial sequence.

Possible next directions include:

    persistent memory
    richer tools
    structured APIs
    planning
    retrieval-augmented generation
    MCP integration
    external services
    CI automation
    model comparison
    more advanced evaluation

Those can now be approached as product or architecture decisions rather than
missing fundamentals.
