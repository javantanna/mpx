from src.MPXConfig import MPXConfig
import logging
import numpy as np
import cv2
import os
from src.Exceptions import EncodingError,DecodingError
from typing import Optional
import click


logger=logging.getLogger("mpx")
class LSBLayer:
    def __init__(self,config:MPXConfig):
        self.config=config

    @staticmethod
    def _text_to_binary(text:str)->bytes:
        """Convert text to binary string"""
        return ''.join(format(ord(c),'08b') for c in text)
    
    @staticmethod
    def _binary_to_text(binary:str)->str:
        """Convert binary string to text"""
        chars=[binary[i:i+8] for i in range(0,len(binary),8)]
        return ''.join(chr(int(c,2)) for c in chars if len(c)==8)
    


    @staticmethod
    def _embed_stream_chunk(frame: np.ndarray, data_chunk: str, start_offset: int = 0) -> np.ndarray:
        # 1. We take the 3D frame (Height, Width, Colors) and squash it into a 1D line of numbers.
        # Why? It's easier to say "Pixel #500" than "Row 10, Col 20".
        flat=frame.flatten()
        
        # 2. We calculate how many bits we are trying to write right now.
        chunk_len=len(data_chunk)

        # 3. SAFETY CHECK:
        # If the data is too long for the rest of the frame, cut the data short.
        # This prevents the code from crashing if we run out of pixels in this specific frame.
        if start_offset + chunk_len > len(flat):
            chunk_len = len(flat) - start_offset
            data_chunk = data_chunk[:chunk_len]

        # 4. THE CORE LOOP:
        # We iterate through every bit of our data chunk.
        for i in range(chunk_len):
            # bitwise AND (& 0xFE): This forces the last bit of the pixel to 0 (Clears space).
            # bitwise OR (| data): This puts our data bit (0 or 1) into that empty spot.
            # We start writing at 'start_offset' (e.g., pixel 0 or pixel 32).
            cleared_pixel=flat[start_offset + i] & 0xFE
            secret_bit=int(data_chunk[i])

            flat[start_offset + i] = cleared_pixel | secret_bit
        
        # 5. We inflate the 1D line back into a 3D picture and return it.
        return flat.reshape(frame.shape)

        

    @staticmethod
    def write(video_path: str, ai_metadata: bytes, output_path: str) -> bool:
        try:
            data_str=ai_metadata.decode('utf-8')
            data_binary=LSBLayer._text_to_binary(data_str)
            total_bits = len(data_binary)

            logger.info(f"LSB encoding: {len(data_str)} chars -> {len(data_binary)} bits")

            cap=cv2.VideoCapture(video_path)
            #gatherin video info
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            # Check capacity
            # 3 channels (RGB) * width * height = bits per frame
            bits_per_frame = width * height * 3
            if total_bits + 32 > bits_per_frame * total_frames:
                    raise EncodingError("Data too large for this video container!")

            # Use PNG sequence for lossless intermediate storage
            temp_dir = output_path + "_temp_frames"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            bits_written = 0
            frame_count = 0
            embedded=0
            
            with click.progressbar(length=total_frames, label='Embedding Stream') as bar:
                while cap.isOpened():
                    
                    ret,frame=cap.read()

                    if not ret:break
                    if bits_written < total_bits:

                        flat_len = frame.size
                        current_pixel_idx = 0

                        # --- FRAME 0 ONLY: WRITE HEADER ---
                        if frame_count==0:
                            length_bin = format(total_bits, '032b')
                            frame=LSBLayer._embed_stream_chunk(frame, length_bin, start_offset=0)
                            current_pixel_idx = 32

                        # --- WRITE DATA BODY ---
                        bits_available=flat_len - current_pixel_idx
                        bits_needed=total_bits - bits_written
                        bits_to_write=min(bits_available,bits_needed)

                        if bits_to_write > 0:
                            chunk=data_binary[bits_written : bits_written + bits_to_write]
                            frame= LSBLayer._embed_stream_chunk(frame,chunk,current_pixel_idx)
                            bits_written+=bits_to_write
                    
                    # Save as PNG (lossless)
                    frame_path = os.path.join(temp_dir, f"frame_{frame_count:05d}.png")
                    cv2.imwrite(frame_path, frame)
                    
                    frame_count+=1
                    bar.update(1)
            
            cap.release()

            # USING FFMPEG with FFV1 (Optimized - Best lossless compression for LSB)
            logger.info("Embedding Audio & Converting to FFV1 (Optimized)")
            import subprocess
            subprocess.run([
                'ffmpeg',
                '-framerate', str(fps),
                '-i', os.path.join(temp_dir, 'frame_%05d.png'),
                '-i', video_path,
                '-c:v', 'ffv1',         # FFV1 codec (best for lossless)
                '-level', '3',          # FFV1 version 3 (better compression)
                '-coder', '1',          # Range coder (better than Golomb-Rice)
                '-context', '1',        # Large context (better compression, slower)
                '-g', '1',              # Intra-only (no inter-frame prediction)
                '-slices', '24',        # More slices for better multi-threading
                '-slicecrc', '1',       # Error detection
                '-c:a', 'copy',         # Copy audio
                '-map', '0:v:0',
                '-map', '1:a:0?',
                '-f', 'mp4',
                output_path, '-y',
                '-loglevel', 'error'
            ])

            # Cleanup
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return True
            return True

        except Exception as e:
            raise EncodingError(f"LSBLayer.write() failed: {str(e)}")
    # TODO continue from here

    @staticmethod
    def read(mpx_video_path:str,max_frames:int=1000)->Optional[bytes]:
        try:
            cap=cv2.VideoCapture(mpx_video_path)
            
            # 1. Read frame 0 immediatrly, we assume Header is here
            ret,frame=cap.read()
            if not ret: return None

            flat=frame.flatten()
            
            # 2. EXTRACT HEADER
            # Read the LSBs of the first 32 pixels.
            length_bin= ''.join(str(flat[i] & 1) for i in range(32))

            # Convert binary to integer length to find the length of actual data 
            total_bits_expected=int(length_bin,2)

            # Initialize data collection
            full_binary_data = []
            bits_read = 0

            # safety check to ensure we didn't just reading random noise
            if total_bits_expected <=0 or total_bits_expected > max_frames * frame.shape[0] * frame.shape[1] * 3:
                return None

            # 3. EXTRACT DATA from frame 0
            # Calculate how much data fits in Frame 0 (Total pixels minus 32 for header).
            bits_in_frame0=min(total_bits_expected,len(flat)-32)
            chunk0= ''.join(str(flat[32+i] & 1) for i in range(bits_in_frame0))

            full_binary_data.append(chunk0)
            bits_read+=bits_in_frame0
            
            
            # 4. LOOP THROUGH REMAINING FRAMES
            # Keep reading new frames until we have collected 'total_bits_expected'.
            while bits_read < total_bits_expected:
                ret,frame=cap.read()
                if not ret: break
                
                flat=frame.flatten()
                
                # Calculate how much data we need to read
                bits_needed=total_bits_expected-bits_read
                
                # Take either what we need, or the whole frame if we need more.
                bits_to_take=min(len(flat),bits_needed)

                #read bits in frame from pixel 0 (and not header in it)
                chunk=''.join(str(flat[i] & 1) for i in range(bits_to_take))

                full_binary_data.append(chunk)
                bits_read+=bits_to_take

            # 5. COMBINE ALL DATA
            #Glue all the chunks together
            full_binary_data=''.join(full_binary_data)

            # Convert Binary -> Text -> Bytes -> Return
            data_str=LSBLayer._binary_to_text(full_binary_data)
            data_bytes=data_str.encode('utf-8')
            return data_bytes

        except Exception as e:
            raise DecodingError(f"LSBLayer.read() failed: {str(e)}")
