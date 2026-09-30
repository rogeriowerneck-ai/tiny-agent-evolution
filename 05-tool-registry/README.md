# Stage 05 — Tool Registry

Stage 04 introduced our first external capability:

    get_system_info()

But the human had to explicitly invoke it using:

    /system

The language model did not know that the tool existed.

Stage 05 changes that.

For the first time, the model can decide that it needs a tool.

## Goal

Allow the LLM to:

1. know which tools are available
2. decide when a tool is useful
3. request a tool by name

Then allow Python to map that name to an actual function and execute it.

We are introducing:

- tool definitions
- model tool selection
- a tool registry
- tool dispatch

We are deliberately NOT yet returning the tool result to the model.

That missing step will motivate the agent loop in Stage 06.

## Two representations of a tool

Our application now has:

    TOOL_DEFINITIONS

and:

    TOOL_REGISTRY

They solve different problems.

### TOOL_DEFINITIONS

The tool definitions are sent to the LLM.

They describe capabilities such as:

    name: get_system_info

    description:
        Get information about the system where the application
        is currently running.

This allows the model to reason:

    The user is asking about the runtime environment.

    I have a tool called get_system_info.

    That tool appears relevant.

    I should request it.

The definition describes the capability.

It does not execute anything.

### TOOL_REGISTRY

Python also needs to know how a tool name maps to executable code.

The registry provides that mapping:

    TOOL_REGISTRY = {
        "get_system_info": get_system_info,
    }

Conceptually:

    model produces:

        "get_system_info"

              |
              v

        TOOL_REGISTRY

              |
              v

        Python function

              |
              v

        get_system_info()

## Architecture

The interaction now looks like:

    User
      |
      v
     LLM
      |
      | selects tool
      v
    "get_system_info"
      |
      v
    TOOL_REGISTRY
      |
      v
    get_system_info()
      |
      v
    real system information

For the first time, the model rather than the human selects the capability.

## Tool definitions in the LLM request

The Ollama request now contains:

    {
        "model": MODEL,
        "messages": messages,
        "tools": TOOL_DEFINITIONS,
        "stream": false
    }

The important addition is:

    "tools": TOOL_DEFINITIONS

This tells the model which external capabilities the application makes
available.

## Tool calls

The model may return an ordinary assistant message.

For example:

    You: What is 2 + 2?

    Assistant: 4

But it may instead return a structured tool request.

Our application checks:

    tool_calls = assistant_message.get("tool_calls", [])

If a tool was requested, it extracts:

    function_name = tool_call["function"]["name"]

and looks it up:

    function = TOOL_REGISTRY.get(function_name)

Then Python executes the function.

## Experiment

Ordinary questions still produce ordinary model responses:

    You: What is 2 + 2?

    Assistant: 4

But environment questions behave differently:

    You: What system is this application running on?

The model selected:

    get_system_info

without the user explicitly naming the tool.

Our test produced:

    Model selected tool: get_system_info

    Tool result:
    {
        "hostname": "c3363592fd09",
        "python_version": "3.12.14",
        "architecture": "aarch64",
        "system": "Linux"
    }

The same happened when we asked:

    What Python version is this application running?

Again, the model selected:

    get_system_info

This demonstrates that the model can match a user request with the
description of an available capability.

## Stage 04 versus Stage 05

Stage 04:

    Human
      |
      | /system
      v
    Tool

The human selected the capability.

Stage 05:

    User question
         |
         v
        LLM
         |
         | chooses
         v
        Tool

The model selects the capability.

This is an important transition toward agency.

## But something is still missing

The tool result is currently printed by Python:

    result = function()

    print(json.dumps(result, indent=2))

But it is not returned to the model.

The flow therefore stops here:

    User
      |
      v
     LLM
      |
      | tool request
      v
     Tool
      |
      v
    Observation
      |
      X
      |
     LLM

The application knows the result.

The terminal displays the result.

But the model never gets to reason about the observation.

For example, the tool may return:

    {
        "python_version": "3.12.14"
    }

but the model never receives that information and therefore cannot use it
to formulate a final answer.

## Tool selection is not tool reasoning

Stage 05 demonstrates another important distinction.

The model can now decide:

    I need get_system_info().

But it cannot yet perform:

    I need get_system_info().
              |
              v
          execute tool
              |
              v
        observe result
              |
              v
    Python is version 3.12.14.
              |
              v
       answer the user

The observation needs to become part of the model's context.

## Is this an agent yet?

We are much closer, but the control loop is incomplete.

The model can choose an action, and the application can execute it.

But the model cannot observe the result and decide what to do next.

We currently have:

    reason
      |
      v
     act
      |
      v
    observe
      |
      X

The loop stops after observation.

## Next

Stage 06 will connect the observation back to the model.

The application will:

    1. send the conversation to the LLM
    2. receive a tool request
    3. execute the tool
    4. add the tool result to the conversation
    5. call the LLM again
    6. allow the model to reason over the result

The flow will become:

    User
      |
      v
     LLM
      |
      | action
      v
     Tool
      |
      | observation
      v
     LLM
      |
      | reason again
      v
    Answer

Or, more generally:

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
      |
      v
     ...

That is the agent loop.
