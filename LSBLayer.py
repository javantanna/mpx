from MP5Config import MP5Config
import logging
import numpy as np
import cv2
from Exceptions import EncodingError,DecodingError
from typing import Optional
import click


logger=logging.getLogger("mp5")
class LSBLayer:
    def __init__(self,config:MP5Config):
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
    def _embed_in_frame(frame: np.ndarray,data_binary:str)->np.ndarray:
        """Embed binary data into frame using LSB"""
        data_len=len(data_binary)
        flat=frame.flatten().copy()

        #Embed length (32 bits)
        length_bin=format(data_len,'032b')

        # Loop specifically 32 times to embed the 32-bit length header
        for i in range(32):
            # STEP 1: PREPARE THE CANVAS (The Eraser)
            # -> We take the current pixel byte and use Bitwise AND with 0xFE (11111110).
            # -> This forces the Least Significant Bit (LSB) to become 0, 
            # -> effectively "clearing" the space for our new data.
            # -> If pixel was 101 (Odd), it becomes 100. If 100 (Even), it stays 100.
            pixel_lsb_cleared = flat[i] & 0xFE

            # STEP 2: PREPARE THE INK (The Data)
            # -> We take the specific character ('0' or '1') from our binary string
            # -> and convert it into an integer (0 or 1) so we can do math with it.
            secret_bit = int(length_bin[i])

            # STEP 3: WRITE THE DATA (The Pen)
            # -> We use Bitwise OR (|) to combine the cleared pixel and the secret bit.
            # -> Since the pixel's LSB is 0, the OR operation simply copies the secret bit into that slot.
            # -> (0 | 1 = 1) and (0 | 0 = 0).
            flat[i] = pixel_lsb_cleared | secret_bit



        # PHASE 2: EMBEDDING THE ACTUAL SECRET MESSAGE

        # SAFETY CHECK (The Loop Limit):
        # -> We use 'min(data_len, len(flat) - 32)' to compare two things:
        #    1. 'data_len': The amount of secret data we WANT to write.
        #    2. 'len(flat) - 32': The amount of empty pixel space we HAVE left 
        #       (Total pixels minus the 32 we already used for the header).
        # -> The loop stops at whichever number is smaller so we don't crash.
        for i in range(min(data_len, len(flat) - 32)):

            # STEP 2: PREPARE THE CANVAS (The Eraser)
            # -> We look at the pixel at our calculated index.
            # -> We use Bitwise AND (&) with 0xFE to force the last bit to 0.
            # -> This erases whatever random noise was in the LSB so it's clean.
            # -> 32+i is current pixel index(we already used forst 32 bits for header)
            cleared_pixel = flat[32 + i] & 0xFE

            # STEP 3: PREPARE THE INK (The Data)
            # -> We grab the current character from our secret binary string ('0' or '1').
            # -> We convert it to an integer so we can do math.
            secret_bit = int(data_binary[i])

            # STEP 4: WRITE THE DATA (The Pen)
            # -> We use Bitwise OR (|) to combine our cleared pixel and secret bit.
            # -> Since the pixel slot is 0, the OR operation writes our secret bit 
            # directly into that spot.
            flat[32 + i] = cleared_pixel | secret_bit


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

            temp_output=output_path + '.lsb_temp.mp4'
            fourcc=cv2.VideoWriter_fourcc(*'mp4v')
            # print(fourcc)
            out=cv2.VideoWriter(temp_output,fourcc,fps,(width,height))

            bits_written = 0
            frame_count = 0
            embedded=0
            with click.progressbar(length=total_frames, label='Embedding Stream') as bar:
                while cap.isOpened():
                    
                    ret,frame=cap.read()

                    if not ret:break
                    if bits_written < total_bits:

                        flat_len = frame.size  # Total pixels in this frame
                        current_pixel_idx = 0  # Start writing at the beginning of the frame

                        # --- FRAME 0 ONLY: WRITE HEADER ---
                        if frame_count==0:
                            # 1. Embed 32-bit Total Length Header
                            length_bin = format(total_bits, '032b')

                            frame=LSBLayer._embed_stream_chunk(frame, length_bin, start_offset=0)
                            current_pixel_idx = 32 # Move cursor past header

                        # --- WRITE DATA BODY ---
                        # Calculate space left in this frame
                        bits_available=flat_len - current_pixel_idx

                        # Calculate how many bits we can write in this frame
                        bits_needed=total_bits - bits_written
                        bits_to_write=min(bits_available,bits_needed)

                        if bits_to_write > 0:
                            # Slice the chunk from the main payload
                            chunk=data_binary[bits_written : bits_written + bits_to_write]

                            frame= LSBLayer._embed_stream_chunk(frame,chunk,current_pixel_idx)
                            bits_written+=bits_to_write
                    
                    out.write(frame)
                    frame_count+=1
                    bar.update(1)
            
            cap.release()
            out.release()

            # So now our mp5 video is ready ***but*** there is no audio in it bcoz cv2.VideoWriter doesn't support audio.
            # So we need to copy the audio from the original video to our new mp5 video.

            # USING FFMPEG
            logger.info("Embedding Audio")
            import subprocess
            subprocess.run([
                'ffmpeg',
                '-i', temp_output,
                '-i', video_path,
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-map', '0:v:0',
                '-map', '1:a:0?',
                output_path, '-y',
                '-loglevel', 'error'
            ])

            os.remove(temp_output)
            return True

        except Exception as e:
            raise EncodingError(f"LSBLayer.write() failed: {str(e)}")
    # TODO continue from here

    @staticmethod
    def read(mp5_video_path:str,max_frames:int=1000)->Optional[bytes]:
        try:
            cap=cv2.VideoCapture(mp5_video_path)
            
            # 1. Read frame 0 immediatrly, we assume Header is here
            ret,frame=cap.read()
            if not ret: return None

            flat=frame.flatten()
            
            # 2. EXTRACT HEADER
            # Read the LSBs of the first 32 pixels.
            length_bin= ''.join(str(flat[i] & 1) for i in range(32))

            # Convert binary to integer length to find the length of actual data 
            total_bits_expected=int(length_bin,2)

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


# fake_frame = np.arange(100, 150, dtype=np.uint8).reshape((5, 10))
# # print(fake_frame)
# secret_data = b"101"
# result=LSBLayer._embed_in_frame(fake_frame,secret_data)
# # print(result_frame)

LSBLayer.write("E:\mp5\input.mp4",b"Hello World", "E:\mp5\outputs\output.mp5")

print(LSBLayer.read("E:\mp5\outputs\output.mp5.lsb_temp.mp4"))


