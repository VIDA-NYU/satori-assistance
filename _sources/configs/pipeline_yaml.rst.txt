Pipeline Configuration (`pipeline.yaml`)
========================================

Overview
--------
Defines a single pipeline including its class, stream binding, and custom configuration.

Top-Level Fields
----------------

- ``name``: (str) Logical name for the pipeline
- ``class``: (str) Import path for the pipeline class
- ``stream_map``: (dict) Internal stream name → actual stream ID
- ``config``: (dict) Custom configuration passed as kwargs to the pipeline class

Example
-------

.. code-block:: yaml

    name: gpt-guidance
    class: pipelines.task.GPTGuidancePipeline

    stream_map:
      frame: frame
      belief: intent:belief
      desire: intent:desire

    config:
      system_prompt: ../prompts/guidance/system.yaml
      model: gpt-4
