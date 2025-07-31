#!/usr/bin/env python3
"""
FFmpeg Utilities for NetCDF Animations
Centralized FFmpeg detection and codec management
"""

import subprocess
from typing import List, Dict, Any, Optional


class FFmpegManager:
    """Manages FFmpeg detection and codec availability."""
    
    def __init__(self):
        self.ffmpeg_available = False
        self.available_codecs = []
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check if ffmpeg is available and what codecs are supported."""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️  ffmpeg not found. Install ffmpeg for video creation.")
                self.ffmpeg_available = False
                self.available_codecs = []
            else:
                self.ffmpeg_available = True
                # Check for available codecs
                codec_result = subprocess.run(['ffmpeg', '-codecs'], 
                                            capture_output=True, text=True)
                if codec_result.returncode == 0:
                    codec_output = codec_result.stdout
                    self.available_codecs = []
                    if 'libx264' in codec_output:
                        self.available_codecs.append('libx264')
                    if 'libxvid' in codec_output:
                        self.available_codecs.append('libxvid')
                    if 'mpeg4' in codec_output:
                        self.available_codecs.append('mpeg4')
                    print(f"📹 Available codecs: {self.available_codecs}")
                else:
                    self.available_codecs = ['mpeg4']  # Default fallback
        except FileNotFoundError:
            print("⚠️  ffmpeg not found. Install ffmpeg for video creation.")
            self.ffmpeg_available = False
            self.available_codecs = []
    
    def get_codec_info(self) -> Dict[str, Any]:
        """Get information about available codecs and ffmpeg status."""
        info = {
            'ffmpeg_available': self.ffmpeg_available,
            'available_codecs': self.available_codecs,
            'recommended_codec': self._get_recommended_codec()
        }
        return info
    
    def _get_recommended_codec(self) -> Optional[str]:
        """Get the recommended codec based on availability."""
        if not self.available_codecs:
            return 'mpeg4'
        
        # Priority order: libx264 > libxvid > mpeg4
        if 'libx264' in self.available_codecs:
            return 'libx264'
        elif 'libxvid' in self.available_codecs:
            return 'libxvid'
        else:
            return 'mpeg4'
    
    def get_codecs_to_try(self) -> List[str]:
        """Get list of codecs to try in order of preference."""
        codecs_to_try = []
        
        # Add codecs in priority order
        if 'libx264' in self.available_codecs:
            codecs_to_try.append('libx264')
        if 'libxvid' in self.available_codecs:
            codecs_to_try.append('libxvid')
        if 'mpeg4' in self.available_codecs:
            codecs_to_try.append('mpeg4')
        
        # If no specific codecs found, try default
        if not codecs_to_try:
            codecs_to_try = ['mpeg4']
        
        return codecs_to_try
    
    def is_available(self) -> bool:
        """Check if FFmpeg is available."""
        return self.ffmpeg_available


# Global instance for easy access
ffmpeg_manager = FFmpegManager() 