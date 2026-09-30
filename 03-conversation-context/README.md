# Stage 03 — Conversation Context

Stage 02 gave us a working LLM chatbot.

But every request was independent.

If we said:

    My name is Rogerio.

and then asked:

    What is my name?

the model could not answer because the previous message was not included in
the new request.

Stage 03 fixes that problem.

## Goal

Preserve the conversation while the application is running and send that
conversation back to the LLM with every request.

We are introducing:

- conversation state
- user messages
- assistant messages
- multi-turn context

We are still not introducing:

- persistent memory
- tools
- environment access
- tool selection
- an agent loop

## The key change

Stage 02 effectively sent this for every request:

    messages = [
        {
            "role": "user",
            "content": current_message
        }
    ]

Previous messages were discarded.

Stage 03 creates one message list:

    messages = []

and keeps adding conversation turns to it.

After a short conversation it might contain:

    [
        {
            "role": "user",
            "content": "My name is Rogerio"
        },
        {
            "role": "assistant",
            "content": "Hello, Rogerio!"
        },
        {
            "role": "user",
            "content": "What is my name?"
        }
    ]

The entire list is sent to the LLM.

## Architecture

    User
      |
      v
    messages[]
      |
      v
    LLM
      |
      v
    Assistant response
      |
      v
    messages[]
      |
      +------> next interaction

Both sides of the conversation become part of the context.

## Why store assistant messages too?

Conversation history is not only a record of what the user said.

The model also needs to know what it previously answered.

A conversation therefore normally alternates roles:

    user
      |
    assistant
      |
    user
      |
    assistant
      |
     ...

This gives the model the dialogue that led to the current question.

## Build

    docker compose build

## Run

    docker compose run --rm tiny-agent

## Experiment

Try:

    You: My name is Rogerio.

    You: Who am I?

    You: What is my name?

    You: What did I first tell you?

Unlike Stage 02, the model can now use previous conversation turns.

In our test it correctly recalled both the name and the first message.

## Where is the conversation stored?

Right here:

    messages = []

This is just a Python list in the running process.

There is no database.

There is no vector store.

There is no external memory service.

There is no hidden conversation store.

The application is maintaining the context.

## Context is not persistent memory

Now exit:

    You: exit

and start the application again:

    docker compose run --rm tiny-agent

Then ask:

    What is my name?

The model no longer knows.

Why?

The old Python process ended.

Its `messages` list disappeared with it.

The new process starts with:

    messages = []

again.

So:

    Running process
          |
          v
      messages[]
          |
          v
    conversation context

but:

    process exits
          |
          v
      messages[] gone

This is an important distinction:

    conversation context != persistent memory

Stage 03 gives us conversational state only for the lifetime of the
application.

## Error handling and conversation consistency

Before calling the LLM, the current user message is added to the history.

If the LLM request fails, the application executes:

    messages.pop()

This removes that message again.

Otherwise we could create a conversation history containing a user message
for which no assistant response ever occurred.

## A new consequence

Our application now sends increasingly large requests.

At the beginning:

    1 message

Later:

    10 messages

Later still:

    100 messages

The complete conversation cannot grow forever without consequences.

Long conversations consume more context and require more processing.

We are not solving that problem yet.

For now, keeping the complete conversation makes the mechanism easy to
understand.

## What we learned

The model did not suddenly acquire memory.

The application changed what information it sends to the model.

Stage 02:

    current message
          |
          v
         LLM

Stage 03:

    conversation so far
          |
          v
         LLM

The apparent memory comes from supplying previous messages as context.

## Is this an agent yet?

No.

We now have a stateful chatbot.

It can reason over the current conversation, but it still cannot interact
with the world outside that conversation.

If we ask:

    What system are you running on?

the model still cannot inspect the actual container or Jetson Nano.

There is currently a boundary:

    Conversation
         |
         v
        LLM
         |
         X
         |
    Environment

## Next

We now have:

    runtime
       +
    LLM
       +
    conversation context

The next limitation is environment awareness.

In Stage 04 we will introduce the first tool and allow the model-driven
application to obtain real information from the system on which it runs.

That will be our first step from merely generating text toward taking
actions and observing the outside world.
