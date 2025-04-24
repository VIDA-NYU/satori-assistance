from transformers import BlipProcessor, BlipForQuestionAnswering
from PIL import Image
import requests
from ptgctl_pipeline.ptgctl_pipeline.pipeline.base import BasePipeline
from ptgctl_pipeline.ptgctl_pipeline.codec import JsonCodec, HoloframeCodec, BytesCodec, StringCodec
from ptgctl_pipeline.ptgctl_pipeline.stream import StreamConfig
from ptgctl_pipeline.ptgctl_pipeline.pipeline.examples import GPT4VPipeline

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


class CheckpointTesterModule():
    def __init__(self) -> None:
        # Initialize BLIP processor and model from Hugging Face
        self.device = "cuda:0"
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-vqa-base")
        self.model = BlipForQuestionAnswering.from_pretrained("Salesforce/blip-vqa-base").to(self.device)

    def process_frame(self, image, prompt_text_list):
        
        images = [image] * len(prompt_text_list)

        # Create batch inputs using the processor
        inputs = self.processor(images=images, text=prompt_text_list, return_tensors="pt", padding=True).to(self.device)

        # Perform model inference in batch
        outputs = self.model.generate(**inputs)

        # Decode the output to get answers
        answers = [self.processor.decode(output, skip_special_tokens=True) for output in outputs]
        # print(answers)
        return answers
