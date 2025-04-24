# Satori Development Guide

## Overview
Satori is a modular AR task guidance framework that enables researchers and developers to build proactive, multimodal agents using a stream-driven architecture. It communicates with AR headsets using `ptgctl` streams and organizes intelligence into independent pipelines, each performing a specific reasoning task. An agent consists of a set of such pipelines, coordinated via asynchronous data streams.

## Key Concepts

### 1. Streams
Satori uses `ptgctl` streams as the communication backbone. A stream is a named data channel (e.g., `frame`, `belief`, `desire`, `image`) that carries input, output, or intermediate results.

- **Input Streams**: Carry contextual updates (e.g., camera frames).
- **Trigger Streams**: Trigger pipeline execution.
- **Output Streams**: Store results consumed by other pipelines or the AR headset.

### 2. Pipelines
A **Pipeline** is an atomic, self-contained processing unit that:
- Listens to one or more `input` and `trigger` streams.
- Performs a specific function (e.g., belief inference, desire prediction).
- Writes results to a designated output stream.

Each pipeline runs independently and communicates only via streams. Pipelines are designed to be reusable and composable.

### 3. Agent
An **Agent** is a collection of pipelines working together to form a coherent AR assistant. The agent does not perform reasoning itself but manages the lifecycle of pipelines and orchestrates their deployment.

### 4. Agent Assembly Methods
Satori supports two modes for building agents:

#### A. Config-Based
A YAML config lists all pipeline modules:
```yaml
agent:
  name: coffee_assistant
  pipelines:
    - satori.pipelines.belief_pipeline.BeliefPipeline
    - satori.pipelines.desire_pipeline.DesirePipeline
    - satori.pipelines.guidance_pipeline.GuidancePipeline
```
This is interpreted by a factory loader to instantiate an `Agent`.

#### B. API-Based
Developers can programmatically assemble an agent:
```python
from satori.agent import Agent
from satori.pipelines import BeliefPipeline, DesirePipeline

agent = Agent([
    BeliefPipeline(),
    DesirePipeline(),
])
agent.run()
```

Both methods are compatible and interchangeable.

## Layered Architecture

1. **Runtime Layer**
   - Handles communication via `ptgctl`
   - Provides base classes for stream-triggered pipelines
   
2. **Pipeline Layer**
   - Contains logic for reasoning modules (e.g., belief, desire, intention)
   - Includes utility pipelines (e.g., GPT communication, image generation)

3. **Agent Layer**
   - Assembles pipelines into a working system
   - Supports YAML config or programmatic API

## Modularity Rationale
- **Separation of concerns**: Each pipeline handles one type of reasoning.
- **Parallelism**: Pipelines run independently and asynchronously.
- **Flexibility**: Users can swap pipelines, modify logic, or build custom agents.
- **Reusability**: Pipelines can be reused across tasks or agents.

## Deployment & Usage
- Pipelines are instantiated and managed by the `Agent` runtime.
- AR headsets read output streams for rendering guidance.
- Satori supports local testing, Docker, and full AR deployment.

## Summary
Satori provides a structured, extensible framework for building AR guidance systems with modular intelligence. Pipelines are the core building blocks, while the Agent serves as a container and runner. This architecture allows for flexible reuse, simplified configuration, and parallel execution of cognitive and interface modules.
