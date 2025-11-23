from LoggingSetup import *
from MP5Config import MP5Config
from Exceptions import *
from MP5Encoder import MP5Encoder

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


def main():
    log_file="mp5.log"
    setup_logging(log_file=log_file)

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
        
        elif command == "verify":
        
        else:
            raise ValidationError(f"Invalid command: {command}",{"Expected commands": "encode, decode, verify"})

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


