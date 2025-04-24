"""
Frame Selector Pipeline

This module defines a Satori pipeline for filtering and selecting frames
based on visual scene classification. It uses a `MultiSceneClassificationModule`
to determine which frames are informative, skipping over unhelpful or redundant ones.

Author: VIDA NYU
"""

# === Standard Library ===
import os
import json
import re
from functools import reduce
from dataclasses import dataclass

# === Third-party Libraries ===
import cv2
import numpy as np
from PIL import Image
import torch
from sklearn.neighbors import NearestNeighbors
from transformers import DetrImageProcessor, DetrForObjectDetection
from torchvision import models, transforms

# === Internal Imports ===
from ptgctl_pipeline.ptgctl_pipeline.pipeline.base import BasePipeline
from ptgctl_pipeline.ptgctl_pipeline.codec import HoloframeCodec
from ptgctl_pipeline.ptgctl_pipeline.stream import StreamConfig
from pipelines.frame_selector.module import FrameSelectorModule
from .multi_scene import MultiSceneClassificationModule


class FrameSelectorPipeline(BasePipeline):
    """
    A pipeline that filters input video frames using a scene classification model.

    **Streams**:
        - Input: ``main`` (HoloframeCodec) – receives incoming video frames.
        - Trigger: ``main`` (HoloframeCodec) – triggers the filtering process.
        - Output: ``processed_main`` (HoloframeCodec) – publishes selected valid frames.

    This pipeline is designed to ignore uninformative frames and reduce processing load.
    """

    IMAGE_INPUT_STREAM_NAME = "main"
    TRIGGER_STREAM = "main"
    OUTPUT_STREAM = "processed_main"

    def __init__(self, stream_map = {}):
        """
        Initializes the FrameSelectorPipeline with stream configurations and
        a scene classification model to filter valid frames.
        """
        
        super().__init__(stream_map=stream_map)

        input_streams = [StreamConfig(self.IMAGE_INPUT_STREAM_NAME, HoloframeCodec)]
        trigger_streams = [StreamConfig(self.TRIGGER_STREAM, HoloframeCodec)]
        output_streams = [StreamConfig(self.OUTPUT_STREAM, HoloframeCodec)]

        self.add_input_streams(
            input_streams
        )
        self.add_trigger_streams(
            trigger_streams
        )
        self.add_output_streams(
            output_streams
        )

        self.frame_selector = MultiSceneClassificationModule()
        self.frame = None
        self.valid_frame = None
        self.empty_counter = 0
        self.empty_threshold = 10

    async def on_input_stream(self, message, sid):
        """
        Handles new input frames from the input stream.

        :param message: A dictionary containing the frame data (expects a key 'image').
        :type message: dict
        :param sid: The stream ID from which the message originates.
        :type sid: str
        """
        if sid == self.IMAGE_INPUT_STREAM_NAME:
            self.frame = message['image']

    async def on_trigger_stream(self, message):
        """
        Applies the frame filtering logic when triggered.

        If the frame passes the scene classifier, it is returned as valid output.
        Otherwise, the function increments an internal counter and returns None.

        :param message: A dictionary containing the trigger frame (expects a key 'image').
        :type message: dict
        :returns: A valid frame if accepted by the filter, otherwise None.
        :rtype: np.ndarray or None
        """
        frame_rgb = cv2.cvtColor(message['image'], cv2.COLOR_BGR2RGB)

        if self.empty_counter > self.empty_threshold:
            self.empty_counter = 0
            return message['image']

        pil_frame = Image.fromarray(frame_rgb) if isinstance(frame_rgb, np.ndarray) else None

        if pil_frame and self.frame_selector.filter_frame(pil_frame):
            self.valid_frame = message['image']
            return self.valid_frame
        else:
            self.empty_counter += 1
            return None
