import logging
import cv2
import numpy as np
from typing import Dict, Any
from utils.ProgressBar import ProgressBar
import ffmpeg
from moviepy import VideoFileClip
import json
np.set_printoptions(threshold=np.inf)

logger = logging.getLogger("mpx")

class FeatureExtractor:
    """Extract video features using OpenCV and NumPy"""

    @staticmethod
    def extract_all_features(video_path: str) -> Dict[str, Any]:
        """Extract all features from video"""
        logger.info("🔭 Scanning frames like a hawk...")

        cap = cv2.VideoCapture(video_path)

        features={
            "blur_score": 0.0,
            "noise_level": 0.0,
            "dynamic_range": 0.0,
            "edge_density": 0.0,
            "texture_complexity": 0.0,
            "letterbox_ratio": 0.0,
            "rule_of_thirds_score": 0.0,
            "motion_intensity": 0.0,
            "static_frame_ratio": 0.0,
            "camera_shake": 0.0,
            "scene_cut_count": 0,
            "has_audio": False,
            "volume_rms": 0.0,
            "audio_peak": 0.0,
            "silence_ratio": 0.0
        }

        frame_count = 0
        prev_frame = None
        motion_scores = []
        blur_scores = []
        static_frames=0
        scene_cuts=0
        
        total_frames=int((cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        sample_rate= max(1, int(total_frames/30))
        progress_bar=ProgressBar(total=total_frames, label="Extracting features")
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            # Sample frames to save processing time
            if frame_count % sample_rate == 0:
                gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


                #Blur Detection (Laplacian Variance)
                laplacian=cv2.Laplacian(gray, cv2.CV_64F)
                blur_score=laplacian.var()
                blur_scores.append(blur_score)
                
                #Edge Density
                edges=cv2.Canny(gray,50,150)
                edge_density=np.count_nonzero(edges)/edges.size
                features["edge_density"] += edge_density


                # Texture Complexity (standard Deviation)
                features["texture_complexity"] += gray.std()

                #Dynamic Range
                features["dynamic_range"] += gray.max() - gray.min()
                
                # Letterbox detection (check top/bottom rows)
                top_row=gray[0:int(gray.shape[0] * 0.1) : ].mean()
                bottom_row=gray[int(gray.shape[0] * 0.9) :].mean()
                if top_row < 20 and bottom_row < 20:
                    features["letterbox_ratio"] += 1
                
                # Rule of thirds (check if content in center vs edges)
                height,width=gray.shape
                start_row = height // 3
                start_column = width // 3

                center = gray[start_row: 2 * start_row , start_column: 2 * start_column].mean()
                full=gray.mean()
                if full > 0:
                    features["rule_of_thirds_score"] += center / full


                # Motion Detection
                if prev_frame is not None:
                    diff = cv2.absdiff(prev_frame, gray)
                    motion_score = diff.mean()
                    motion_scores.append(motion_score)

                    # Static frame detection
                    if motion_score > 5:
                        static_frames += 1
                    
                    # Scene cut detection
                    if motion_score > 30:
                        scene_cuts += 1

                    # Camera shake (high-frequency motion)
                    features["camera_shake"] += diff.std()

                prev_frame=gray.copy()
            frame_count+=1
            progress_bar.update(1)
        cap.release()
        
        # Average out accumulated features
        sampled_frames= frame_count / sample_rate
        if sampled_frames > 0:
            features["blur_score"] = float(np.mean(blur_scores)) if blur_scores else 0.0
            features["noise_level"] = float(np.std(blur_scores)) if blur_scores else 0.0
            features["edge_density"] = features["edge_density"] / sampled_frames
            features["texture_complexity"] = features["texture_complexity"] / sampled_frames
            features["dynamic_range"] = features["dynamic_range"] / sampled_frames
            features["letterbox_ratio"] = features["letterbox_ratio"] / sampled_frames
            features["rule_of_thirds_score"] = features["rule_of_thirds_score"] / sampled_frames
            features["motion_intensity"] = float(np.mean(motion_scores)) if motion_scores else 0.0
            features["static_frame_ratio"] = static_frames / sampled_frames
            features["camera_shake"] = features["camera_shake"] / sampled_frames
            features["scene_cut_count"] = scene_cuts
        
        # Audio features (if available)
        if FeatureExtractor._has_audio(video_path):
            audio_features=FeatureExtractor.extract_audio_features(video_path)
            features.update(audio_features)
            
        logger.info("🌟 Features locked and loaded")
        return features
                    


    @staticmethod
    def _has_audio(video_path:str)->bool:
        try:
            # "probe" just reads the metadata, doesn't decode the file
            probe = ffmpeg.probe(video_path)
            
            # Look through all streams (video, audio, subtitle)
            # and check if any of them are 'audio'
            for stream in probe['streams']:
                if stream['codec_type'] == 'audio':
                    return True
                
            return False
        except ffmpeg.Error as e:   
            print(f"File error: {e}")
            return False

    @staticmethod
    def extract_audio_features(video_path:str)->Dict[str, Any]:
        """Extract audio features from video"""
        logger.info("🎵 Listening to the audio vibes...")
        features={
            "volume_rms": 0.0,
            "audio_peak": 0.0,
            "silence_ratio": 0.0,
            "has_audio": False
        }
        try:
            # 1. Load video, but don't parse frames yet
            clip = VideoFileClip(video_path)

            # 2. Fast Fail: If no audio, return 0s
            if clip.audio is None:
                clip.close()
                return features
            # 3. Extract Audio -> Numpy Array
            # fps=16000: Low sample rate makes extracting 3x faster than default
            # data is array of floats between -1.0 and 1.0
            data = clip.audio.to_soundarray(fps=16000)
            clip.close()

            # 4. Merge Stereo to Mono (if needed) for simple math
            if data.ndim > 1:
                data = data.mean(axis=1)

            # 5. The Math (Vectorized = Instant)
            abs_data = np.abs(data)
            
            features["audio_peak"] = float(np.max(abs_data))
            features["volume_rms"] = float(np.sqrt(np.mean(data**2)))
            features["silence_ratio"] = float(np.mean(abs_data < 0.01))
            features["has_audio"] = True

        except Exception:
            pass  # Return 0.0s on error

        return features