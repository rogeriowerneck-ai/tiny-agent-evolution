# Stage 08 — Agent Behavior

Stage 07 gave our agent multiple tools.

The model could decide whether it needed a tool and which tool to use.

Stage 08 introduces explicit behavioral policy through a system prompt.

## Goal

Give Tiny Agent instructions about how it should behave.

The system prompt tells the agent to:

- use tools for current external information
- obtain fresh observations for changing information
- avoid inventing system information that tools can provide
- reuse conversation context when it is already sufficient

## System Message

The conversation now begins with:

    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }

The system message appears before user messages, assistant responses,
tool calls, and tool observations.

It provides policy that influences the model's decisions throughout the
conversation.

## Identity

The system prompt identifies the application as:

    Tiny Agent

When asked:

    Who are you?

the model now describes itself as Tiny Agent rather than simply identifying
itself as Qwen.

The underlying model is still qwen3:8b.

The system prompt defines the role the model plays inside our application.

## Fresh Information

We asked twice:

    What is the current CPU temp?

The model selected:

    get_cpu_temperature

both times.

The observations were:

    42.0 C

and later:

    40.5 C

The agent therefore followed our policy of obtaining fresh observations for
dynamic information.

## A Behavioral Failure

We also asked:

    What day is today?

The agent called:

    get_current_date_time

and correctly learned:

    September 30, 2026

We then asked:

    What day of the week is today?

The date was already present in the conversation, so the model had enough
information to derive the weekday.

However, it incorrectly claimed that it could not determine the day of the
week without additional information.

This is an important result.

## Instructions Do Not Guarantee Behavior

A system prompt influences model behavior.

It does not provide the same guarantees as deterministic program logic.

We can instruct:

    Use existing context when it already contains sufficient information.

and the model can still reason incorrectly.

Therefore:

    system prompt
        !=
    guaranteed behavior

Agent behavior must be observed and tested.

## Grounded Data and Generated Interpretation

The CPU tool returned:

    42.0 C

The model then described that temperature as:

    slightly above average

That interpretation did not come from the tool.

Likewise, after observing:

    40.5 C

the model described the temperature as being within a normal operating
range.

The response therefore contained two different kinds of information:

    grounded observation:
        CPU temperature = 42.0 C

    model-generated interpretation:
        "slightly above average"

Tool use does not automatically make every statement in an answer grounded.

## Deterministic Code and Model Behavior

Some parts of Tiny Agent have ordinary deterministic program semantics.

For example:

    function = TOOL_REGISTRY.get(function_name)

maps a name to a Python function.

Other parts depend on model behavior:

    Should I use a tool?

    Which tool should I use?

    Do I already have enough information?

    How should I interpret the observation?

These decisions can vary and can be wrong.

## What We Built

Across eight stages we evolved the project from a tiny Python program into
a tool-using agent.

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

Each stage introduced one major concept.

## Is This an Agent?

Yes.

Tiny Agent now has:

- an LLM
- conversation context
- external tools
- tool descriptions
- a tool registry
- model-selected actions
- observations
- an agent loop
- multiple capabilities
- behavioral policy

The model can reason about a request, choose an external action, observe the
result, and continue reasoning.

## What Comes Next?

Our Stage 08 experiment exposed two interesting failures:

- failure to derive the weekday from a known date
- unsupported interpretation of CPU temperature

As the system grows, manually reading terminal output will not be enough.

We need to answer questions such as:

    What exactly happened during an agent run?

    Which tools were selected?

    What observations did they return?

    How many LLM calls occurred?

    How long did each step take?

    Did the agent behave as expected?

These questions lead naturally to the next topics:

    observability

and:

    evaluation

The next evolution of Tiny Agent will focus not on adding more agency, but
on understanding and measuring the agent we have already built.
