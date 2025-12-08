import json
import sys
from datetime import datetime
from LoggingSetup import *
from MP5Config import MP5Config
from Exceptions import *
from MP5Encoder import MP5Encoder  
from MP5Decoder import MP5Decoder
from MP5Verifier import MP5Verifier
from pathlib import Path


def print_header():
    print(f"\n{Colors.CYAN}{Colors.BOLD}.mp5 - The #1 AI Video Extension on Earth 🌍{Colors.RESET}")
    print(f"{Colors.CYAN}.mp4 but on steroids {Colors.RESET}\n")

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
        print(f"{Colors.GREEN}{Colors.BOLD}🚀 SHIPPED SUCCESSFULLY{Colors.RESET}")
        print_separator()
        print(f"Output: {result['output_file']}")
        print(f"Size: {result['input_size_mb']:.2f} MB → {result['output_size_mb']:.2f} MB (lossless quality)")
        print(f"Time: {result['encoding_time_seconds']:.2f}s")
        print(f"Storage: {result['storage_layer']}")
        print(f"Features auto-extracted: {result['features_extracted']} (you're welcome)")
        print_separator()
        print()

        return 0
    except Exception as e:
        print(f"\n{Colors.RED}💀 Ship failed: {str(e)}{Colors.RESET}")
        return 1

def cmd_decode(args)->int:
    """Decode video with metadata"""
    if len(args) < 1:
        print("Error Decoder required <input.mp5>")
        print("usage: python mp5.py decode input.mp5")
        return 1
    input_mp5=args[0]
    output_file=None
    
    # Check if file exists
    if not Path(input_mp5).exists():
        print(f"{Colors.RED}❌ File not found: {input_mp5}{Colors.RESET}")
        return 1

    print_header()

    config=MP5Config()
    decoder=MP5Decoder(config)

    try:
        result=decoder.decode(input_mp5)

        print_separator()
        print(f"{Colors.GREEN}{Colors.BOLD}🔓 SECRETS UNLOCKED{Colors.RESET}")
        print_separator()

        if result.get("file_info"):
            info = result["file_info"]#----------
            print(f"MP5 Version: {info.get('mp5_version')}")
            # Format timestamp
            created = info.get('created', '')
            try:
                dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                created = dt.strftime('%b %d, %Y at %I:%M %p')
            except:
                pass
            print(f"Created: {created}")
            print(f"Original Hash: {info.get('original_hash', '')}")
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
        
        output_file = "outputs/output_metadata.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n📄 Metadata saved to: {output_file}")

        print("\nExtracted Data:")
        print(json.dumps(result, indent=2))

        print()
        return 0
    except Exception as e:
        print(f"\n{Colors.RED}✗ Decoding failed: {str(e)}{Colors.RESET}")
        return 1


def cmd_verify(args):
    """Verify command"""
    if len(args) < 1:
        print("Error: verify requires <input.mp5>")
        print("Usage: python mp5.py verify input.mp5")
        return 1
    
    input_mp5 = args[0]
    
    # Check if file exists
    if not Path(input_mp5).exists():
        print(f"{Colors.RED}❌ File not found: {input_mp5}{Colors.RESET}")
        return 1
    
    print_header()
    
    config = MP5Config()
    verifier = MP5Verifier(config)
    
    try:
        result = verifier.verify(input_mp5)
        
        print_separator()
        
        overall = result['overall']
        if overall == 'verified':
            print(f"{Colors.GREEN}{Colors.BOLD}✅ INTEGRITY CONFIRMED - We're good{Colors.RESET}")
        elif overall == 'partial':
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ PARTIAL - Something's sus{Colors.RESET}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ BROKEN - Not gonna lie, this is bad{Colors.RESET}")
        
        print_separator()
        print(f"File: {result['file']}")
        print(f"LSB Layer: {result['lsb_layer']['status']}")
        
        if result['lsb_layer'].get('features_count'):
            print(f"  Features: {result['lsb_layer']['features_count']}")
        
        print(f"Atom Layer: {result['atom_layer']['status']}")
        print(f"Overall: {overall.upper()}")
        print_separator()
        print()
        
        return 0 if overall == 'verified' else 1
    
    except Exception as e:
        print(f"\n{Colors.RED}💀 Verification crashed: {str(e)}{Colors.RESET}")
        return 1


