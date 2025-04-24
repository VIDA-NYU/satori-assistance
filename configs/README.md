# ⚙️ Configuring Agents and Pipelines

This folder contains YAML configuration files for defining the structure and behavior of your Satori agent and its constituent pipelines.

The configuration system allows you to:
- Specify which pipelines to include in an agent
- Define stream mappings and global parameters
- Modularize pipeline configurations for reuse and clarity

---

## 📁 File Overview

- `agent.yaml`: Defines the full agent, including pipeline composition, stream mappings, global arguments, and trigger schedules.
- `pipelines/*.yaml`: Each file defines a single pipeline, including its class path, internal stream map, and parameters.

---

## 🧠 Agent Configuration (`agent.yaml`)

The agent config defines:
- A **global stream map** for shorthand aliases (e.g., `main: main`)
- **Global arguments** shared across pipelines (e.g., API keys)
- A list of **pipelines**, each referencing a separate YAML file
- Optional **trigger schedules** for time-based stream polling

### Example

```yaml
agent:
  stream_map:
    main: main
  global_args:
    api_key: sk-xxx...
  pipelines:
    - ref: ../pipelines/guidance.yaml
    - ref: ../pipelines/task_control.yaml
  triggers:
    - stream: intent:trigger:control
      interval: 2
