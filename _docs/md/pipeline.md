# Satori Pipeline Framework Documentation

## Pipeline Runtime Framework

Satori defines a unified structure for executing pipelines asynchronously and communicating through `ptgctl` streams.

### Pipeline Design Rationale

Each pipeline encapsulates a single type of computation. To avoid unnecessary recomputation, each pipeline separates:

- **Input Streams**: Updated continuously
- **Trigger Streams**: Cause the pipeline logic to run

This distinction ensures that pipelines are reactive but not wastefully busy, a key principle for stream-driven AR systems. By limiting the triggers, pipelines avoid re-executing on every update, enabling lightweight and efficient stream handling.

Pipelines operate as self-contained, reactive microservices that publish and subscribe to named data streams. Their design emphasizes isolation and composability—any pipeline can be developed and tested independently.

### Pipeline Server

The `PipelineServer` is the runtime manager responsible for starting and managing multiple pipelines concurrently. It abstracts away stream subscriptions, triggering logic, and asynchronous execution.

Its primary roles include:

- **Initialization**: Launches and configures each registered pipeline
- **Coordination**: Monitors all trigger streams and invokes the correct pipeline logic
- **Execution Management**: Runs all pipelines in parallel, each with its own async loop

This server provides the infrastructure to deploy a full system composed of multiple reasoning and presentation pipelines, making it scalable and extensible.

---

# GPT Prompt for Documentation Generation

You are assisting with documenting and refactoring an open-source AR assistant framework called Satori. The system uses ptgctl streams and has multiple independently running pipelines, each triggered by certain input/trigger streams and writing to output streams. The core runtime components are:

- A `BasePipeline` class defining the processing interface
- A `PipelineServer` class that runs all registered pipelines asynchronously

Write clean documentation (without code) that:
- Explains the role and rationale of the pipeline model
- Explains the role of the Pipeline Server as an orchestrator
- Describes the separation of input/trigger/output streams and how it improves responsiveness and efficiency
- Frames how this structure supports building modular AR agents using multiple interacting pipelines