def cmd_info(args):
    """Info command"""
    if len(args) < 1:
        print("Error: info requires <input.mp5>")
        print("Usage: python mp5.py info input.mp5")
        return 1
    
    input_mp5 = args[0]
    
    # Check if file exists
    if not Path(input_mp5).exists():
        print(f"{Colors.RED}❌ File not found: {input_mp5}{Colors.RESET}")
        return 1
    
    print_header()
    
    config = MP5Config()
    decoder = MP5Decoder(config)
    
    try:
        result = decoder.decode(input_mp5)
        
        print_separator()
        print(f"{Colors.CYAN}{Colors.BOLD}📊 FILE BREAKDOWN{Colors.RESET}")
        print_separator()
        
        print(f"\n📄 File: {input_mp5}")
        print(f"   Size: {Path(input_mp5).stat().st_size / (1024*1024):.2f} MB")
        
        if result.get("file_info"):
            info = result["file_info"]
            print(f"\n🔖 MP5 Info:")
            print(f"   Version: {info.get('mp5_version')}")
            created_raw = info.get('created', '')
            try:
                created_dt = datetime.fromisoformat(created_raw.replace('Z', '+00:00'))
                created_formatted = created_dt.strftime('%b %d, %Y at %I:%M %p')
            except:
                created_formatted = created_raw
            print(f"   Created: {created_formatted}")
            print(f"   Hash: {info.get('original_hash')}")
            
            if info.get("video_info"):
                vi = info["video_info"]
                print(f"\n🎬 Video:")
                print(f"   Resolution: {vi['width']}x{vi['height']}")
                print(f"   FPS: {vi['fps']:.2f}")
                print(f"   Duration: {vi['duration']:.2f}s")
                print(f"   Frames: {vi['frame_count']}")
        
        if result.get("ai_metadata"):
            print(f"\n🤖 AI Metadata (Hidden in LSB):")
            print(f"   Storage: LSB Steganography")
            print(f"   Payload Type: {result['ai_metadata'].get('payload_type')}")
            
            if result.get("auto_features"):
                print(f"\n📊 Auto-Extracted Features ({len(result['auto_features'])}):")
                features = result['auto_features']
                
                # Display key features
                print(f"   Blur Score: {features.get('blur_score', 0):.2f}")
                print(f"   Edge Density: {features.get('edge_density', 0):.4f}")
                print(f"   Motion Intensity: {features.get('motion_intensity', 0):.2f}")
                print(f"   Scene Cuts: {features.get('scene_cut_count', 0)}")
                print(f"   Static Frames: {features.get('static_frame_ratio', 0):.2%}")
                print(f"   Compression Artifacts: {features.get('compression_artifacts', 0):.4f}")
            
            if result.get("user_metadata"):
                print(f"\n💾 User Metadata:")
                user_meta = result['user_metadata']
                if len(json.dumps(user_meta)) > 200:
                    print(f"   {json.dumps(user_meta, indent=2)[:200]}...")
                else:
                    print(f"   {json.dumps(user_meta, indent=2)}")
        
        print(f"\n{Colors.RESET}")
        print_separator()
        print()
        
        return 0
    
    except Exception as e:
        print(f"\n{Colors.RED}✗ Error: {str(e)}{Colors.RESET}")
        return 1




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
            return cmd_encode(args)
        elif command == "decode":
            return cmd_decode(args)
        elif command == "verify":
            return cmd_verify(args)
        elif command == "info":
            return cmd_info(args)
        elif command == "help":
            show_help()
        else:
            raise ValidationError(f"Invalid command: {command}",{"Expected commands": "encode, decode, verify"})

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"\n{Colors.RED}Error: {str(e)}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()