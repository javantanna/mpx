from MP5Config import MP5Config
import numpy as np
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




# fake_frame = np.arange(100, 150, dtype=np.uint8).reshape((5, 10))
# # print(fake_frame)
# secret_data = b"101"
# result=LSBLayer._embed_in_frame(fake_frame,secret_data)
# # print(result_frame)
