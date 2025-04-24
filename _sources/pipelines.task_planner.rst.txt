Guidance Pipelines
===================

The ``guidance`` module contains pipelines for AR task tracking and visual assistance generation.
It includes task state controllers and GPT-based visual reasoning pipelines.

Overview
--------

The guidance module consists of modular pipelines that collectively support proactive AR task assistance.
Each pipeline performs a distinct reasoning or control function in the Satori system:

- **Task Control Pipeline**: Tracks and manages transitions between multi-step tasks, maintaining context over time.
- **GPT Guidance Pipeline**: Generates contextual multimodal guidance (e.g., text, image) for the current user action using GPT-4V.
- **GPT Action Pipeline**: Recognizes and forecasts user actions based on visual input and GPT-based reasoning.
- **Task Planner Pipeline**: Converts high-level goals into step-wise task plans with detailed checkpoints for progress tracking.
- **Step Checkpoint Pipeline**: Monitors visual checkpoints to determine completion status of each task step and triggers next-step logic.

These pipelines form the core of the Satori system’s reasoning layer, enabling intelligent, timely, and personalized AR guidance.

Task Control Pipeline
---------------------

.. automodule:: pipelines.task.task_control_pipeline
    :members:
    :undoc-members:
    :show-inheritance:

GPT Guidance Pipeline
---------------------

.. automodule:: pipelines.task.gpt_guidance_pipeline
    :members:
    :undoc-members:
    :show-inheritance:

GPT Action Pipeline
-------------------

.. automodule:: pipelines.task.gpt_action_pipeline
    :members:
    :undoc-members:
    :show-inheritance:

Task Planner Pipeline
---------------------

.. automodule:: pipelines.task.task_planner_pipeline
    :members:
    :undoc-members:
    :show-inheritance:

Step Checkpoint Pipeline
------------------------

.. automodule:: pipelines.task.step_checkpoint_pipeline
    :members:
    :undoc-members:
    :show-inheritance:
