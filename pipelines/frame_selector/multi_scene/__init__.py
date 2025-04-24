"""
Multi-Scene Classification Module

Classifies input frames into one of several task-specific scenes using a CLIP model.
This module is used to filter out irrelevant frames and detect relevant task contexts.

Author: Guande Wu
"""

# === Third-party Libraries ===
import torch
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel


class MultiSceneClassificationModule:
    """
    Scene classification using OpenAI CLIP for detecting relevant task-related scenes.
    """

    def __init__(self):
        self.device = torch.device("cuda:1" if torch.cuda.is_available() else "cpu")
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.model.eval()

        self.scenes = [
            "coffee making",
            "room cleaning with mop",
            "connecting Nintendo Switch to monitor",
            "arranging flowers",
            "unrelated scene"
        ]

        self.scene_descriptions = [
            "A person making coffee, with items like a coffee machine, grinder, kettle, or coffee beans visible",
            "Someone cleaning a room with a mop, showing cleaning supplies and wet floor",
            "Connecting a Nintendo Switch console to a TV or monitor, with cables and gaming equipment visible",
            "Arranging flowers in a vase, with various flowers and floral supplies present",
            "A scene unrelated to coffee making, room cleaning, Nintendo Switch setup, or flower arranging"
        ]

        self.text_inputs = self.processor(text=self.scene_descriptions, padding=True, return_tensors="pt").to(self.device)

    @torch.no_grad()
    def classify_image(self, image: Image.Image) -> list:
        """
        Classifies the input image into one of the predefined scenes.

        :param image: Input image (PIL or numpy array).
        :type image: PIL.Image or np.ndarray
        :returns: List of tuples (scene, probability).
        :rtype: list
        """
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image.astype('uint8'), 'RGB')

        image_inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        outputs = self.model(**image_inputs, **self.text_inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)
        return [(scene, prob.item()) for scene, prob in zip(self.scenes, probs[0])]

    def filter_frame(self, frame: Image.Image, threshold: float = 0.3) -> bool:
        """
        Filters the frame based on whether it is a relevant scene.

        :param frame: Input frame.
        :type frame: PIL.Image or np.ndarray
        :param threshold: Probability threshold to consider a scene as relevant.
        :type threshold: float
        :returns: True if the frame is relevant; False if it's unrelated.
        :rtype: bool
        """
        results = self.classify_image(frame)
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
        top_scene, top_prob = sorted_results[0]
        is_relevant = top_scene != "unrelated scene" and top_prob >= threshold
        return is_relevant
