# Tiny Agent Evolution

A small educational project that builds an AI agent from first principles,
one concept at a time.

The goal is not to build the most capable agent possible.

The goal is to understand what makes an agent an agent.

Instead of starting with an agent framework, this project begins with a
minimal Python program and gradually introduces:

- an LLM
- conversation context
- tools
- tool descriptions
- tool selection
- observations
- an agent loop
- multiple capabilities
- behavioral policy

Each stage is intentionally small and can be compared with the previous
stage.

## Why This Project Exists

Agent frameworks can make powerful systems surprisingly easy to build.

That convenience can also hide important mechanics.

Tiny Agent Evolution takes the opposite approach.

We build the important pieces ourselves so that concepts such as tool
calling, observations, context, orchestration, and agent behavior remain
visible.

The project intentionally avoids agent frameworks such as LangChain or
LlamaIndex.

The core implementation uses Python's standard library and Ollama's HTTP
API.

## Arc 1 — Building an Agent

The first arc evolves a tiny Python program into a minimal tool-using
agent.

    01  Container Runtime
            |
            v
    02  Simple Chat
            |
            v
    03  Conversation Context
            |
            v
    04  First Tool
            |
            v
    05  Tool Registry
            |
            v
    06  Agent Loop
            |
            v
    07  Multiple Tools
            |
            v
    08  Agent Behavior

### 01 — Container

Establishes a reproducible Python runtime using Docker.

There is no LLM and no agent yet.

### 02 — Simple Chat

Connects the Python application to an LLM through Ollama's HTTP API.

Each message is independent.

### 03 — Conversation Context

Introduces a message history.

The model can now reason about earlier turns in the same process.

### 04 — First Tool

Introduces an external Python capability.

The application can call the tool, but the model cannot select it.

### 05 — Tool Registry

Describes tools to the model and maps tool names to Python functions.

The model can now choose a tool.

The tool result is not yet returned to the model.

### 06 — Agent Loop

Closes the loop:

    reason
      |
      v
     act
      |
      v
    observe
      |
      v
    reason

Tool observations are returned to the model so it can continue reasoning
and produce a grounded answer.

This is the first stage we consider a minimal tool-using agent.

### 07 — Multiple Tools

Adds multiple capabilities:

- system information
- CPU temperature
- current date and time

The model must now decide both whether a tool is necessary and which tool
is appropriate.

### 08 — Agent Behavior

Introduces a system prompt containing behavioral policy.

The agent receives instructions about when to use tools, when to obtain
fresh observations, and when existing context may be sufficient.

This stage also demonstrates an important lesson:

    instructions do not guarantee behavior

LLM decisions still need to be observed and evaluated.

## Architecture

By Stage 08, Tiny Agent has three important layers:

                         Tiny Agent

              +-------------+-------------+
              |             |             |
              v             v             v

           POLICY      ORCHESTRATION   CAPABILITIES

        system prompt    agent loop       tools
                              |
                              v
                       tool registry

The model participates in the orchestration by deciding whether and how to
use the capabilities available to it.

## Requirements

You need:

- Docker
- Docker Compose
- an Ollama server reachable from the container
- a tool-capable model

The project currently uses:

    qwen3:8b

by default.

Other Ollama models may work if they support the required tool-calling
behavior.

## Configuration

Copy the example environment file:

    cp .env.example .env

Edit `.env` and configure the Ollama endpoint reachable from your Docker
container.

For example:

    OLLAMA_URL=http://YOUR_OLLAMA_HOST:11434/api/chat
    OLLAMA_MODEL=qwen3:8b

`OLLAMA_URL` can point to an Ollama server on the local network or to another
Tailscale node using its MagicDNS hostname. Starting with stage 10, the
Docker Compose configuration uses Tailscale's `100.100.100.100` DNS resolver
so MagicDNS hostnames can be resolved from inside the Tiny Agent container.

The `.env` file contains local configuration and is intentionally excluded
from Git.

## Running a Stage

Each stage is an independent Docker Compose project.

For example:

    cd 08-agent-behavior

    docker compose build
    docker compose run --rm tiny-agent

Then interact with Tiny Agent:

    You: What Python version are you running?

    Model selected tool: get_system_info

    Assistant: I am running Python version 3.12.14.

The exact output may vary because responses and tool-selection behavior are
generated by an LLM.

## Reading the Project

The stages are intended to be read in order.

A useful way to study the evolution is to compare neighboring stages:

    diff -u 05-tool-registry/app.py 06-agent-loop/app.py

or:

    diff -u 06-agent-loop/tools.py 07-multiple-tools/tools.py

Some stages deliberately change only one architectural layer.

For example:

    Stage 06
        changes orchestration

    Stage 07
        changes capabilities

    Stage 08
        changes policy

This separation is intentional.

## What Is an Agent?

There is no single universally accepted boundary between a chatbot and an
agent.

For this project, the important transition occurs when the model can:

1. interpret a goal
2. decide that an external action is required
3. select that action
4. observe the result
5. continue reasoning
6. produce an answer

In this progression, that loop first appears in Stage 06.

## What This Project Is Not

Tiny Agent Evolution is not intended to be:

- a production agent framework
- a replacement for established orchestration libraries
- a secure sandbox for arbitrary tools
- a production-ready AI service

The deliberately small implementation exists to make agent mechanics easy
to inspect.

## Next — Observability and Evaluation

Arc 1 answers:

    How do we build an agent?

The next arc will ask:

    How do we understand what the agent actually did?

and:

    How do we know whether it behaved correctly?

Future stages will explore concepts such as:

- structured events
- agent traces
- timing and latency
- tool-call visibility
- evaluations
- regression tests

The goal is to evolve Tiny Agent from something we can merely run into
something we can systematically observe and measure.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
