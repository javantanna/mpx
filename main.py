from LoggingSetup import *
from MP5Config import MP5Config
from Exceptions import *
from MP5Encoder import MP5Encoder

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
    config=MP5Config()

    try:
        if command == "encode":
            if len(args)!= 2:
                print("Error: Usage is `encode <input.mp4> <json_file>`")
                sys.exit(1)
            
            input_video=sys.argv[2]
            metadata_file=sys.argv[3]

            with open(metadata_file,'r') as f:
                metadata.json.load(f)
            encoder= MP5Encoder(config)

        elif command == "decode":
        
        elif command == "verify":
        
        else:
            raise ValidationError(f"Invalid command: {command}",{"Expected commands": "encode, decode, verify"})

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


