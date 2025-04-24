"""
GPTGuidancePipeline

A stream-driven pipeline for generating multimodal step-level guidance using GPT-4V.

This implementation listens to image input, user beliefs, task step descriptions,
and expertise level, and responds to trigger messages by generating task guidance.
The output includes intent, desire, meta-intent, and both textual and visual guidance.

This pipeline adheres to Satori's pipeline abstraction and is designed to be reactive
and stateless between invocations. It supports modular integration via ptgctl streams.
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
import cv2
import numpy as np
from functools import reduce
import time

import re
import json
import yaml
from pipelines.frame_selector import FrameSelectorModule 
from PIL import Image
from pathlib import Path


PROMPT_PATH = Path(__file__).parent.parent.parent / "configs/prompts/sample_guidance.yaml"
with PROMPT_PATH.open() as f:
    PROMPT_CONFIG = yaml.safe_load(f)


class GPTGuidancePipeline(GPT4VPipeline):
    """
    A pipeline for multimodal guidance generation based on egocentric image and task context.

    Listens to:
    - `main` (image)
    - `intent:belief` (user/system belief)
    - `intent:task:step:next` (next task step)
    - `intent:expertise` (user expertise level)

    Triggered by:
    - `intent:trigger:guidance`

    Outputs to:
    - `intent:pred:guidance` with parsed structured fields
    """
    IMAGE_INPUT_STREAM_NAME = "main"
    TRIGGER_STREAM = "intent:trigger:guidance"
    OUTPUT_STREAM = "intent:pred:guidance"
    TASK_DESCRIPTION = ""
    def __init__(self, 
        system_prompt: str = PROMPT_CONFIG['system_prompt'],
        api_key:str = "",
        model="gpt-4",
        image_resolution=512,
        downsample_rate=3,
        stream_map = {},
        ):
        """
        Initialize the GPTGuidancePipeline with configuration and stream bindings.

        Args:
            system_prompt (str): The system-level prompt used in GPT-4V interactions.
            api_key (str): API key for accessing the GPT model.
            model (str): Model identifier (default: "gpt-4").
            image_resolution (int): Resolution used for image resizing.
            downsample_rate (int): Downsampling factor for video frames.
            stream_map (dict): Optional mapping for stream name overrides.

        Streams:
            Input:
                - 'main' (image stream inherited from GPT4VPipeline)
                - 'intent:belief' (user/system belief; expects HoloframeCodec)
                - 'intent:task:step:next' (next task step; expects JsonCodec)
                - 'intent:expertise' (user's expertise level; expects JsonCodec)

            Trigger:
                - 'intent:trigger:guidance'

            Output:
                - 'intent:pred:guidance' (guidance response; uses JsonCodec)
        """
        super().__init__(system_prompt=system_prompt, api_key=api_key, postprocess=self.postprocess, buffer_limit=2, downsample_rate=downsample_rate, stream_map=stream_map)
        self.add_input_stream(
            StreamConfig("intent:belief", HoloframeCodec)
        )
        self.add_input_stream(
            StreamConfig("intent:task:step:next", JsonCodec)
        )
        self.add_input_stream(
            StreamConfig("intent:expertise", JsonCodec)
        )

        self.add_trigger_stream(
            GPTGuidancePipeline.TRIGGER_STREAM
        )

        self.add_output_streams(
            [StreamConfig(GPTGuidancePipeline.OUTPUT_STREAM, JsonCodec)]
        )
        self.dialogue = []
        self.user_belief = []
        self.system_belief = []
        self.expertise = "novice"
        self.guidance_history = []
        self.desire_history = []
        self.busy = False

        self.index = 100
        self.guidance_index = 8000
        self.dirty = False

        ### system state
        self.active = True
        self.frontend_force_active = True
        self.detect = False
        self.guidance_flag = False
        self.dropout = 1

        self.system_prompt = system_prompt
        self.next_step = None
        self.initialized = False

    async def on_input_stream(self, message, sid):
        """
        Process incoming stream messages.

        Args:
            message (dict): Incoming message payload.
            sid (str): Stream identifier.
        """
        if self.busy:
            return 
        if sid == "intent:belief" and message != None:
            self.user_belief = message['belief']['objects']
            self.system_belief = message['object_history']
        elif sid == "assistant:slow_activate" and message != None:
            self.frontend_force_active = message['status']
        elif sid == "intent:expertise" and message != None:
            self.expertise = message['expertise']
        elif sid == "intent:task:step:next" and message != None:
            self.next_step = message
            self.initialized = True
        elif sid == "intent:task_objects":
            self.task_objects = message
            self.frame_selector.set_valid_objects(self.task_objects)
        elif await self.check_and_process_image_stream(message, sid):
            pass
        elif sid == "intent:chat:user" and message != None:
            message_obj = self.parse_chat_message(message)
            message_obj['sender'] = "user"
            self.dialogue.append(message_obj)
        self.dirty = True
    
    async def on_trigger_stream(self, data):
        """
        Trigger handler that generates guidance using GPT-4V when a trigger message is received.

        Args:
            message (dict): The trigger message (unused).

        Returns:
            dict or None: Processed guidance response.
        """
        if not self.initialized :
            return None
        if self.frontend_force_active == False:
            return None
        self.busy = True
        start_time = time.time()
        self.guidance_index += 1
        # logger.info(f"Start generating guidance {self.guidance_index}")
        
        dialogue_xml = self.assemble_dialogue_xml()
        self.prompt_message = "<EXPERTISE>" + self.expertise +"</EXPERTISE>"
        self.prompt_message += "<TASK_DESCRIPTION>" + GPTGuidancePipeline.TASK_DESCRIPTION + "</TASK_DESCRIPTION>"
        next_step_text = ". ".join(list(map(lambda x: x['instruction'], self.next_step['checkpoints'])))
        next_step_text = self.next_step['content']
        self.prompt_message += "<NEXT_STEP>" + next_step_text + "</NEXT_STEP>"
        # logger.info(f"next step in Prompt message: {next_step_text}")
        self.prompt_message += "You should always output <INTENT><DESIRE><META_INTENT><GUIDANCE_TYPE><CONFIRMATION_CONTENT><OBJECT_LIST><TEXT_GUIDANCE_TITLE><TEXT_GUIDANCE_CONTENT><GUIDANCE_FLAG><DALLE_PROMPT><HIGHLIGHT_OBJECT_FLAG><HIGHLIGHT_OBJECT_LOC><HIGHLIGHT_OBJECT_LABEL> in the response. If you can't recognize INTENT due to blur image or vague actions, infer the <INTENT> as the action the <NEXT_STEP> and provide assistance as usual."
        self.enabled = True
        
        flag, concat_image = await self.get_concat_image()
        if flag:
        
            concat_image = concat_image
            
            resized_concat_image = cv2.resize(concat_image, (0, 0), fx=0.5, fy=0.5)
            # cv2.imwrite(f"figs/slow{self.guidance_index}.jpg", self.concat_image)
            origin_response = await self.fetch_gpt_response_async(resized_concat_image)
            self.enabled = False
            if self.postprocess and 'result' in origin_response:
                # logger.info(f"Origin Response: {origin_response}")
                response = self.postprocess(origin_response['result'])
                # logger.info(f"Response: {response}")
            else:
                self.debug("origin:", origin_response)
                return None
            time_duration = time.time() - start_time
            if response['guidance_flag'] == True:
                cv2.imwrite(f"figs/assistance.jpg", self.concat_image)
            self.busy = False
            if response['confirmation_content'] == '':
                self.debug("ERROR: Empty content", origin_response)
            return response
        else:
            self.busy = False

    def get_prompt_message(self):
        prompt_message = "<EXPERTISE>" + self.expertise +"</EXPERTISE>"
        prompt_message += "<TASK_DESCRIPTION>" + GPTGuidancePipeline.TASK_DESCRIPTION + "</TASK_DESCRIPTION>"
        next_step_text = ". ".join(list(map(lambda x: x['instruction'], self.next_step['checkpoints'])))
        next_step_text = self.next_step['content']
        prompt_message += "<NEXT_STEP>" + next_step_text + "</NEXT_STEP>"
        # logger.info(f"next step in Prompt message: {next_step_text}")
        prompt_message += "You should always output <INTENT><DESIRE><META_INTENT><GUIDANCE_TYPE><CONFIRMATION_CONTENT><OBJECT_LIST><TEXT_GUIDANCE_TITLE><TEXT_GUIDANCE_CONTENT><GUIDANCE_FLAG><DALLE_PROMPT><HIGHLIGHT_OBJECT_FLAG><HIGHLIGHT_OBJECT_LOC><HIGHLIGHT_OBJECT_LABEL> in the response. If you can't recognize INTENT due to blur image or vague actions, infer the <INTENT> as the action the <NEXT_STEP> and provide assistance as usual."
        return prompt_message
    
    def postprocess(self, response):
        """
        Extract and structure guidance information from GPT output lines.

        Args:
            result (list of str): Lines of GPT-4V response.

        Returns:
            dict: Parsed guidance information.
        """
        line_list = response
        response = {}
        response['prompt_confirmation'] = True
        response['intent'] = ""
        response['desire_confirmation'] = ""
        response['desire'] = ""
        response['meta_intent'] = ""
        response['guidance_type'] = ""
        response['confirmation_content'] = ""
        response['lod'] = ""
        response['text_guidance_title'] = ""
        response['text_guidance_content'] = ""
        response['prompt'] = ""
        response['highlight_object_flag'] = False
        response['highlight_object_loc'] = "none"
        response['highlight_object_label'] = "N/A"

       
        
        thoughts = []
        chat_message_bool = False
        guidance_flag = False
        for line in line_list:
            if "<INTENT>" in line:
                response['intent'] = line.split("<INTENT>")[1].split("</INTENT>")[0].strip()
            elif "<DESIRE_CONFIRMATION>" in line:
                response['desire_confirmation'] = line.split("<DESIRE_CONFIRMATION>")[1].split("</DESIRE_CONFIRMATION>")[0].strip()
            elif "<DESIRE>" in line:
                response['desire'] = line.split("<DESIRE>")[1].split("</DESIRE>")[0].strip()
            elif "<META_INTENT>" in line:
                response['meta_intent'] = line.split("<META_INTENT>")[1].split("</META_INTENT>")[0].strip()
            elif "<GUIDANCE_TYPE>" in line or "<Guidance_TYPE>" in line or "<guidance_type>" in line:
                response['guidance_type'] = line.split("<GUIDANCE_TYPE>")[1].split("</GUIDANCE_TYPE>")[0].strip().lower()
                if response['guidance_type'] == "text":
                    response['guidance_type'] = "notes"
                if 'image' in response['guidance_type']:
                    response['guidance_type'] = "image"
                if 'timer' in response['guidance_type']:
                    response['guidance_type'] = "timer"
            elif "<CONFIRMATION_CONTENT>" in line:
                response['confirmation_content'] = line.split("<CONFIRMATION_CONTENT>")[1].split("</CONFIRMATION_CONTENT>")[0].strip()
            elif "<LOD>" in line:
                response['lod'] = line.split("<LOD>")[1].split("</LOD>")[0].strip()
            elif "<TEXT_GUIDANCE_TITLE>" in line:
                response['text_guidance_title'] = "Guidance"
                response['text_guidance_title'] = line.split("<TEXT_GUIDANCE_TITLE>")[1].split("</TEXT_GUIDANCE_TITLE>")[0].strip()
            elif "<TEXT_GUIDANCE_CONTENT>" in line:
                response['text_guidance_content'] = line.split("<TEXT_GUIDANCE_CONTENT>")[1].split("</TEXT_GUIDANCE_CONTENT>")[0].strip()
            elif "<GUIDANCE_FLAG>" in line:
                text_guidance_flag = line.split("<GUIDANCE_FLAG>")[1].split("</GUIDANCE_FLAG>")[0].strip()
                guidance_flag = True if text_guidance_flag.strip().lower() == "true" else False
                response['guidance_flag'] = guidance_flag
            elif "<DALLE_PROMPT>" in line:
                response['prompt'] = line.split("<DALLE_PROMPT>")[1].split("</DALLE_PROMPT>")[0].strip()
            elif "<CHAT_MESSAGE_FLAG>" in line:
                chat_message_flag = line.split("<CHAT_MESSAGE_FLAG>")[1].split("</CHAT_MESSAGE_FLAG>")[0].strip()
                chat_message_bool = True if chat_message_flag.strip().lower() == "true" else False
                response['chat_flag'] = chat_message_flag
            elif "<CHAT_MESSAGE>" in line:
                response['chat_message'] = line.split("<CHAT_MESSAGE>")[1].split("</CHAT_MESSAGE>")[0].strip()
                if chat_message_bool:
                    self.dialogue.append(
                        {
                            "sender": "assistant",
                            "content": response['chat_message'],
                            "timestamp": int(time.time())
                        }
                    )
            elif "<HIGHLIGHT_OBJECT_FLAG>" in line:
                highlight_object_flag = line.split("<HIGHLIGHT_OBJECT_FLAG>")[1].split("</HIGHLIGHT_OBJECT_FLAG>")[0].strip()
                highlight_object_bool = True if highlight_object_flag.strip().lower() == "true" else False
                response['highlight_object_flag'] = highlight_object_bool
            elif "<HIGHLIGHT_OBJECT_LOC>" in line:
                response['highlight_object_loc'] = line.split("<HIGHLIGHT_OBJECT_LOC>")[1].split("</HIGHLIGHT_OBJECT_LOC>")[0].strip().lower()
            elif "<HIGHLIGHT_OBJECT_LABEL>" in line:
                response['highlight_object_label'] = line.split("<HIGHLIGHT_OBJECT_LABEL>")[1].split("</HIGHLIGHT_OBJECT_LABEL>")[0].strip()
            else:
                thoughts.append(line)
        response["index"] = int(time.time())
        response['desire'] = "Connect Switch"
        # response['desire'] = 'Arrange Flowers'
        # response['desire'] = 'Make Coffee'
        # response['desire'] = 'Clean Room'
        self.desire_history.append(response['desire'])
        response['guidance_flag'] = True
        self.detect = True
        response['detect'] = self.detect
        response['type'] = "slow"
        response['active'] = self.active
        response['text_always'] = True 
        response['input_action'] = self.next_step
        self.guidance_history.append(
                    {
                        "title": response['text_guidance_title'],
                        "content": response['text_guidance_content']
                    }
                )
        
        return response
    
    def parse_result(self, result):
        """
        Split GPT output into visible lines and extract internal thoughts.

        Args:
            result (str): Multiline GPT string output.

        Returns:
            tuple[list[str], str]: List of result lines, and a string of internal thoughts.
        """
        lines = result.split("\n")
        thoughts = []
        visible_lines = []
        for line in lines:
            if line.startswith("#"):
                thoughts.append(line)
            else:
                visible_lines.append(line)
        return visible_lines, "\n".join(thoughts)

    def parse_chat_message(self, message):
        """
        Parse chat message string with pipe-separated content and timestamp.

        Args:
            message (str): Raw chat message in the format "content|timestamp".

        Returns:
            dict or None: Parsed dictionary with content and timestamp or None if format invalid.
        """
        splits = message.split("|")
        if len(splits) == 2:
            return {
                "content": splits[0],
                "timestamp": int(splits[1])
            }
        return None

    def assemble_dialogue_xml(self):
        """
        Assemble user-assistant dialogue into XML string.

        Returns:
            str: XML-formatted dialogue history.
        """
        messages = self.dialogue
        messages_xml = list(map(lambda x: f'<Message sender="{x["sender"]}" content="{x["content"]}"/>\n', messages))
        messages_xml_str = reduce(lambda x, y: x + y, messages_xml, "")
        return "<Dialogue> {} </Dialogue>".format(messages_xml_str)

