# ReadMe: PTGCTL Pipeline
A server for running pipelines with PTGCTL.
<!-- # Satori ptgctl-pipeline -->
This package defines the modular and extensible pipeline framework for the Satori AR assistant system. It enables asynchronous, stream-driven processing using the [`ptgctl`](https://github.com/VIDA-NYU/ptgctl) library, supporting multimodal reasoning and guidance through a flexible pipeline model.

## Features

- ✨ Modular async pipelines for AR agents
- ▶️ Stream-based reactive execution (input/trigger/output separation)
- 🚀 PipelineServer manages lifecycle, config, and parallelism
- 🏛️ Supports both YAML config and Python-based pipeline registration

---

## Directory Structure

```
ptgctl_pipeline/
├── __init__.py
├── pipeline.py         # BasePipeline and sample pipelines (Print, GPT)
├── server.py           # PipelineServer: manages concurrent pipeline execution
├── config.py           # read_config(): loads pipeline spec from YAML or dict
```

---

## Usage

```python
from ptgctl_pipeline import PipelineServer
from ptgctl_pipeline.pipeline import PrintPipeline, GPTPipeline
from ptgctl_pipeline.config import read_config
import asyncio

async def main():
    # Load from config file (optional)
    config = read_config()
    server = PipelineServer(config)

    # Define pipelines manually
    custom_pipeline_1 = GPTPipeline(
        prompt_message="Please generate anything about New York",
        input_stream_name="chat:user:message_channel1",
        output_stream_name="chat:assistant:message_channel1",
        sleep_time=0
    )

    custom_pipeline_2 = PrintPipeline(
        input_stream_name="chat:user:message_channel2",
        output_stream_name="chat:assistant:message_channel2",
        sleep_time=0
    )

    server.register_pipeline(custom_pipeline_1)
    server.register_pipeline(custom_pipeline_2)

    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Concepts

### Pipelines
- Subclass of `BasePipeline`
- Defines `async def run()`
- Listens to **input** + **trigger** streams
- Writes to **output** stream

### PipelineServer
- Loads pipelines from config or manual input
- Runs all pipelines concurrently
- Provides lifecycle control and coordination

### Stream Separation
- **Input stream**: carries context (e.g., frame, state)
- **Trigger stream**: causes computation to start
- **Output stream**: publishes results (e.g., inference, response)

---

## Config File Example
```yaml
pipelines:
  - type: ptgctl_pipeline.pipeline.PrintPipeline
    kwargs:
      input_stream_name: "chat:user:message_channel1"
      output_stream_name: "chat:assistant:message_channel1"
      sleep_time: 0
```

---

## License
MIT. See `LICENSE` file.

## Maintainers
This module is developed and maintained by the [VIDA NYU](https://vida.engineering.nyu.edu/) research group as part of the Satori AR assistant project.

