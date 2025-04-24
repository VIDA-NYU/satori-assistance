Agent Configuration (`agent.yaml`)
==================================

Overview
--------
The `agent.yaml` file defines how the agent system composes multiple pipelines and shares stream bindings and trigger behaviors.

Top-Level Fields
----------------

- ``stream_map`` (dict): Global mapping from internal stream names to actual stream IDs. Lowest priority.
- ``pipelines`` (list): List of pipelines, each optionally with:
  - ``ref`` (str): Path to the pipeline YAML
  - ``overrides`` (dict): Optional override for config and stream_map
- ``triggers`` (list): Optional list of triggers to register at startup

Stream Map Precedence
---------------------
1. Global stream_map
2. Per-pipeline `stream_map` in pipeline YAML
3. `overrides.stream_map` from agent YAML

Example
-------

.. code-block:: yaml

    agent:
      stream_map:
        frame: mainx

      pipelines:
        - ref: ../pipelines/guidance.yaml
          overrides:
            config:
              model: gpt-4
            stream_map:
              output: my-custom-output

      triggers:
        - stream: intent:trigger:control
          interval: 2
