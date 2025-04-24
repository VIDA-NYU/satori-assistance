"""
Task Control Pipeline

Handles stream-driven guidance for procedural tasks, such as brewing coffee, by maintaining task state,
processing user feedback, and coordinating guidance generation using a finite state machine and input from
multimodal sensors. Designed for integration into the Satori AR assistant system.
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
import torch
from transformers import DetrImageProcessor, DetrForObjectDetection
from sklearn.neighbors import NearestNeighbors
from torchvision import models, transforms
from PIL import Image
import numpy as np
import json
import os
from pipelines.frame_selector.module import FrameSelectorModule
from .models import CheckpointTesterModule
from dataclasses import dataclass
from .fuzzy import FuzzyTaskMachine
from .task_plans import TASK_PLAN_MAP
from collections import deque
import asyncio
from .helper import load_default_system_prompt




@dataclass
class CheckpointReachAction:
    """
    Dataclass representing an action where a user reaches a specific checkpoint
    in a task. Used for tracking inventory or progress data.

    Attributes:
        name (str): Name of the checkpoint or action.
        unit_price (float): Cost or value associated with this action (if applicable).
        quantity_on_hand (int): Tracks inventory or count (default is 0).
    """
    name: str
    unit_price: float
    quantity_on_hand: int = 0


def enumerate_and_clear(sequence):
    """
    Consume and yield all items from a deque.

    Args:
        sequence (deque): A deque to enumerate and clear.

    Yields:
        deque item
    """
    while sequence:
        yield sequence.popleft()


class TaskControlPipeline(BasePipeline):
    """
    Main control pipeline for task guidance coordination in the Satori AR system.

    This pipeline:
    - Maintains current task state using a fuzzy state machine.
    - Responds to user actions and feedback via trigger/input streams.
    - Orchestrates downstream pipelines like checkpoint tester and guidance generator.
    - Issues activation commands for guidance at key steps.

    Inputs:
        - Camera frames and predicted checkpoints/guidance
        - Task plans and step-level feedback
        - Activation requests (fast/slow)

    Outputs:
        - Updated task steps and task state
        - Trigger signals for checkpoint testing and guidance generation

    Attributes:
        task_name (str): Name of the task (e.g., 'coffee').
        task_machine (FuzzyTaskMachine): Internal task state manager.
        feedback_actions (deque): Feedback queue from the user.
        guidance_pred (dict): Stores the predicted guidance for current step.
        states (dict): Tracks whether steps/guidance have changed/shown.
    """
    OUTPUT_STREAM = "assistant:test"
    TRIGGER_STREAM = "intent:trigger:controlx"
    IMAGE_INPUT_STREAM_NAME = "main"
    
    def __init__(self, task_name="coffee", stream_map={}):
        """
        Initialize the TaskControlPipeline.

        This constructor sets up the pipeline's input, output, and trigger streams,
        and prepares the internal state for managing procedural AR tasks using a
        fuzzy state machine. It supports dynamic activation, task feedback tracking,
        and coordination with downstream modules such as guidance and checkpoint testers.

        Args:
            task_name (str): Name of the task plan to load (e.g., 'coffee').
            stream_map (dict): Optional mapping for renaming or redirecting streams.
        """
        super().__init__(
            stream_map=stream_map,
        )
        
        self.add_input_stream(
            StreamConfig("intent:task:step:current", JsonCodec)
        )

        self.add_input_streams(
            [
                StreamConfig(TaskControlPipeline.IMAGE_INPUT_STREAM_NAME, HoloframeCodec), 
                StreamConfig("intent:task_plan", JsonCodec), 
                StreamConfig("intent:pred:step:checkpoints", JsonCodec), 
                StreamConfig("intent:pred:guidance", JsonCodec), 
                StreamConfig("assistant:fast_activate", JsonCodec), 
                StreamConfig("assistant:slow_activate", JsonCodec),
                StreamConfig("intent:feedback:checkpoint", JsonCodec),
                StreamConfig("intent:feedback:step", JsonCodec),
            ]   
        )

        self.add_trigger_streams(
            [TaskControlPipeline.TRIGGER_STREAM]
        )

        self.add_output_streams(
            [
                StreamConfig("intent:task:step:current", JsonCodec), 
                StreamConfig("intent:task:step:next", JsonCodec),
                StreamConfig("intent:trigger:checkpoint_tester", JsonCodec),
                StreamConfig("intent:trigger:guidance", JsonCodec),
                StreamConfig("intent:trigger:action", JsonCodec),
                StreamConfig("assistant:summary", JsonCodec),
                StreamConfig("intent:task:state", JsonCodec)
            ]
        )
        self.frame = None
        self.index = 0
        self.task_name = task_name
        self.task_plan = TASK_PLAN_MAP[self.task_name] 
        self.task_machine = FuzzyTaskMachine(self.task_plan, allow_self_step_change=True)
        self.count = 0
        self.action_sequence = []
        self.test_mode = "image"
        self.in_confirmning = False
        self.states = {
            "step_change": False,
            "guidance_countdown": -1,
            "first_guidance_shown": False,
            "shown_guidance_list": []
        }
        self.trigger_count = 0
        self.busy = False
        self.initilaized = False
        self.output_mode = 'multi'
        self.in_step_state = False
        
        self.fast_guidance_index = 0
        self.guidance_index = 0
        self.guidance_pred = {} 
        self.first_time = True
        self.feedback_actions = deque()
        self.guidance_dirty = False
        
    async def on_input_stream(self, message, sid):
        """
        Handle all input streams to update task state.

        Args:
            message (dict): Stream message content.
            sid (str): Stream identifier.
        """
        # Message here is assumed to be a frame
        if sid == "intent:task_plan":
            task_plan = message
            valid_task_objects = task_plan['objects']
            self.task_plan = task_plan
        elif sid == "intent:pred:step:checkpoints":
            self.step_checkpoints_pred = message
            if self.task_machine.task_state != "IN_TRANSITION":
                self.task_machine.add_frame(self.step_checkpoints_pred)
                results = self.task_machine.update_step_state()
                if results['step_change'] :
                    # self.debug("DOING STEP CHANGE BY PREDICTION")
                    self.schedule_new_guidance()
                    self.states['step_change'] = True

        elif sid == "intent:pred:guidance":
            next_action_id = self.task_machine.get_next_action_id()
            step_index = message['input_action']['step_index']
            self.guidance_pred[step_index] = message
            if not self.task_machine.is_initialized():
                self.task_machine.initialize()
                self.schedule_new_guidance()
                
            if self.task_machine.task_state == "IN_STEP":
                self.schedule_new_guidance()
        elif sid == "assistant:fast_activate":
            pass
        elif sid == "assistant:slow_activate":
            return 
            new_in_step_state = message['status']
            if new_in_step_state == True and not self.in_step_state:
                self.in_step_state = True
                next_step_flag = self.task_machine.get_next_step(force=True)
                if next_step_flag:
                    self.states['step_change'] = True
            elif new_in_step_state == False and self.in_step_state:
                self.in_step_state = False
                if self.first_time:
                    self.first_time = False
                    self.task_machine.initialize()
        elif sid == "intent:feedback:checkpoint":
            feedback_action = message 
            if feedback_action['action'] == "checkpoint_set":
                state_to_set = feedback_action['state']
                checkpoint_index = feedback_action['checkpoint_index']
                self.task_machine.force_set_checkpoint_state(checkpoint_index, state_to_set)
                results = self.task_machine.update_step_state()
                if results['step_change'] :
                    self.schedule_new_guidance()
                    self.states['step_change'] = True
                
        elif sid == "intent:feedback:step":
            feedback_action = message
            if feedback_action['action'] == "step_next":
                self.task_machine.finish_step(force=True)
                if not self.in_confirmning:
                    self.schedule_new_guidance()
                    self.states['step_change'] = True
            elif feedback_action['action'] == "step_back":
                self.task_machine.force_go_prev_step()
            elif feedback_action['action'] == "step_next_confirm":
                self.task_machine.finish_transition()
                self.states['step_change'] = False
                await asyncio.sleep(3)
                self.in_confirmning = False
            elif feedback_action['action'] == "step_next_decline":
                self.task_machine.decline_next_step()
            elif feedback_action['action'] == "step_next_revert":
                self.task_machine.reset_step_state()
            elif feedback_action['action'] == "step_set":
                pass
            
    def merge_fast_slow_message(self, fast_message, slow_message, guidance_index, fast_detect, slow_detect, fast_active, slow_active):
        merged_message = {}
        merged_message['guidance_type'] = "none"
        for key, value in slow_message.items():
            if key in ['active', 'detect']:
                continue
            merged_message[key] = value
        for key, value in fast_message.items():
            if key in ['active', 'detect']:
                continue
            merged_message[key] = value
        
        merged_message['fast_detect'] = fast_detect # fast_message['detect']
        merged_message['slow_detect'] = slow_detect # slow_message['detect']
        merged_message['fast_active'] = fast_active # fast_message['active']
        merged_message['slow_active'] = slow_active # slow_message['active']
        merged_message['slow_index'] = self.guidance_index
        merged_message['index'] = self.fast_guidance_index #self.slow_index
        return merged_message
           
    def determine_next_step(self):
        current_step_id = self.get_current_step_id()
        if current_step_id not in self.guidance_pred:
            return self.task_machine.steps[current_step_id]
        else:
            next_step_id = self.task_machine.get_next_action_id()
            return self.task_machine.steps[next_step_id]
    
    def prepare_initializing_message(self):
        initializing_message  = {
            "guidance_type": "none",
            "prompt_confirmation": False,
            "confirmation_content": "none",
            "index": 0,
            "text_guidance_title": "none",
            "text_guidance_content": "none",
            "desire": "none",
            "meta-intent": "none",
            "intent": "none",
            "objects": "none",
            "detect": False,
            "active": True,
            "fast_detect": True,
            "slow_detect": False,
            "fast_active": True,
            "slow_active": True,
            "message_type": "init"
        }
        return initializing_message
            
    def prepare_guidance_message(self, update_message=False, update_countdown=False):
        default_message = {
            "guidance_type": "none",
            "prompt_confirmation": False,
            "confirmation_content": "none",
            "index": 0,
            "text_guidance_title": "none",
            "text_guidance_content": "none",
            "desire": "none",
            "meta-intent": "none",
            "intent": "none",
            "objects": "none",
            "detect": False,
            "active": True,
            "message_type": "guidance"
        }
        self.fast_guidance_index = int(time.time())
        if update_message and self.guidance_dirty:
            self.guidance_index = int(time.time())
            self.guidance_dirty = False
        default_fast_message = {"type": "fast", "guidance_flag": False, "intent": "", "active": True, "detect": False}
        guidance_step_index = self.task_machine.get_guidance_step_index()
        # self.debug("GUIDANCE_STEP_INDEX", guidance_step_index, self.guidance_pred)
        if guidance_step_index in self.guidance_pred:
            merged_message = self.merge_fast_slow_message(default_fast_message, self.guidance_pred[guidance_step_index], self.guidance_index, update_countdown, update_message==True, True, self.in_step_state)
        else:
            return None
        if update_message:
            merged_message['slow_detect'] = True
        merged_message['message_type'] = "guidance"
        merged_message['slow_detect'] = True
        
        if len(merged_message['confirmation_content']) < 0:
            merged_message['confirmation_content'] = current_step_desc = self.task_machine.steps[self.task_machine.get_guidance_step_index()]['content']
        ###### chenyi-change ######

        return merged_message
        
    def prepare_task_status(self):
        
        checkpoint_states = ["NOT_STARTED"] * len(self.task_machine.current_checkpoint_states)
        for checkpoint_index, fuzzy_state in self.task_machine.current_checkpoint_states.items():
            checkpoint_states[checkpoint_index] = fuzzy_state.state
        current_step_index = self.task_machine.get_current_step_id()
        current_step_index_to_show = current_step_index
        if not self.task_machine.is_initialized_and_first_transitioned():
            current_step_index_to_show = -1
            
        if current_step_index in self.guidance_pred:
            guidance_step_desc = self.guidance_pred[current_step_index]['text_guidance_content']
            if guidance_step_desc != "" and len(guidance_step_desc) > 10:
                current_step_desc = guidance_step_desc
            else:
                current_step_desc = self.task_machine.get_current_step()['content']
        else:
            current_step_desc = self.task_machine.get_current_step()['content']
        
        if len(current_step_desc) > 100:
            current_step_desc = current_step_desc[:100] + "..."
        next_step_index = self.task_machine.get_next_action_id()
        return {
            "current_step": current_step_desc,
            "checkpoints": list(map(lambda x: x['instruction'], self.task_machine.get_current_step()['checkpoints'])),
            "checkpoint_states": checkpoint_states,
            "step_status": self.task_machine.current_step_state.state,
            "allow_next": (next_step_index in self.guidance_pred) and current_step_index < len(self.task_machine.task_schema['steps']) - 1,
            "allow_prev": current_step_index > 0,
            "step_id":current_step_index_to_show 
        }
        
    def schedule_new_guidance(self):
        """
        Flag pipeline state as needing to generate new guidance.
        """
        self.guidance_dirty = True
        
    async def on_trigger_stream(self, message):
        """
        Trigger guidance generation and update task state outputs.

        Args:
            message (dict): Trigger input (ignored).

        Returns:
            dict: Outbound messages for various guidance and state outputs.
        """
        response = {}
        timestamp = int(time.time())
        if not self.states['first_guidance_shown']:
            current_step = self.task_machine.get_current_step()
            next_action = self.task_machine.get_next_action()
            response['intent:task:step:current'] = current_step
            response['intent:task:step:next'] = next_action
        finsihed_step = self.task_machine.finish_step()
        
        if (self.states['step_change'] ) or not self.initilaized:
            current_step = self.task_machine.get_current_step()
            next_action = self.task_machine.get_next_action()
            self.initilaized = True
            self.states['guidance_countdown'] = 0
            self.states['step_change'] = False

        if self.trigger_count % 5 == 1 and not self.task_machine.is_in_transitioning():
            response['intent:trigger:checkpoint_tester'] = {
                "timestamp": timestamp
            }
            
        if self.trigger_count % 10 == 1 and not self.task_machine.is_in_transitioning():
            response['intent:trigger:action'] = {
                "timestamp": timestamp
            }
            
        if self.trigger_count % 20 == 1 and not self.task_machine.is_in_transitioning():
            response['intent:trigger:guidance'] = {
                "timestamp": timestamp
            }
        self.trigger_count += 1
        current_step_id = self.task_machine.get_current_step_id()
        
        response['intent:task:state'] = self.prepare_task_status()
        
        if current_step_id in self.guidance_pred and self.task_machine.is_initialized():
            if self.states['guidance_countdown'] > 0:
                self.states['guidance_countdown'] -= 1
                guidance_message = self.prepare_guidance_message(update_message=False, update_countdown=True)
            elif self.states['guidance_countdown'] == 0 and not self.in_confirmning:
                self.in_confirmning = True

                guidance_message = self.prepare_guidance_message(update_message=True)
                self.states['guidance_countdown'] = -1
            else:
                guidance_message = self.prepare_guidance_message()
            if guidance_message is not None:
                response['assistant:summary'] = guidance_message
        elif not self.task_machine.is_initialized():
            initializing_message = self.prepare_initializing_message()
            response['assistant:summary'] = initializing_message
        return response