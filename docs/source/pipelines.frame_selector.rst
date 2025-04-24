Frame Selector Pipeline
=====================

The ``frame_selector`` module implements video frame selection mechanisms for AR task guidance systems. It provides pipelines and classifiers to select informative frames from a video stream.

Overview
--------

This module includes:

- A frame selection pipeline that consumes raw video streams and outputs filtered frames
- A module that performs visual object-based keyframe selection using OWL-ViT and KNN clustering
- A scene classifier using CLIP to detect relevant task contexts

Module Contents
---------------

.. automodule:: pipelines.frame_selector.pipeline
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: pipelines.frame_selector.module
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: pipelines.frame_selector.multi_scene
    :members:
    :undoc-members:
    :show-inheritance:
