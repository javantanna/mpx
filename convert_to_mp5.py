from bz2 import compress
from mutagen.mp4 import MP4
import json
import zlib
import base64
import shutil
import cv2
import numpy as np
import os

class Atom:
    HEADER="MP5_v1"
    VERSION=1.0
    
    def __init__(self) -> None:
        self.ai_metadata=None
        self.metadata=None
        

    def encode_metadata_atom(self,video_path : str , metadata_dict : dict ,output_path : str) -> bool:
        """Encode metadata into MP4 atom - FIXED VERSION"""
        try:
            
            if video_path != output_path:
                shutil.copy2(video_path, output_path)
                print(f"✓ Copied {video_path} → {output_path}")
                
            # Compress the JSON
            
            
            json_str = json.dumps(metadata_dict)
            compressed = zlib.compress(json_str.encode('utf-8'),level=9)
            b64_encoded = base64.b64encode(compressed).decode('utf-8')
            
            print("b64 encoded: "+b64_encoded)

            # Open the MP4 file
            try:
                video = MP4(output_path)
            except Exception as e:
                print("Error opening MP4 file:", e)
            
            print("video before: ") #TODO remove after
            print(video)


            # 3. Store in custom atom (mp5_metadata is our custom tag)
            video["©mp5"] = b64_encoded
            
            print("video after: ") #TODO remove after
            print(video)

            # 4. Save the file
            video.save()
            
            print(f"✓ Stored MP5 metadata in {output_path}")
            print(f"  Original size: {len(json_str)} bytes")
            print(f"  Compressed: {len(compressed)} bytes")
            print(f"  Base64: {len(b64_encoded)} bytes")
            return True
        
        except Exception as e:
            print(f"✗ Error encoding metadata atom: {e}")
            return False

    def decode_metadata_atom(self,mp5_file_path : str)->dict:
        """Decode metadata from MP4 atom - FIXED VERSION"""
        
        try:
            video=MP4(mp5_file_path)
            print(video)
            mp5_data=video.get('©mp5')
            if(not mp5_data):
                raise ValueError("No MP5 metadata found in video!")
            
            # Handle both list and string formats
            mp5_data=video['©mp5']
            
            # If it's a list (reading), take first element
            if isinstance(mp5_data, list):
                b64_data = mp5_data[0]
            else:
                b64_data = mp5_data
            
            if not b64_data:
                raise ValueError("No b64 data found in mp5_data!")
            
            print(f"✓ Found MP5 metadata: {len(b64_data)} bytes (base64)")
            
            # Decompress
            compressed = base64.b64decode(b64_data)
            json_str = zlib.decompress(compressed).decode('utf-8')
            
            print(f"✓ Decompressed to {len(json_str)} bytes")
            
            return json.loads(json_str)
            
            
        except Exception as e:
            print(f"✗ Error decoding metadata atom: {e}")
            return False

        


    
class LSB:
    
    
    def text_to_binary(self,text):
        """Convert text to binary string"""
        return ''.join(format(ord(char),'08b') for char in text)
    
    def binary_to_text(self,binary_string:str):
        """Convert binary string back to text"""
        #Ensure binary String length is multiple of 8
        padding= len(binary_string)%8
        
        if padding !=0:
            binary_string=binary_string[:-padding]
            
        chars=[binary_string[i:i+8] for i in range(0, len(binary_string) , 8)]
        text=''.join(chr(int(char,2)) for char in chars if int(char,2)!=0)
        return text
    
    
    def encode_byte_in_frame(self,frame,byte_binary):
        """Hide one 8-bit 'byte' in the LSB of the frame's first 8 pixels."""
        if(len(byte_binary)) != 8:
            raise ValueError("Must provide an 8-bit binary string (a byte)")
        
        flat_frame=frame.flatten()
        print(flat_frame)
        for i in range(8):
            # (flat_frame[i] & 0xFE) sets the last bit to 0
            # | int(byte_binary[i]) then sets it to the bit we want
            flat_frame[i]=(flat_frame[i] & 0xFE) | int(byte_binary[i])
            
        return flat_frame.reshape(frame.shape)
        
test="hello my name is javan"

lsb=LSB()
lsbinary=lsb.text_to_binary(test)

text=lsb.binary_to_text(lsbinary)
        
        
        
            


# test_data = {
#     "mp5_version": "1.0",
#     "transcript": "Hello world, this is a test",
#     "tags": ["demo", "test"]
# }
# mp5=Atom()
# mp5.encode_metadata_atom("input.mp4",test_data,"output.mp5")

# mp5_data=mp5.decode_metadata_atom("output.mp5")
# print(mp5_data)
