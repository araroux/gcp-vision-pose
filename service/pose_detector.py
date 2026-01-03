# pose_detector.py
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List

import cv2
import numpy as np

# ★ここがポイント：mp.solutions を使わず直 import
from mediapipe.python.solutions import pose as mp_pose


POSE_LANDMARK_NAMES = [
    "NOSE",
    "LEFT_EYE_INNER", "LEFT_EYE", "LEFT_EYE_OUTER",
    "RIGHT_EYE_INNER", "RIGHT_EYE", "RIGHT_EYE_OUTER",
    "LEFT_EAR", "RIGHT_EAR",
    "MOUTH_LEFT", "MOUTH_RIGHT",
    "LEFT_SHOULDER", "RIGHT_SHOULDER",
    "LEFT_ELBOW", "RIGHT_ELBOW",
    "LEFT_WRIST", "RIGHT_WRIST",
    "LEFT_PINKY", "RIGHT_PINKY",
    "LEFT_INDEX", "RIGHT_INDEX",
    "LEFT_THUMB", "RIGHT_THUMB",
    "LEFT_HIP", "RIGHT_HIP",
    "LEFT_KNEE", "RIGHT_KNEE",
    "LEFT_ANKLE", "RIGHT_ANKLE",
    "LEFT_HEEL", "RIGHT_HEEL",
    "LEFT_FOOT_INDEX", "RIGHT_FOOT_INDEX",
]

@dataclass
class PoseResult:
    width: int
    height: int
    landmarks: List[Dict[str, Any]]
    inference_ms: int


class PoseDetector:
    def __init__(self) -> None:
        self._pose = mp_pose.Pose(
            static_image_mode=True,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
        )

    def detect_from_bytes(self, image_bytes: bytes) -> PoseResult:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Failed to decode image bytes")

        h, w = bgr.shape[:2]
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        t0 = time.time()
        r = self._pose.process(rgb)
        inference_ms = int((time.time() - t0) * 1000)

        landmarks: List[Dict[str, Any]] = []
        if r.pose_landmarks:
            for i, lm in enumerate(r.pose_landmarks.landmark):
                name = POSE_LANDMARK_NAMES[i] if i < len(POSE_LANDMARK_NAMES) else f"LM_{i}"
                landmarks.append({
                    "id": i,
                    "name": name,
                    "x": float(lm.x),
                    "y": float(lm.y),
                    "z": float(lm.z),
                    "visibility": float(lm.visibility),
                })

        return PoseResult(width=w, height=h, landmarks=landmarks, inference_ms=inference_ms)
