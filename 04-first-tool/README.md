# Stage 04 — First Tool

Stage 03 gave our chatbot conversation context.

It can now remember previous messages while the application is running.

But it still cannot observe the environment in which the application runs.

Stage 04 introduces our first tool.

## Goal

Give the application a capability that obtains real information from its
environment.

We introduce:

    get_system_info()

The important restriction is:

    The LLM does NOT choose or execute this tool.

The user explicitly invokes it with:

    /system

This distinction is intentional.

## What is a tool?

At the simplest level, a tool is just code.

Our first tool is a Python function:

    def get_system_info():
        ...

It returns information about the environment where it executes.

There is no agent framework involved.

There is no special "AI tool" technology involved.

It is simply a Python function that provides a useful capability.

## Project structure

Stage 04 introduces a new file:

    04-first-tool/
    ├── app.py
    ├── tools.py
    ├── Dockerfile
    ├── docker-compose.yml
    └── README.md

The responsibilities are beginning to separate:

    app.py
        conversation and application control

    tools.py
        capabilities that interact with the environment

## The first tool

`get_system_info()` returns information such as:

    {
        "hostname": "...",
        "python_version": "...",
        "architecture": "aarch64",
        "system": "Linux"
    }

Because the function executes inside the container, it reports information
about the container environment.

In our test it returned:

    Python 3.12.14
    architecture: aarch64
    system: Linux

The hostname was the Docker container hostname.

## Manual tool invocation

The application recognizes:

    /system

and directly executes:

    get_system_info()

The flow is:

    User
      |
      | /system
      v
    Python
      |
      v
    get_system_info()
      |
      v
    real system information
      |
      v
    User

The LLM is not involved.

## Build

    docker compose build

## Run

    docker compose run --rm tiny-agent

## Experiment

First ask:

    What system are you running on?

The LLM cannot inspect the actual runtime.

It may describe itself or its model architecture instead.

Then run:

    /system

The application returns real information from the container.

Now ask again:

    What system are you running on?

The LLM still does not know.

## Why doesn't the LLM know?

The `/system` result is printed directly to the terminal.

It is not added to the conversation:

    messages[]

Therefore there are currently two independent paths:

                    Application
                 +---------------+
                 |               |
    User --------+--> LLM        |
                 |               |
    User /system +--> tools.py   |
                 |               |
                 +---------------+

The LLM path and the tool path do not meet.

## Capability is not agency

This stage demonstrates an important distinction.

Our application has gained a capability:

    get_system_info()

But the model cannot decide to use it.

The decision is still made explicitly by the human:

    /system

So:

    tool exists
        !=
    model can use tool

and:

    application has tools
        !=
    application is an agent

## Why separate tools.py?

At this stage we have only one tool, so putting it in another file may seem
unnecessary.

The separation becomes useful as capabilities grow.

Conceptually:

    app.py
      |
      +---- conversation
      +---- application control
      |
      v
    tools.py
      |
      +---- system information
      +---- future capabilities

Later, the model will be able to select capabilities from this tool layer.

## What we learned

A language model cannot automatically access Python functions merely because
those functions exist in the same application.

Something must connect:

    model decision
         |
         v
    Python function

Stage 04 does not provide that connection.

Instead:

    Human decision
         |
         v
    Python function

This gives us external capability without model agency.

## Is this an agent yet?

No.

The application has a tool, but the model cannot choose to use it.

The model still only performs:

    receive conversation
          |
          v
       generate text

It cannot decide:

    I need information from the environment.
          |
          v
    I should call get_system_info().

That is the next problem.

## Next

Stage 05 will introduce tools to the model itself.

We need to solve two separate problems:

    1. How does the model know which tools exist?

    2. How does a tool selected by the model map to an actual
       Python function?

This will introduce tool definitions and a tool registry.

The decision path will begin changing from:

    Human
      |
      v
    Tool

toward:

    User request
        |
        v
       LLM
        |
        | chooses a capability
        v
       Tool

That will bring us much closer to the agent boundary.
