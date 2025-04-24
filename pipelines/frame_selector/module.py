"""
Frame Selector Module

Provides frame selection functionality based on object detection and visual similarity.
Encapsulates logic for buffering frames, detecting valid objects, extracting features,
and selecting keyframes using KNN clustering.

Author: Guande Wu
"""

# === Standard Library ===
import os
import json
from typing import List, Optional

# === Third-party Libraries ===
import torch
import numpy as np
from PIL import Image
import cv2
from sklearn.neighbors import NearestNeighbors
from torchvision import models, transforms
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection


def select_k_evenly(arr: List, k: int) -> List:
    """
    Selects k elements evenly distributed from the input list.

    :param arr: List of items.
    :type arr: List
    :param k: Number of elements to select.
    :type k: int
    :returns: Subset of `arr` with k evenly spaced elements.
    :rtype: List
    """
    n = len(arr)
    if k > n:
        return arr
    step = n / k
    return [arr[int(i * step)] for i in range(k)]


class FrameSelectorModule:
    """
    Selects informative frames using object detection and KNN-based feature clustering.
    """

    def __init__(self, init_valid_objects: Optional[List[str]] = None):
        self.device = torch.device("cuda:1" if torch.cuda.is_available() else "cpu")

        # Load OWL-ViT for object detection
        checkpoint = "google/owlv2-base-patch16-ensemble"
        self.model = AutoModelForZeroShotObjectDetection.from_pretrained(checkpoint).to(self.device)
        self.processor = AutoProcessor.from_pretrained(checkpoint)

        # Feature extractor
        self.feature_extractor = models.resnet50(pretrained=True).to(self.device)
        self.feature_extractor = torch.nn.Sequential(*list(self.feature_extractor.children())[:-1])
        self.feature_extractor.eval()

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        self.valid_object_list = init_valid_objects or ['grinder', 'cup', 'coffee', 'mug', 'filter', 'dripper']
        self.knn_model = None
        self.n_neighbors = 5
        self.frame_buffer = []
        self.index = 0
        self.selected_frames = []

    def process_frame(self, frame: Image.Image) -> None:
        self.frame_buffer.append(frame)
        self.index += 1
        if self.index % 30 == 1:
            self.process_frame_selection()

    def process_frame_selection(self):
        frames = self.fetch_frames()
        filtered_frames, frame_features = self.filter_frames(frames)
        self.knn_model = self.update_knn_model(frame_features)
        keyframe_indices = self.perform_knn_inference(frame_features)
        keyframe_indices.sort()
        self.selected_frames = [frames[i] for i in keyframe_indices]

    def filter_frame(self, frame: Image.Image) -> bool:
        return self.detect_objects(frame)

    def detect_objects(self, image: Image.Image) -> bool:
        inputs = self.processor(text=self.valid_object_list, images=image, return_tensors="pt").to(self.device)
        outputs = self.model(**inputs)
        target_sizes = torch.tensor([image.size[::-1]])
        results = self.processor.post_process_object_detection(outputs, threshold=0.1, target_sizes=target_sizes)[0]
        return any(score > 0.1 for score in results["scores"].tolist())

    def filter_frames(self, frames: List[Image.Image]) -> (List[int], List[np.ndarray]):
        filtered_indices = []
        features = []
        for idx, frame in enumerate(frames):
            features.append(self.extract_features(frame))
            filtered_indices.append(idx)
        return filtered_indices, features

    def extract_features(self, image: Image.Image) -> np.ndarray:
        image = self.transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            features = self.feature_extractor(image).squeeze().cpu().numpy()
        return features

    def update_knn_model(self, frame_features: List[np.ndarray]) -> Optional[NearestNeighbors]:
        if not frame_features:
            return self.knn_model
        features = np.array(frame_features)
        if self.knn_model is None:
            self.knn_model = NearestNeighbors(n_neighbors=self.n_neighbors, metric='euclidean')
        self.knn_model.fit(features)
        return self.knn_model

    def perform_knn_inference(self, frame_features: List[np.ndarray], top_k: int = 6) -> List[int]:
        if not self.knn_model or len(frame_features) < self.n_neighbors:
            return list(range(len(frame_features)))
        distances, _ = self.knn_model.kneighbors(frame_features)
        total_distances = np.sum(distances, axis=1)
        return list(np.argsort(total_distances)[-top_k:])

    def fetch_frames(self) -> List[Image.Image]:
        buffered = self.frame_buffer.copy()
        self.frame_buffer.clear()
        self.knn_model = None
        return buffered

    def fetch_valid_frames(self) -> List[Image.Image]:
        return self.selected_frames

    def fetch_latest_frames(self, k: int = 3) -> Optional[List[Image.Image]]:
        selected_frames = self.selected_frames[-30:]
        return select_k_evenly(selected_frames, k) if selected_frames else None

    def set_valid_objects(self, new_valid_objects: List[str]) -> None:
        self.valid_object_list = new_valid_objects

    def save_selected_frames(self, selected_frames: List[Image.Image], save_directory: str = "selected_frames") -> None:
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
        for idx, frame in enumerate(selected_frames):
            path = os.path.join(save_directory, f"frame_{idx}.jpg")
            frame.save(path)
            print(f"Saved frame {idx} to {path}")

    def send_to_output_stream(self, selected_frames: List[Image.Image]) -> None:
        output_message = json.dumps({"selected_frames": [frame.info for frame in selected_frames]})
        self.save_selected_frames(selected_frames)
        # self.publish(FrameSelectorPipeline.OUTPUT_STREAM, output_message)
