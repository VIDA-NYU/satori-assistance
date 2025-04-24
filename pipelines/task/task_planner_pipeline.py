"""
Task Planner Pipeline

Generates a task plan from egocentric image input using GPT-4V.

This pipeline infers a structured task plan—including high-level goals, step content,
checkpoints, and required objects—by sending visual context to GPT-4V and parsing the
resulting XML-formatted response.
"""

from ptgctl_pipeline.ptgctl_pipeline.pipeline.base import BasePipeline
from ptgctl_pipeline.ptgctl_pipeline.codec import JsonCodec, HoloframeCodec, BytesCodec, StringCodec
from ptgctl_pipeline.ptgctl_pipeline.stream import StreamConfig
from ptgctl_pipeline.ptgctl_pipeline.pipeline.examples import GPT4VPipeline
from pathlib import Path
import cv2
import numpy as np
from functools import reduce
import time

import re
import json
import xml.etree.ElementTree as ET
from .helper import load_default_system_prompt
from .task_plans import TASK_PLAN_MAP


def parse_xml_to_dict(xml_data):
    """
    Convert XML-formatted task plan into a structured dictionary.

    Args:
        xml_data (str): XML string from GPT-4V.

    Returns:
        dict: Parsed task plan with fields:
            - 'desired_task': High-level task name
            - 'steps': List of steps, each with:
                - is_start: Whether it’s the first step
                - content: Step-level instruction
                - checkpoints: Instruction + blip prompt pairs
                - step_check_prompts: List of prompts for checking step completion
            - 'objects': List of relevant objects
    """
    # Parse XML data into an ElementTree
    root = ET.fromstring(xml_data)
    
    # Initialize the output dictionary
    task_plan = {
        "desired_task": root.find("DesiredTask").text,
        "steps": [],
        "objects": []
    }
    
    # Parse Steps
    for step in root.find("Steps").findall("Step"):
        step_data = {
            "is_start": step.attrib.get("isStart") == "true",
            "checkpoints": [],
            "step_check_prompts": [],
            "content": step.find("StepContent").text
        }
        for checkpoint in step.find("Checkpoints").findall("Checkpoint"):
            checkpoint_data = {
                "instruction": checkpoint.find("Instruction").text,
                "blip_prompt": checkpoint.find("BlipPrompt").text
            }
            step_data["checkpoints"].append(checkpoint_data)
        
        for prompt in step.find("StepStatusCheckPrompts").findall("Prompt"):
            step_data['step_check_prompts'].append(prompt.text)
        
        task_plan["steps"].append(step_data)
    
    # Parse Objects
    for obj in root.find("Objects").findall("Object"):
        task_plan["objects"].append(obj.text)
    
    return task_plan



class TaskPlannerPipeline(GPT4VPipeline):
    """
    A pipeline for planning multistep tasks from visual input using GPT-4V.

    This pipeline:
    - Takes egocentric image frames as input
    - Triggers task planning on demand
    - Sends the image to GPT-4V with a predefined prompt
    - Parses the XML response into a structured task plan

    Input Stream:
        - 'main': Holoframe image stream

    Trigger Stream:
        - 'intent:trigger-planner': Activates task planning logic

    Output Stream:
        - 'intent:task_plan': Structured JSON of the generated task plan
    """
    IMAGE_INPUT_STREAM_NAME = "main"
    TRIGGER_STREAM = "intent:trigger-planner"
    OUTPUT_STREAM = "intent:task_plan"
    
    def __init__(self, 
        system_prompt: str = load_default_system_prompt(
            Path(__file__).parent / "prompts/task_planner.yaml"
        ),
        api_key: str = "",
        stream_map = {},
    ):
        """
        Initialize the task planner pipeline.

        Args:
            system_prompt (str): XML-based instruction prompt for GPT-4V.
            api_key (str): API key for the GPT model.
            stream_map (dict): Optional overrides for stream names.

        Registers:
            - Input stream: visual image (Holoframe)
            - Trigger stream: to start task planning
            - Output stream: for sending structured task plan
        """
        input_streams = [
            StreamConfig(TaskPlannerPipeline.IMAGE_INPUT_STREAM_NAME, HoloframeCodec)
        ]
        super().__init__(
            system_prompt=system_prompt,
            api_key=api_key,
            stream_map=stream_map,
            postprocess=self.postprocess, 
            buffer_limit=2
        )
        self.add_input_streams([
            StreamConfig(TaskPlannerPipeline.IMAGE_INPUT_STREAM_NAME, HoloframeCodec)
        ])
        self.add_trigger_streams([TaskPlannerPipeline.TRIGGER_STREAM])
        self.add_output_streams([StreamConfig(TaskPlannerPipeline.OUTPUT_STREAM, JsonCodec)])

        
    async def on_input_stream(self, message, sid):
        """
        Handle incoming image stream data.

        Args:
            message (dict): Image data.
            sid (str): Stream identifier.

        Returns:
            None. Sets internal state to prepare for future trigger.
        """
        if self.busy:
            return 
        if await self.check_and_process_image_stream(message, sid):
            pass
    
    async def on_trigger_stream(self, data):
        """
        Trigger handler for running the task planning logic.

        Steps:
            - Resize the current image buffer
            - Send it to GPT-4V with system prompt
            - Parse response into structured task plan

        Args:
            data (dict): Trigger message (not used).

        Returns:
            dict or None: Parsed task plan dictionary, or None if no image is available.
        """
        # time
        
        self.busy = True
        start_time = time.time()
        
        self.enabled = True
        if self.concat_image_set:
            concat_image = cv2.resize(self.concat_image, (0, 0), fx=0.3, fy=0.3)
            origin_response = await self.fetch_gpt_response_async(concat_image)
            self.enabled = False
            if self.postprocess:
                response = self.postprocess(origin_response['response'])
                self.busy = False
                return response
            self.busy = False
            return response
        else:
            self.busy = False
    
    def get_prompt_message(self):
        """
        Returns a simple placeholder prompt for debugging or fallback.

        Returns:
            str: Default text message for prompt logic (usually unused in favor of system prompt).
        """
        return "Analyze the frames to generate the task plan"
    
    def postprocess(self, result):
        """
        Postprocess GPT-4V response to extract task plan in dictionary form.

        Args:
            result (str): Raw XML response from GPT.

        Returns:
            dict: Parsed task plan containing:
                - desired_task: The goal of the task
                - steps: List of step dicts with checkpoints and status prompts
                - objects: List of required object names
        """
        result = result.strip()
        if result.startswith("xml"):
            result = result[3:]
        return parse_xml_to_dict(result)