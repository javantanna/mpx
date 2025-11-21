import cv2
import numpy as np
import os

# --- Your original helper functions (unchanged) ---

def text_to_binary(text):
    """Convert text to binary string"""
    return ''.join(format(ord(char), '08b') for char in text)

def binary_to_text(binary_str):
    """Convert binary string back to text"""
    # Ensure the binary string length is a multiple of 8
    padding = len(binary_str) % 8
    if padding != 0:
        binary_str = binary_str[:-padding] # Discard incomplete byte
        
    chars = [binary_str[i:i+8] for i in range(0, len(binary_str), 8)]
    return ''.join(chr(int(char, 2)) for char in chars if int(char, 2) != 0)

# --- New, simpler LSB functions ---

def encode_byte_in_frame(frame, byte_binary):
    """Hide one 8-bit 'byte' in the LSB of the frame's first 8 pixels."""
    if len(byte_binary) != 8:
        raise ValueError("Must provide an 8-bit binary string (a byte)")
    
    flat_frame = frame.flatten()
    for i in range(8):
        # (flat_frame[i] & 0xFE) sets the last bit to 0
        # | int(byte_binary[i]) then sets it to the bit we want
        flat_frame[i] = (flat_frame[i] & 0xFE) | int(byte_binary[i])
    
    return flat_frame.reshape(frame.shape)

def decode_byte_from_frame(frame):
    """Extract one 8-bit 'byte' from the frame's first 8 pixels."""
    flat_frame = frame.flatten()
    byte_binary = ''.join(str(flat_frame[i] & 1) for i in range(8))
    return byte_binary

# --- New Main Video Functions ---

def encode_video(input_video_path, message, output_video_path):
    """
    Hides a secret message within a video file, spreading it one
    byte (character) per frame.
    """
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print(f"Error: Could not open input video {input_video_path}")
        return

    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') # 'mp4v' for .mp4
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

    # --- Prepare Data ---
    data_binary = text_to_binary(message)
    data_len = len(data_binary)
    
    # 1. Prepare Header: 32-bit string of the data's length
    header_binary = format(data_len, '032b')
    header_bytes = [header_binary[i:i+8] for i in range(0, 32, 8)] # 4 chunks of 8 bits
    
    # 2. Prepare Data: List of 8-bit chunks
    data_bytes = [data_binary[i:i+8] for i in range(0, data_len, 8)]
    
    total_frames_needed = len(header_bytes) + len(data_bytes)
    
    frame_num = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break # End of video
        
        # --- Start Encoding ---
        if frame_num < len(header_bytes):
            # Stage 1: Hide header (length)
            byte_to_hide = header_bytes[frame_num]
            frame = encode_byte_in_frame(frame, byte_to_hide)
            
        elif (frame_num - len(header_bytes)) < len(data_bytes):
            # Stage 2: Hide data
            data_index = frame_num - len(header_bytes)
            byte_to_hide = data_bytes[data_index]
            frame = encode_byte_in_frame(frame, byte_to_hide)
        
        # Stage 3: Write the frame (either modified or original)
        out.write(frame)
        frame_num += 1

    print(f"Successfully encoded message into {output_video_path}")
    print(f"Frames used: {total_frames_needed}")
    
    cap.release()
    out.release()

def decode_video(video_path):
    """
    Extracts a secret message from a video file.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return

    # --- Stage 1: Read Header (first 4 frames) ---
    header_binary = ""
    for i in range(4): # 4 frames for 32 bits
        ret, frame = cap.read()
        if not ret:
            print("Error: Video is too short to contain a header.")
            cap.release()
            return
        header_binary += decode_byte_from_frame(frame)
    
    data_len = int(header_binary, 2)
    num_data_frames = data_len // 8
    
    # --- Stage 2: Read Data ---
    data_binary = ""
    for i in range(num_data_frames):
        ret, frame = cap.read()
        if not ret:
            print("Error: Video ended unexpectedly while reading data.")
            cap.release()
            return
        data_binary += decode_byte_from_frame(frame)

    cap.release()
    
    # --- Convert to text ---
    secret_message = binary_to_text(data_binary)
    return secret_message

# --- Helper to create a dummy video for testing ---
def create_dummy_video(filename="input.mp4", duration_sec=5, fps=30):
    print(f"Creating dummy video: {filename}")
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    for i in range(duration_sec * fps):
        # Create a simple frame with noise
        frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        # Add a frame number
        cv2.putText(frame, f'Frame {i}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (255, 255, 255), 2)
        out.write(frame)
    out.release()
    print("Dummy video created.")

# --- Main part to run the test ---
if __name__ == "__main__":
    
    IN_VIDEO = "input.mp4"
    OUT_VIDEO = "output_ai_meta.mp4"
    
    # 1. Create a dummy video to work with
    if not os.path.exists(IN_VIDEO):
        create_dummy_video(IN_VIDEO)
    
    # 2. Define your AI metadata
    # This can be any complex dictionary
    my_ai_metadata = {
        "model_name": "ObjectDetector_v3.1",
        "timestamp": "2025-11-13T15:45:00Z",
        "confidence_threshold": 0.85,
        "frames_processed": 1450,
        "objects_found": [
            {"label": "car", "count": 4},
            {"label": "person", "count": 2},
            {"label": "dog", "count": 1}
        ]
    }

    # 3. Encode the secret
    print(f"\nEncoding metadata...")
    
    # ----- THIS IS THE NEW STEP (ENCODE) -----
    # 'dumps' = DUMP to String
    message_string = json.dumps(my_ai_metadata)
    # ----------------------------------------
    
    # Now, just pass this simple string to your existing function
    encode_video(IN_VIDEO, message_string, OUT_VIDEO)
    
    # 4. Decode the secret
    print(f"\nDecoding metadata from {OUT_VIDEO}...")
    
    # Your existing function returns the simple string
    extracted_string = decode_video(OUT_VIDEO)
    
    # ----- THIS IS THE NEW STEP (DECODE) -----
    # 'loads' = LOAD from String
    try:
        extracted_metadata = json.loads(extracted_string)
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from video.")
        extracted_metadata = None
    # ----------------------------------------

    
    # 5. Check if it worked
    print("---" * 10)
    print("Decoded Metadata:")
    # Use json.dumps for pretty printing the dictionary
    if extracted_metadata:
        print(json.dumps(extracted_metadata, indent=2))
    print("---" * 10)
    
    if extracted_metadata == my_ai_metadata:
        print("✅ Success! The metadata matches perfectly.")
    else:
        print("❌ Failure! The metadata does not match.")