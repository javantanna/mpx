import cv2
from typing import Dict, Any
from src.MP5Config import MP5Config
from src.Exceptions import ValidationError
from pathlib import Path

class VideoUtils:
    """Video processing utilities"""

    @staticmethod
    def get_video_info(video_path: str)->Dict[str,Any]:
        """Extract video metadata using OpenCV"""
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValidationError(f"Cannot open video: {video_path}")

        info={
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "codec": int(cap.get(cv2.CAP_PROP_FOURCC)),
            "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
        }

        cap.release()
        return info

    @staticmethod
    def validate_video(video_path: str, config: MP5Config) -> bool:
        """Validate video file"""
        path=Path(video_path)

        if not path.exists():
            raise ValidationError(f"Video file not found: {video_path}")

        if path.suffix.lower() not in config.supported_formats:
            raise ValidationError(
                f"Unsupported format: {path.suffix}. "
                f"Supported: {config.supported_formats}"
            )

        # Try to open with OpenCV
        try:
            VideoUtils.get_video_info(video_path)
        except Exception as e:
            raise ValidationError(f"Invalid video file: {str(e)}")
        
        return True