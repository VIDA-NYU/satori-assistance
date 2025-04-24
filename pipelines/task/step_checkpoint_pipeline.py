"""
Step Checkpoint Test Pipeline

This pipeline evaluates whether checkpoints in the current task step have been completed
based on image frames. It uses a BLIP-based vision-language model to verify whether each
checkpoint or step prompt condition is met.

Each task step may have multiple checkpoints and one or more high-level step-check prompts.
This pipeline processes the most recent frame (or all frames in video mode) and generates
a fuzzy evaluation of progress.

Outputs include:
- Binary values (0 or 1) for each checkpoint.
- A fuzzy scalar indicating progress toward completing the entire step.
"""


from ptgctl_pipeline.ptgctl_pipeline.pipeline.base import BasePipeline
from ptgctl_pipeline.ptgctl_pipeline.codec import JsonCodec, HoloframeCodec, BytesCodec, StringCodec
from ptgctl_pipeline.ptgctl_pipeline.stream import StreamConfig
from ptgctl_pipeline.ptgctl_pipeline.pipeline.examples import GPT4VPipeline, FramePipeline
import cv2
import numpy as np
from functools import reduce
import time

import re
import json
import xml.etree.ElementTree as ET
from .models import CheckpointTesterModule


class StepCheckpointTestPipeline(FramePipeline):
    """
    Pipeline for evaluating the completion status of task step checkpoints using visual input.

    Uses:
    - Egocentric video or image input
    - BLIP model inference on checkpoint and step-check prompts

    Produces:
    - List of binary checkpoint completion values (1 if completed, else 0)
    - Scalar score for overall step completion (in_step)

    Input Streams:
        - 'main': Visual image stream
        - 'intent:task:step:current': JSON describing current step and its prompts

    Trigger Streams:
        - 'intent:task:step:checkpoints': Dummy trigger for compatibility
        - 'intent:trigger:checkpoint_tester': Triggers execution of the checkpoint checker

    Output Stream:
        - 'intent:pred:step:checkpoints': Result with fuzzy evaluation of step progress
    """
    
    def __init__(self, stream_map = {}) -> None:
        """
        Initialize the checkpoint testing pipeline.

        Args:
            stream_map (dict): Optional mapping for overriding default stream names.

        Components:
            - Uses FramePipeline to handle frame buffering
            - Registers checkpoint tester for processing BLIP prompts
        """
        super().__init__(
            buffer_limit=4,
            dropout=3,
            postprocess=None,
            stream_map=stream_map,
        )
        self.add_input_streams([
            StreamConfig("intent:task:step:current", JsonCodec)
        ])
        self.add_trigger_streams([
            StreamConfig("intent:task:step:checkpoints", JsonCodec),
            StreamConfig("intent:trigger:checkpoint_tester", JsonCodec)
        ])
        self.add_output_streams([
            StreamConfig("intent:pred:step:checkpoints", JsonCodec)
        ])
        self.checkpoint_tester = CheckpointTesterModule()
        self.current_step = None
        self.dirty = False
        self.initialized = False
        self.test_mode = "image"

    async def on_input_stream(self, message, sid):
        """
        Handles input messages for task step data and frames.

        Args:
            message (dict): Incoming message, usually an image or step JSON.
            sid (str): Stream identifier.

        Sets:
            - current_step: Internal record of the current task step
            - initialized: Marks readiness for running checkpoint evaluation
        """
        # Message here is assumed to be a frame
        if await self.check_and_process_image_stream(message, sid):
            pass
        elif sid == "intent:task:step:current":
            self.current_step = message
            self.initialized = True
    
    @staticmethod
    def _parse_blip_inference(blip_inference):
        """
        Convert BLIP model response ('yes'/'no') to binary numeric value.

        Args:
            blip_inference (str): BLIP output ("yes" or "no").

        Returns:
            float: 1.0 if "yes", 0.0 if "no"
        """
        return 1. if blip_inference == "yes" else 0.
    
    async def run_step_check(self, valid_frames, current_step):
        """
        Run BLIP-based evaluation to check completion of checkpoints and overall step.

        Args:
            valid_frames (list): List of buffered image frames.
            current_step (dict): Step information with checkpoints and status prompts.

        Returns:
            dict: A dictionary with:
                - checkpoint_predictions: list of 0.0 or 1.0 for each checkpoint
                - in_step: fuzzy scalar for whether the step is considered in progress
        """
        if  len(valid_frames) != 0 and self.initialized:
            
            frame = valid_frames[-1]
            checkpoint_prompts = list(map(lambda x: x['blip_prompt'], current_step['checkpoints']))
            step_check_prompts = current_step['step_check_prompts']
            if self.test_mode == "video":
                result = await self.checkpoint_tester.process_frames(
                    valid_frames, checkpoint_prompts + step_check_prompts
                )
            else:
                result = self.checkpoint_tester.process_frame(
                    frame, checkpoint_prompts + step_check_prompts
                )
            result_values = list(map(StepCheckpointTestPipeline._parse_blip_inference, result))
            fuzzy_inputs = {
                    "checkpoint_predictions": [],
                    "in_step": 0.
            }
            for checkpoint_i, checkpoint in enumerate(current_step['checkpoints']):
                fuzzy_inputs['checkpoint_predictions'].append(result_values[checkpoint_i])
            in_step_predictions = result_values[len(checkpoint_prompts):]

            in_step_ratio = sum(in_step_predictions) 
            # / len ( in_step_predictions)
            fuzzy_inputs['in_step'] = in_step_ratio
            return fuzzy_inputs

    
    async def on_trigger_stream(self, message):
        """
        Trigger handler to run the checkpoint evaluator.

        Captures buffered frames and evaluates against current step prompts.

        Args:
            message (dict): Trigger message (unused).

        Returns:
            dict: Result dictionary from `run_step_check`, or None if no step is set.
        """
        frames = await self.get_frames()
        if self.current_step is not None:
            fuzzy_inputs = await self.run_step_check(frames, self.current_step)
            return fuzzy_inputs

    