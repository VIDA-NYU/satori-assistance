"""
GPT Action Prediction Pipeline

Uses GPT-4V to infer the state of task checkpoints based on egocentric images.
Generates structured predictions (COMPLETED, IN_PROGRESS, etc.) for each checkpoint and overall step.
"""

import cv2
import json
from ptgctl_pipeline.ptgctl_pipeline.pipeline.examples import GPT4VPipeline
from ptgctl_pipeline.ptgctl_pipeline.stream import StreamConfig
from ptgctl_pipeline.ptgctl_pipeline.codec import JsonCodec, HoloframeCodec
from pathlib import Path
import yaml

# Load prompt from YAML
PROMPT_PATH = Path(__file__).parent / "prompts/action.yaml"
with PROMPT_PATH.open() as f:
    PROMPT_CONFIG = yaml.safe_load(f)


class GPTActionPredictionPipeline(GPT4VPipeline):
    """
    A pipeline for predicting task checkpoint progress using GPT-4V and visual input.

    This pipeline:
    - Listens for task step descriptions (current and next).
    - Waits for a trigger to process the current image stream.
    - Sends concatenated visual input and task prompts to GPT-4V.
    - Parses and outputs checkpoint-level status predictions.

    Input Streams:
        - 'main': Visual input stream (inherited from GPT4VPipeline)
        - 'intent:task:step:current': Description and checkpoints for current step
        - 'intent:task:step:next': Description for next step (optional)

    Trigger Stream:
        - 'intent:trigger:action': Initiates prediction on demand

    Output Stream:
        - 'intent:pred:step:checkpoints': JSON with status prediction for each checkpoint
    """

    INPUT_IMAGE_STREAM_NAME = "main"
    TRIGGER_STREAM_NAME = "intent:trigger:action"
    OUTPUT_STREAM_NAME = "intent:pred:step:checkpoints"

    def __init__(self,
            api_key: str = "",
            system_prompt: str = PROMPT_CONFIG['system_prompt'],
            stream_map = {}
        ):
        """
        Initialize the pipeline with necessary prompts and stream bindings.

        Args:
            api_key (str): API key for accessing the GPT model.
            system_prompt (str): Prompt template for GPT-4V prediction.
            stream_map (dict): Optional overrides for stream names.

        Registers:
            - Two input streams: current step and next step descriptions.
            - One trigger stream to activate inference.
            - One output stream for predictions.
        """
        input_streams = [
            StreamConfig('intent:task:step:next', JsonCodec),
            StreamConfig('intent:task:step:current', JsonCodec),
        ]
        super().__init__(
            system_prompt = PROMPT_CONFIG['system_prompt'],
            api_key = api_key,
            stream_map = stream_map,
        )
        self.add_input_streams(
            [
                StreamConfig('intent:task:step:next', JsonCodec),
                StreamConfig('intent:task:step:current', JsonCodec),
            ]
        )
        self.add_trigger_streams(
            [self.TRIGGER_STREAM_NAME]
        )
        self.add_output_streams(
            [StreamConfig(self.OUTPUT_STREAM_NAME, JsonCodec)]
        )
        self.current_step = None
        self.next_step = None

    async def on_input_stream(self, message, sid):
        """
        Handle input stream updates for task steps and image triggers.

        :param message: Input data message.
        :param sid: Stream identifier.
        """
        if await self.check_and_process_image_stream(message, sid):
            return
        elif sid == "intent:task:step:current":
            self.current_step = message
        elif sid == "intent:task:step:next":
            self.next_step = message

        return await super().on_input_stream(message, sid)

    async def on_trigger_stream(self, message):
        """
        Triggered to process image and generate GPT-4V prediction.

        :param message: Unused trigger message.
        :return: Dictionary of predictions or None.
        """
        flag, concat_image = await self.get_concat_image(resize_ratio=0.6)
        cv2.imwrite("concat_image.jpg", concat_image)

        if flag and self.current_step is not None:
            prompt = self._build_prompt()
            response = await self.fetch_gpt_response_async(
                concat_image,
                prompt_message=prompt,
                system_prompt=self.SYSTEM_PROMPT
            )
            result = parse_result(response['response'])

            if result:
                return {
                    "checkpoint_predictions": [
                        {"value": 1., "confidence": 1.} if s == 'IN_PROGRESS' else {"value": 0., "confidence": 1.}
                        for s in result['checkpoints']
                    ],
                    "in_step": {"value": 1., "confidence": 1.} if result['in_step'] == 'PROCESSING' else {"value": 0., "confidence": 1.}
                }
        return None

    def _build_prompt(self):
        """
        Build the step + checkpoint prompt for GPT-4V.

        :return: Prompt string in XML-like format.
        """
        checkpoints = "\n".join(
            f"<Checkpoint>{c['instruction']}</Checkpoint>" for c in self.current_step['checkpoints']
        )
        current = f"""
        <Step isStart="true">
            <StepContent>{self.current_step['content']}</StepContent>
            <Checkpoints>{checkpoints}</Checkpoints>
        </Step>"""
        next_step = f"<NextStep>{self.next_step['content']}</NextStep>" if self.next_step else ""
        return current + next_step


def parse_result(result_string):
    """
    Parse GPT-4V JSON output into simplified format.

    :param result_string: Raw JSON string from GPT response.
    :return: Parsed dictionary or None on failure.
    """
    try:
        result_string = result_string.strip()
        if result_string.startswith("```json"):
            result_string = result_string[7:-3]
        result = json.loads(result_string)
        return {
            "checkpoints": [c['status'] for c in result['checkpoints']],
            "in_step": result['overallStatus']
        }
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Parse error: {e}\n{result_string}")
        return None
