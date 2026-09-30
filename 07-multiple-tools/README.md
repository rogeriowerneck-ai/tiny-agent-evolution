# Stage 07 — Multiple Tools

Stage 06 created our first minimal tool-using agent.

The model could:

    reason
      |
      v
    select a tool
      |
      v
    observe the result
      |
      v
    reason again

But there was only one available tool:

    get_system_info()

Tool selection was therefore trivial.

Stage 07 gives the agent multiple capabilities.

## Goal

Allow the model to choose among different tools according to the user's
request.

The available tools are:

    get_system_info()
    get_cpu_temperature()
    get_current_date_time()

The agent must now decide both:

    Do I need a tool?

and:

    Which tool do I need?

## Available capabilities

### get_system_info

Returns information about the runtime environment:

    hostname
    Python version
    architecture
    operating system

### get_cpu_temperature

Reads:

    /sys/class/thermal/thermal_zone0/temp

and returns the current CPU temperature.

For example:

    {
        "temperature_celsius": 40.5
    }

### get_current_date_time

Returns the current date and time using UTC-03:00.

For example:

    {
        "datetime": "2026-09-30T16:12:06.647762-03:00",
        "timezone": "UTC-03:00"
    }

## Tool selection

The model receives descriptions of all available capabilities.

It can therefore match the user's intent with an appropriate tool.

Conceptually:

                         +--> get_system_info
                         |
    User --> LLM --------+--> get_cpu_temperature
                         |
                         +--> get_current_date_time
                         |
                         +--> no tool

The final option is important.

Having tools available does not mean every request should use one.

## Experiment — no tool required

We asked:

    What is 10 * 7?

The model answered:

    70

No tool was selected.

The model already had everything required to answer the question.

## Experiment — selecting the temperature tool

We asked:

    What is the CPU temp right now?

The model selected:

    get_cpu_temperature

The tool returned:

    {
        "temperature_celsius": 40.5
    }

The model then answered using that observation.

## Experiment — selecting the system tool

We asked:

    What operating system are you running on?

The model selected:

    get_system_info

The observation contained:

    {
        "hostname": "262d3b93f66e",
        "python_version": "3.12.14",
        "architecture": "aarch64",
        "system": "Linux"
    }

The model used that result to answer that the application was running on
Linux.

## Fresh observations

We then asked again:

    What is the CPU temp right now?

The previous temperature observation was still present in the conversation.

Nevertheless, the model selected:

    get_cpu_temperature

again.

This is useful behavior because CPU temperature is dynamic.

An earlier measurement does not necessarily represent the current state.

The phrase:

    right now

gave the model a reason to obtain a fresh observation.

## Reusing an observation

We asked:

    What day is today?

The model selected:

    get_current_date_time

and received:

    2026-09-30

We then asked:

    What day of the week is today?

This time the model did not call the tool again.

It already had the current date in its context.

It reasoned from that existing observation and answered:

    Wednesday

This demonstrates an important property of the agent loop.

Tools provide observations.

Those observations become part of the conversation and can support later
reasoning.

## Freshness depends on the information

Compare these interactions:

    CPU temperature right now
              |
              v
        call tool again

with:

    What day of the week is today?
              |
              v
       reuse known date

The model treated the two pieces of information differently.

CPU temperature can change quickly.

The calendar date was already known and sufficient to derive the requested
answer.

We have not explicitly programmed this behavior.

The model inferred it from the request, the tool descriptions, and the
conversation context.

## The agent loop did not change

An important architectural result of this stage is that `app.py` did not
need to know the details of the new capabilities.

Stage 06 already provided a generic loop:

    model
      |
      v
    tool call
      |
      v
    registry lookup
      |
      v
    execution
      |
      v
    observation
      |
      v
    model

Stage 07 primarily expands:

    TOOL_DEFINITIONS

and:

    TOOL_REGISTRY

This separation lets us add capabilities without redesigning the agent
loop.

## Tool descriptions matter

The model does not inspect the Python implementation to understand what a
tool does.

It sees the tool definition.

For example:

    get_cpu_temperature

is described as obtaining the current CPU temperature.

The description helps the model decide when that capability is relevant.

As the number of tools grows, clear tool names and descriptions become
increasingly important.

## Tools expose different layers

Our tools also demonstrate different kinds of external information.

`get_system_info()` observes aspects of the container runtime:

    Python 3.12.14
    aarch64
    Linux
    container hostname

`get_cpu_temperature()` reads a kernel interface that exposes information
about the underlying Nano hardware.

`get_current_date_time()` observes the application's current clock.

A tool therefore represents a capability boundary, not necessarily one
particular kind of resource.

Future tools could access:

    files
    databases
    APIs
    sensors
    devices
    network services
    other applications

The agent loop does not fundamentally need to change.

## Is this an agent?

Yes.

The system can now:

- interpret a user request
- decide whether external information is required
- select among multiple capabilities
- execute the selected capability
- observe its result
- reason about that observation
- continue until it can answer

The model is making meaningful choices among possible actions.

## What is still missing?

Most of the agent's behavior currently emerges from:

- the user's request
- the conversation
- tool names
- tool descriptions
- the model's general reasoning

We have not explicitly told the agent how it should behave.

For example, we have not specified rules such as:

    Use tools for questions about current system state.

    Obtain fresh information for dynamic values.

    Check the current date before answering relative date questions.

These are behavioral policies.

## Next

Stage 08 introduces a system prompt.

But its purpose will not simply be to give the chatbot a personality.

The system prompt will define behavior and decision policy.

The architecture becomes:

             System instructions
                    |
                    v
    User ---------> LLM
                    |
                    v
              decide what to do
                 /       \
                /         \
             answer       tool
                           |
                           v
                       observation
                           |
                           +----> LLM

This will complete the first evolution from a minimal Python program to
Tiny Agent.
