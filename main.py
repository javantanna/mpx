import json
import sys
from LoggingSetup import *
from MP5Config import MP5Config
from Exceptions import *
from MP5Encoder import MP5Encoder  
from MP5Decoder import MP5Decoder

def print_header():
    print(f"\n{Colors.CYAN}{Colors.BOLD}MP5 - Enterprise Video Metadata Tool{Colors.RESET}")
    print(f"{Colors.CYAN}Version 1.0.0 - Auto Feature Extraction{Colors.RESET}\n")

def cmd_encode(args):
    """Encode video with metadata"""
    if len(args) != 2:
        raise ValidationError("Usage: encode <input.mp4> <metadata.json>")

    input_video=args[0]
    metadata_file=args[1]
    
    print_header()
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"{Colors.RED} error loading metadata {str(e)}{Colors.RESET}")
        return 1
    
    config= MP5Config()
    encoder= MP5Encoder(config)
    
    try:
        result = encoder.encode(input_video, metadata)

        # Display results
        print_separator()
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ENCODING SUCCESSFUL{Colors.RESET}")
        print_separator()
        print(f"Output: {result['output_file']}")
        print(f"Input size:  {result['input_size_mb']:.2f} MB")
        print(f"Output size: {result['output_size_mb']:.2f} MB")
        print(f"Size increase: {result['size_increase_percent']:.3f}%")
        print(f"Encoding time: {result['encoding_time_seconds']:.2f}s")
        print(f"Storage: {result['storage_layer']}")
        print(f"Features extracted: {result['features_extracted']}")
        print_separator()
        print()

        return 0
    except Exception as e:
        print(f"\n{Colors.RED}✗ Encoding failed: {str(e)}{Colors.RESET}")
        return 1

def cmd_decode(args)->int:
    """Decode video with metadata"""
    if len(args) < 1:
        print("Error Decoder required <input.mp5>")
        print("usage: python mp5.py decode input.mp5")
        return 1
    input_mp5=args[0]
    output_file=None
    

    print_header()

    config=MP5Config()
    decoder=MP5Decoder(config)

    try:
        result=decoder.decode(input_mp5)

        print_separator()
        print(f"{Colors.GREEN}{Colors.BOLD}✓ DECODING SUCCESSFUL{Colors.RESET}")
        print_separator()

        if result.get("file_info"):
            info = result["file_info"]#----------
            print(f"MP5 Version: {info.get('mp5_version')}")
            print(f"Created: {info.get('created')}")
            print(f"Original Hash: {info.get('original_hash', '')[:16]}...")
        print()

        ai_metadata = result.get("ai_metadata", {})
        if ai_metadata:
            print(f"{Colors.CYAN}Hidden AI Metadata Found:{Colors.RESET}")
            auto_features = ai_metadata.get("auto_features", {})
            user_metadata = ai_metadata.get("user_metadata", {})
            print(f"  Auto-features: {len(auto_features)} features")
            print(f"  User metadata: {len(user_metadata)} keys")
        else:
            print(f"{Colors.YELLOW}⚠ No hidden AI metadata found{Colors.RESET}")

        print_separator()
        
        with open("metadata.json", 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nMetadata saved to: {output_file}")

        print("\nExtracted Data:")
        print(json.dumps(result, indent=2))

        print()
        return 0
    except Exception as e:
        print(f"\n{Colors.RED}✗ Decoding failed: {str(e)}{Colors.RESET}")
        return 1

def print_header():
    print(f"\n{Colors.CYAN}{Colors.BOLD}MP5 - Enterprise Video Metadata Tool{Colors.RESET}")
    print(f"{Colors.CYAN}Version 1.0.0 - Auto Feature Extraction{Colors.RESET}\n")


def print_separator():
    print("=" * 60)

def show_help():
    print("""
Usage:
    python mp5.py encode <input.mp4> <user_metadata.json>
    python mp5.py decode <input.mp5>
    python mp5.py verify <input.mp5>
    python mp5.py info <input.mp5>
    python mp5.py help

Commands:
    encode    Auto-extract features and embed in video (LSB layer)
    decode    Extract hidden AI metadata from video
    verify    Verify integrity and presence of hidden metadata
    info      Show detailed file information
    help      Show this help message

Examples:
    # Encode (auto-generates features)
    python mp5.py encode video.mp4 metadata.json output.mp5
    
    # Decode
    python mp5.py decode output.mp5
    
    # Verify
    python mp5.py verify output.mp5

Features Auto-Extracted:
    - blur_score, noise_level, compression_artifacts
    - dynamic_range, edge_density, texture_complexity
    - letterbox_ratio, rule_of_thirds_score
    - motion_intensity, static_frame_ratio, camera_shake
    - scene_cut_count, volume_rms, audio_peak, silence_ratio
""")



def main():
    log_file="mp5.log"
    logger = setup_logging(log_file=log_file)

    if len(sys.argv) < 2:
        print("\n Create the best video for AI on the Internet : MP5 ")
        print("  Encode: python mp5.py encode <input.mp4> <metadata.json>")
        print("  Decode: python mp5.py decode <input.mp5> (or you can just rename the file)")
        print("  Verify: python mp5.py verify <input.mp5>")
        sys.exit(1)
    
    command=sys.argv[1].lower()
    args=sys.argv[2:]

    try:
        if command == "encode":
            cmd_encode(args)
        elif command == "decode":
            cmd_decode(args)
        # elif command == "verify":
        
        else:
            raise ValidationError(f"Invalid command: {command}",{"Expected commands": "encode, decode, verify"})

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()