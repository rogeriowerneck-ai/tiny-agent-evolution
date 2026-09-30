# Stage 01 — Container Runtime

The first step in building Tiny Agent is not the LLM.

It is creating a predictable environment in which our application can run.

## Goal

Run a simple Python 3.12 application inside Docker on the Jetson Nano.

At this stage there is:

- no LLM
- no chat
- no tools
- no agent loop
- no external API

We are only preparing the runtime.

## Why use a container?

The Jetson Nano used for this project runs an older operating system with
Python 3.6.9 installed on the host.

Our application, however, will use Python 3.12.

Instead of modifying the Nano's system Python, Docker gives the application
its own isolated and reproducible runtime.

The architecture at this stage is:

    Jetson Nano
        |
        v
      Docker
        |
        v
    python:3.12-slim
        |
        v
      app.py

The host and container therefore have different Python environments:

    Host                     Container
    -------------------      -------------------
    Python 3.6.9             Python 3.12
    aarch64                  aarch64
    Ubuntu 18.04             isolated Linux runtime

## Files

    01-container/
    ├── app.py
    ├── Dockerfile
    ├── docker-compose.yml
    └── README.md

### app.py

A minimal Python program that prints information about its runtime
environment.

### Dockerfile

Defines the application image using `python:3.12-slim`.

### docker-compose.yml

Provides a simple way to build and run the application.

## Build

From this directory:

    docker compose build

## Run

    docker compose run --rm tiny-agent

Expected output will look similar to:

    Tiny Agent environment is ready!
    Python: 3.12.x
    Architecture: aarch64
    System: Linux

## What we learned

The application does not need to use the Python installation provided by
the host operating system.

Docker gives Tiny Agent its own runtime while still using the Nano's
underlying ARM64 hardware.

This also makes the application easier to reproduce on another compatible
machine.

## Is this an agent yet?

No.

At this stage we have only created the environment in which Tiny Agent will
eventually run.

There is no language model and no agent behavior.

## Next

In Stage 02 we will connect this Python application to an LLM and turn it
into a simple interactive chat application.

That will give us:

    User
      |
      v
    Python application
      |
      v
    LLM
      |
      v
    Response

It still will not be an agent.

That distinction will become important as the project evolves.
