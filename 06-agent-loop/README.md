# Stage 06 — Agent Loop

Stage 05 allowed the language model to select a tool.

The model could decide:

    I need get_system_info().

Python could then execute that function.

But the process stopped after the tool returned its result.

The model never received the observation and therefore could not reason
about it.

Stage 06 closes that loop.

## Goal

Allow the model to:

1. reason about a user request
2. select a tool when needed
3. receive the tool result
4. reason about that observation
5. continue until it can answer

This creates our first minimal tool-using agent.

## The missing connection

Stage 05 looked like:

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

Stage 06 connects the observation back to the model:

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
      v
    Answer

## The agent loop

The central change is:

    while True:

The application repeatedly asks the model what to do.

Conceptually:

              +---------------------------+
              |                           |
              v                           |
             LLM                          |
              |                           |
              v                           |
        tool requested?                   |
           /       \                      |
         no         yes                   |
         |           |                    |
         v           v                    |
       answer       execute tool          |
         |           |                    |
         v           v                    |
       return      observation -----------+

The loop ends only when the model produces an ordinary response instead of
requesting another tool.

## run_agent()

The orchestration now lives in:

    run_agent(messages)

Its job is not to answer the user's question itself.

Instead, it coordinates the interaction between:

    conversation
         |
         v
        LLM
         |
         v
       tools

The language model makes decisions.

Python performs the requested operations.

## Actions

When the model requests:

    get_system_info

the application looks up the function in:

    TOOL_REGISTRY

and executes it.

This is the action step:

    reason
      |
      v
     act

## Observations

The result of the tool is converted to JSON and added to the conversation:

    messages.append(
        {
            "role": "tool",
            "content": json.dumps(result),
        }
    )

This is the critical change from Stage 05.

The tool result is no longer merely printed to the terminal.

It becomes part of the model's context.

The model can now observe the result of its action.

## Preserving the tool request

The assistant message containing the tool request is also stored:

    messages.append(assistant_message)

This preserves the sequence:

    user request
         |
         v
    assistant tool request
         |
         v
    tool observation
         |
         v
    assistant response

The conversation now contains more than human and assistant text.

It also records actions and observations.

## Experiment

We asked:

    What system is this app running on?

The model selected:

    get_system_info

The tool returned:

    {
        "hostname": "d45cb53756f4",
        "python_version": "3.12.14",
        "architecture": "aarch64",
        "system": "Linux"
    }

Unlike Stage 05, execution did not stop there.

The observation was added to the conversation and the model was called
again.

It then answered using the real tool result.

## Reusing observations

We then asked:

    What architecture are you running on?

The model answered:

    aarch64

without requesting the tool again.

This happened because the previous tool observation was still present in
the conversation history.

The model already had the information it needed.

The flow was therefore:

    previous tool observation
              |
              v
         messages[]
              |
              v
             LLM
              |
              v
            answer

rather than:

    LLM -> tool -> LLM

This demonstrates that an agent does not need to invoke a tool for every
question.

Tool use is conditional on what information is already available.

## Reason, act, observe

We can now describe the core cycle as:

    REASON
       |
       v
      ACT
       |
       v
    OBSERVE
       |
       v
    REASON
       |
       v
      ...

For our current example:

    "What system is this app running on?"
                    |
                    v
       model determines that real
       system information is needed
                    |
                    v
          get_system_info()
                    |
                    v
       Linux / aarch64 / Python 3.12
                    |
                    v
       model interprets observation
                    |
                    v
             final answer

## Why use a loop?

With one tool it might seem sufficient to:

    call model
    call tool
    call model again

But that assumes exactly one action.

An agent may eventually need:

    model
      |
      v
    tool A
      |
      v
    model
      |
      v
    tool B
      |
      v
    model
      |
      v
    answer

The loop allows the model to continue acting until it has enough
information to respond.

## Is this an agent yet?

Yes, in a minimal but meaningful sense.

The system now has:

- an LLM that reasons about requests
- external capabilities
- model-selected actions
- tool execution
- observations returned to the model
- a control loop that continues until an answer is produced

The model is no longer limited to generating text from the user's original
prompt.

It can choose an action, observe its result, and continue reasoning.

## What is still limited?

Our agent currently has only one tool:

    get_system_info

That makes tool selection trivial.

If external information is required, there is only one available
capability.

We therefore have not yet demonstrated meaningful selection among different
actions.

## Next

Stage 07 will give the agent multiple tools.

Instead of deciding only:

    Should I use the tool?

the model will need to decide:

    Do I need a tool?

and, if so:

    Which tool should I use?

The architecture becomes:

                       +--> system information
                       |
    User --> LLM ------+--> CPU temperature
                       |
                       +--> date and time

This will make tool descriptions and tool selection substantially more
important.
