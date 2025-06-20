Satori Documentation
====================

Satori is a development framework for creating augmented reality (AR) task guidance systems. It supports stream-based communication and modular reasoning to enable context-aware, step-by-step assistance in physical tasks. The system is designed to work with AR headsets, such as Microsoft HoloLens, and supports integration with visual recognition models and language models.

The framework organizes functionality into three main layers:
- **Streams**: Data channels managed through `ptgctl`, used to pass information such as images, task states, predictions, and feedback.
- **Pipelines**: Modular processing units that handle individual reasoning tasks, such as interpreting user actions, managing task plans, or generating guidance content.
- **Agents**: Composed of multiple pipelines, agents define how the system responds to input and coordinates guidance delivery.

Satori supports both local testing and deployment in live AR environments. Its architecture allows developers to configure, extend, and evaluate task assistance logic using reusable components.

.. toctree::
   :maxdepth: 3
   :caption: Contents:

   configs/index
   ptgctl_pipeline
   pipelines
