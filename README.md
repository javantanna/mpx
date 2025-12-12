<div align="center">

# .MP5 
#### *The BEST AI Video Format on Earth 🌍*
mp4 but on steroids

---


<img src="assets/logo.jpg" alt="MP5 Logo" width="200"/>

**Version 1.0.0** | **License Apache 2.0** | **Cross-platform**





</div>

---

## 📖 What Is MP5?

Here's the thing. We've been using MP4 for videos for like 20 years. It works. But it was built for a different era—when videos were just for people to watch.

Now we're training AI models on millions of videos. And every video needs metadata. Where it came from. How it was generated. What's actually in it. The technical parameters. All of it.

So where do you put that data? In a separate file? In a database? That's a mess. Files get lost. Databases get out of sync. It breaks.

**MP5 fixes this.**

It's a video format that stores everything—the video AND all its AI metadata—in one single file. Hidden. Lossless. Automatically extracted.

Think of it like this: MP4 stores the video. MP5 stores the video plus everything an AI needs to understand it.

Same compatibility. Same playback. But actually useful for the AI age.

That's it. That's MP5.

---

## 🔮 The Vision (Why MP5 Exists)

We're at the start of something big with AI and video. In the next few years, we'll be training models on billions of videos. Building systems that understand scenes in real-time. Creating experiences we can't predict yet.

But here's the problem: **the infrastructure isn't ready**.

Right now, working with video for AI is broken. You've got the video file in one place. Metadata in a database. Features in a CSV. Training parameters in another system. When you move datasets or share them, you're juggling five different pieces and hoping they stay synced.

That doesn't scale. And it blocks the innovation we need.

**MP5 fixes this by making video intelligent by default.**

Every video knows what it is. Metadata travels with the file automatically. AI features are extracted once and embedded forever. Everything self-contained. No external dependencies.

This isn't about replacing MP4 for streaming or YouTube. It's about building the format that should exist for AI-first workflows—training, datasets, automation, video intelligence at scale.

When you have millions of videos with perfect metadata built-in, you unlock things that are impossible today. Better training pipelines. Smarter automation. Systems that actually work.

This is infrastructure work. Not flashy. But it's the foundation for everything else.

That's why MP5 exists.

---

## ⚠️ The Problem

MP4 was designed in the early 2000s. Back then, video was simple: you encoded it, you played it, you deleted it. Nobody was training AI models on millions of clips or tracking generation parameters for every frame.

**But now we are. And MP4 breaks.**

Here's what happens in a typical AI video workflow today:

1. **You generate or download a video** → Gets saved as `video.mp4`
2. **You need to store metadata and features** (prompt, model, seed, parameters) → Create `metadata.json`

5. **You move the video** → Now you have 2 systems to keep in sync

This is fragile. When you're working with 100 videos, it's annoying. When you're working with 100,000 videos, it's broken.

**Real problems this causes:**

- **Files get separated.** You download a dataset, but the metadata is in a different repo. Good luck matching them.
- **Features get recomputed.** Every tool re-analyzes the same video because nothing's stored with it.
- **Metadata gets lost.** Move files between systems, and suddenly you don't know which model generated what.
- **Sharing is painful.** Want to send someone a video with context? You're zipping 5 files and writing a README.

And the big one: **this doesn't scale.** You can't build reliable AI infrastructure on top of a system where the data and metadata live in completely different places.

MP4 was great for what it was built for. But we need something designed for how we actually work with video today.

That's the problem MP5 solves.

---

## 🔄 MP5 Works Everywhere (Seriously)

The whole point is that you don't need new infrastructure. MP5 files are valid MP4 files. They play in everything that plays MP4. No conversion. No special players. No hassle.

| What You Want To Do | How It Works | What You Get |
|---------------------|--------------|--------------|
| **Watch the video** | Drop into VLC/QuickTime/Chrome | Plays normally, metadata stays hidden |
| **Share with colleagues** | Send the `.mp5` file (or rename to `.mp4`) | They watch it like any video |
| **Upload to cloud** | S3, GCS, Dropbox—doesn't matter | Stores like MP4, metadata intact |
| **Use in AI pipeline** | Load with OpenCV/PyTorch/TensorFlow | Reads video + extracts embedded metadata |
| **Train ML models** | Point your training script at `.mp5` files | Gets features without reprocessing |

### The Technical Reality

MP5 is built on **FFV1** (a lossless codec) inside an **MP4 container**. Every modern video player already supports this. We're not inventing anything wild—we're using battle-tested tech in a smarter way.

**Two metadata layers working together:**

```
┌─────────────────────────────────────┐
│         MP5 File Structure          │
├─────────────────────────────────────┤
│  MP4 Container (Universal format)   │
│  ├─ moov/udta/MP5M Atom ────────────┼──► Public metadata (version, hash, timestamps)
│  └─ Video Stream (FFV1 codec)       │
│     └─ LSB Layer (hidden) ──────────┼──► AI features, training data, user metadata
│                                     │
└─────────────────────────────────────┘
         ↓                    ↓
   Normal Player          AI Tool
   Sees: Video           Sees: Video + All metadata
```

**Why this matters:** You move one file, everything moves. You backup one file, everything's backed up. You share one file, all context comes with it.

Zero external dependencies. Zero sync issues. Zero broken links.

---

## 🪄 THE REAL MAGIC HAPPENS HERE!

Here's how MP5 stores AI metadata invisibly. It's simpler than you think.

### The Steganography Process

**Video → Pixels → RGB → Binary → Hidden Data**

```
Step 1: Video Frame
   ↓
1920×1080 = 2,073,600 pixels

Step 2: Each Pixel = RGB Values
   ↓
Pixel #1: Red=214, Green=89, Blue=156

Step 3: Convert to Binary (8 bits each)
   ↓
Red:   11010110 (214)
Green: 01011001 (89)
Blue:  10011100 (156)

Step 4: Change Last Bit (LSB)
   ↓
Red:   11010111 (215) ← Changed from 214 to 215
              ▲
         This is where we hide data
```

**Here's the trick:** Changing 214 to 215? Your eye can't tell the difference. But we just stored 1 bit of information.

Do this for every color channel of every pixel, and we can hide **6.2 million bits per frame**. That's enough for all the AI metadata you need, and it's completely invisible.

### The Two Layers

**Layer 1: Atom Metadata (Public)**
- Lives in MP4's standard metadata structure (`moov/udta/MP5M`)
- Stores: version, timestamp, hash, video specs
- Any MP4 tool can read this

**Layer 2: LSB Metadata (Hidden)**
- Embedded in pixel data using steganography
- Stores: AI features, training data, prompts, parameters
- Only MP5 decoder extracts this

### Why This Works

**Capacity.** Atom metadata has size limits. LSB? Unlimited. A 4K frame holds 25 million bits.

**Tamper detection.** Re-encode with H.264? LSB data gets destroyed. You know instantly if the file changed.

**Lossless codec.** We use FFV1 to preserve LSBs exactly. Every bit survives.

### What You Get

One file. Video + metadata together. Move it, share it, store it—everything stays intact.

The file is the database. That's the magic.

---

## ⚡ Key Features

- **Auto-Feature Extraction** - 15+ video features extracted automatically (blur, motion, audio, composition)
- **Dual-Layer Storage** - Public metadata in atoms, hidden AI data in LSB steganography
- **Universal Playback** - Works in any MP4 player (VLC, QuickTime, browsers)
- **Lossless Quality** - FFV1 codec preserves every pixel exactly
- **Self-Contained** - Video + metadata in one file, no external dependencies
- **Tamper Detection** - SHA-256 hash verification, LSB destruction on re-encode
- **Cross-Platform** - Windows, macOS, Linux, mobile, cloud—works everywhere
- **Backward Compatible** - Rename to `.mp4` and it just plays

---

## 📊 Auto-Extracted Features

Every MP5 file automatically gets analyzed. Here's what we extract:

| Category | Features | What It Measures |
|----------|----------|------------------|
| **Visual Quality** | `blur_score`, `noise_level`, `compression_artifacts` | Focus, noise, encoding quality |
| **Color & Tone** | `dynamic_range`, `edge_density`, `texture_complexity` | Contrast, detail, richness |
| **Composition** | `letterbox_ratio`, `rule_of_thirds_score` | Framing, aesthetic quality |
| **Motion** | `motion_intensity`, `static_frame_ratio`, `camera_shake` | Action level, stability |
| **Scene** | `scene_cut_count` | Editing complexity |
| **Audio** | `volume_rms`, `audio_peak`, `silence_ratio`, `has_audio` | Loudness, clipping, speech detection |

**All extracted in ~5 seconds for a 2-minute video.** No manual work required.

---

## 🆚 MP5 vs MP4 (Comparison Table)

| Feature | MP4 | MP5 |
|---------|-----|-----|
| **Playback** | ✅ Universal | ✅ Universal (same players) |
| **Quality** | ⚠️ Usually lossy (H.264) | ✅ Lossless (FFV1) |
| **AI Metadata** | ❌ None | ✅ Built-in (dual-layer) |
| **Auto Features** | ❌ Reprocess every time | ✅ Extracted once, stored forever |
| **Use Case** | Streaming, YouTube | AI training, datasets, archival |
| **External Files** | ❌ Metadata separate | ✅ Self-contained |
| **Verification** | ❌ None | ✅ SHA-256 hash + tamper detection |
| **Training Data** | ❌ Manual tracking | ✅ Embedded in file |

**Bottom line:** MP4 is for watching. MP5 is for building AI.

---

## 🎯 Real-World Use Cases

### 1. AI Training Datasets
Store generation prompts, model versions, and parameters directly in video files. No more separate JSON files or databases.

### 2. Video Content Libraries
Tag and organize videos with metadata that travels with the file. Search by features without reprocessing.

### 3. Quality Assurance Automation
Auto-detect blur, shake, noise at scale. Filter low-quality videos before training.

### 4. Reproducible Research
Track exact parameters for every generated video. Reproduce results months later without guessing.

### 5. Copyright & Provenance
Embed invisible watermarks and ownership data. Verify authenticity and track video origins.

---

## 🚀 Get Started

### Installation

**Prerequisites:** Python 3.8+ and FFmpeg (we'll install it for you)

**macOS:**
```bash
git clone https://github.com/javantanna/mp5.git
cd mp5
chmod +x macos_setup.sh
./macos_setup.sh
```

**Linux:**
```bash
git clone https://github.com/javantanna/mp5.git
cd mp5
chmod +x linux_setup.sh
./linux_setup.sh
```

**Windows:**
```powershell
git clone https://github.com/javantanna/mp5.git
cd mp5
.\windows_setup.ps1
```

The setup script handles everything: Python environment, dependencies, and FFmpeg installation.

---


### Quick Start

**Step 1: Activate the environment**
```bash
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

**Step 2: Create metadata file**
```bash
# metadata.json
{
  "title": "My AI Video",
  "model": "Stable Diffusion XL",
  "prompt": "Epic sunset over mountains",
  "seed": 42,
  "steps": 50
}
```

**Step 3: Encode**
```bash
python main.py encode input.mp4 metadata.json
```

**Done.** Your MP5 file is in `outputs/output.mp5` with all metadata embedded.

---

### Usage

**Encode a video:**
```bash
python main.py encode <input.mp4> <metadata.json>
```
Auto-extracts features, embeds metadata, verifies integrity.

**Decode metadata:**
```bash
python main.py decode <file.mp5>
```
Extracts hidden AI metadata to `outputs/output_metadata.json`.

**Verify integrity:**
```bash
python main.py verify <file.mp5>
```
Checks LSB layer, atom layer, and hash verification.

**Get file info:**
```bash
python main.py info <file.mp5>
```
Shows all metadata, features, and technical specs.

**GUI Version:**
```bash
python mp5_gui.py
```
Drag-and-drop interface with real-time feature preview.

---

### Real-World Example

**Scenario:** You're training a video generation model and need to track every video's generation parameters.

```bash
# 1. Generate/download a video
# video.mp4 is ready

# 2. Create metadata.json
cat > metadata.json << EOF
{
  "model": "Runway Gen-3",
  "prompt": "Cyberpunk city at night, neon lights",
  "negative_prompt": "blurry, low quality",
  "seed": 12345,
  "steps": 50,
  "guidance_scale": 7.5,
  "resolution": "1920x1080",
  "dataset": "custom_urban_v2"
}
EOF

# 3. Encode
python main.py encode video.mp4 metadata.json

# Output:
# 🚀 mp5 MAGIC DONE SUCCESSFULLY
# Output: outputs/output.mp5
# Features auto-extracted: 15 (you're welcome)

# 4. Six months later, you forgot what this video was
python main.py decode outputs/output.mp5

# Output shows exact parameters:
# Model: Runway Gen-3
# Prompt: Cyberpunk city at night, neon lights
# Seed: 12345
# Plus 15 auto-extracted features

# 5. Reproduce the exact same video
# All parameters are right there in the file
```

**The benefit:** No spreadsheets. No databases. No "wait, which prompt generated this?" The video knows what it is.

---

## 🎬 Playing MP5 Files (Optional Setup)

MP5 files are valid MP4 files. You have **two options** to play them:

### Option 1: Quick & Easy (Rename to .mp4)

Just rename the file extension:

```bash
mv video.mp5 video.mp4
```

**Pros:**
- ✅ Instant playback in any player
- ✅ No setup required
- ✅ Works everywhere

**Cons:**
- ⚠️ Need to rename back to `.mp5` to use MP5 decoder

---

### Option 2: File Association (Recommended for Frequent Use)

Set up `.mp5` files to automatically open in VLC Media Player.

**macOS:**
```bash
./associate_mp5_macos.sh
```

**Linux:**
```bash
./associate_mp5_linux.sh
```

**Windows:**
```powershell
.\associate_mp5_windows.ps1
```

**What this does:**
- Registers `.mp5` as a known file type
- Associates it with VLC Media Player
- Double-click to play (metadata stays hidden)
- No renaming needed

**After setup:**
- Double-click any `.mp5` file → Opens in VLC automatically
- Video plays normally, AI metadata invisible to VLC
- Use `python main.py decode` to extract metadata anytime

**To undo (revert file association):**

```bash
# macOS
./revert_mp5_association_macos.sh

# Linux
./revert_mp5_association_linux.sh

# Windows
.\revert_mp5_association_windows.ps1
```

Removes the association and cleans up dependencies. After reverting, use Option 1 (rename) to play videos.

---

### Option 3: Use MP5 GUI (All-in-One)

Launch the MP5 GUI for a complete video management experience:

```bash
source .venv/bin/activate  # Activate environment first
python mp5_gui.py
```

**What you can do:**
- 🎬 **Play videos** - Built-in video player with metadata display
- 📊 **View features** - See all 15+ auto-extracted features
- 🔍 **Decode metadata** - Extract and view AI metadata
- ✅ **Verify files** - Check integrity and hash verification
- 📝 **Edit metadata** - Update user metadata in real-time
- 🖱️ **Drag & drop** - Easy file management

**Best for:**
- Viewing MP5 files with all metadata visible
- Managing multiple MP5 files
- Quick verification and feature inspection

**No file association needed** - The GUI handles everything.

---

## 🏗️ The MP5 Architecture

Here's how MP5 files are actually structured and how the dual-layer system works.

### File Structure Overview

```
┌─────────────────────────────────────────────────────────┐
│               MP5 File (MP4 Container)                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Layer 1: MP4 Atom Structure (Public Metadata)          │
│  ┌─────────────────────────────────────────────┐        │
│  │ moov                                        │        │
│  │  └── udta (User Data)                       │        │
│  │       └── ©mp5 (Custom MP5 Atom)            │◄───────┼─── Public metadata
│  │            ├─ version: "1.0.0"              │        │    • Version
│  │            ├─ created: timestamp            │        │    • Timestamp
│  │            ├─ original_hash: SHA-256        │        │    • Hash
│  │            ├─ video_info: specs             │        │    • Video specs
│  │            └─ notes: "AI data in LSB"       │        │
│  └─────────────────────────────────────────────┘        │
│                                                         │
│  Layer 2: Video Stream (LSB Steganography Layer)        │
│  ┌────────────────────────────────────────────┐         │
│  │ FFV1 Lossless Video Codec                  │         │
│  │                                            │         │
│  │  Frame 0:                                  │         │
│  │  ┌──────────────────────────────────┐      │         │
│  │  │ Pixels 0-31: Header (32 bits)    │◄─────┼─────────┼─── LSB Header
│  │  │  → Data length in binary         │      │         │    (32-bit length)
│  │  │                                  │      │         │
│  │  │ Pixels 32+: Compressed JSON Data │◄─────┼─────────┼─── Hidden AI metadata
│  │  │  → auto_features                 │      │         │    • Auto features
│  │  │  → user_metadata                 │      │         │    • User metadata
│  │  │  → training_data                 │      │         │    • Training data
│  │  └──────────────────────────────────┘      │         │
│  │                                            │         │
│  │  Frame 1+: Continuation of data...         │         │
│  └────────────────────────────────────────────┘         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### The LSB Layer In Detail

**Header Structure (Frame 0, Pixels 0-31):**

```
Bit Position:  0                               31
               ├────────────────────────────────┤
               │   32-bit Binary Length Value   │
               └────────────────────────────────┘
                        ↓
            Example: 00000000000000010010110100000000
                    (Binary for 10,000 bits)
```

**How it works:**
1. **Read header** - Extract LSB from first 32 pixels → Get total data length
2. **Validate** - Check if length is reasonable (not random noise)
3. **Read data** - Extract exactly that many bits from remaining pixels
4. **Decompress** - Unzip the binary data back to JSON

**Data Storage Format:**

```python
# What gets stored in LSB layer (HERE IS THE SAMPLE for reference):
{
  "ai_metadata": {
    "auto_features": {
      "audio_peak": 0.031494140625,
      "blur_score": 113.5306205420588,
      "camera_shake": 13.96377456321575,
      "dynamic_range": 261.0864553314121,
      "edge_density": 0.010813710357962431,
      "has_audio": true,
      "letterbox_ratio": 0.0,
      "motion_intensity": 2.893833992412551,
      "noise_level": 2.1380897405140358,
      "rule_of_thirds_score": 1.1627447796382293,
      "scene_cut_count": 0,
      "silence_ratio": 0.0,
      "static_frame_ratio": 0.29827089337175794,
      "texture_complexity": 32.70188700778534,
      "volume_rms": 0.031494140625
    },
    "mp5_version": "1.0.0",
    "payload_type": "ai_training_data",
    "timestamp": "2025-12-09T01:01:24.745920Z",
    "user_metadata": {
      "NOTE": "This is a sample metadata file for MP5 just for testing purposes. you can use any json just replace metadata.json with your own metadata file",
      "ai_model": "Stable Diffusion XL",
      "ai_version": "1.0",
      "author": "Javan Tanna",
      "category": "entertainment",
      "cfg_scale": 7.5,
      "description": "A sample video with embedded AI metadata",
      "license": "Creative Commons",
      "negative_prompt": "blurry, low quality, distorted",
      "prompt": "A beautiful sunset over mountains with clouds",
      "sampler": "DPM++ 2M Karras",
      "seed": 42,
      "source": "Original",
      "steps": 50,
      "tags": [
        "sample",
        "demo",
        "mp5",
        "ai-generated"
      ],
      "title": "input.mp4",
      "training_data": {
        "batch_size": 16,
        "dataset": "custom_landscape_v2",
        "epochs": 100
      }
    }
  },
  "file_info": {
    "created": "2025-12-09T01:01:24.745920Z",
    "layers": {
      "atom": {
        "location": "moov.udta.\u00a9mp5"
      }
    },
    "mp5_version": "1.0.0",
    "notes": "AI Metadata stored in lsb layer",
    "original_hash": "906a9076671cb27c29e574e68a324b2fc0b01affed8375bba7307fdfaa80321c",
    "video_info": {
      "codec": 875967080,
      "duration": 28.916666666666668,
      "fps": 24.0,
      "frame_count": 694,
      "height": 1920,
      "width": 1080
    }
  }
}
```

### Encoding Flow

```
Input MP4 Video
    ↓
┌───────────────────────────────────────┐
│ 1. Feature Extraction                 │
│    - Scan frames with OpenCV          │
│    - Extract 15+ features (~5 sec)    │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 2. Build Metadata Payloads            │
│    - Atom: version, hash, video info  │
│    - LSB: auto features + user data   │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 3. Compress Metadata                  │
│    - JSON → zlib (3-5x compression)   │
│    - Convert to binary string         │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 4. LSB Embedding                      │
│    - Frame 0: Write 32-bit header     │
│    - Frames 0+: Write data bits       │
│    - Each pixel LSB = 3 data bit      │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 5. Re-encode with FFV1                │
│    - Lossless codec preserves LSBs    │
│    - Level 3 with range coder         │
│    - CRC error detection enabled      │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 6. Write Atom Metadata                │
│    - Add public metadata to MP4 atoms │
│    - Store in moov/udta/©mp5          │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 7. Verification                       │
│    - Decode both layers               │
│    - Verify hash matches              │
│    - Confirm data integrity           │
└───────────────────────────────────────┘
    ↓
Output MP5 File
```

### Decoding Flow

```
Input MP5 File
    ↓
┌───────────────────────────────────────┐
│ 1. Read Atom Layer                    │
│    - Extract moov/udta/©mp5 atom      │
│    - Decompress → Get file info       │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 2. Read LSB Header (Frame 0)          │
│    - Extract first 32 pixel LSBs      │
│    - Convert to integer = data length │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 3. Extract LSB Data                   │
│    - Read exactly 'length' bits       │
│    - Collect from frame 0, 1, 2...    │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 4. Decompress & Parse                 │
│    - Binary → zlib decompress         │
│    - JSON parse → Get metadata        │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 5. Combine Results                    │
│    - Merge atom + LSB data            │
│    - Return complete metadata         │
└───────────────────────────────────────┘
    ↓
Output: Complete MP5 Metadata
```


### Key Design Decisions

**Why 32-bit header?**
- Supports up to 4GB of metadata (2^32 bits)
- Small overhead (just 32 pixels)
- Easy to validate (check if length is reasonable)

**Why FFV1 codec?**
- Lossless (LSBs survive perfectly)
- Better compression than raw
- CRC error detection built-in
- Industry standard

**Why dual layers?**
- **Atom layer**: Universal compatibility (any MP4 tool can read)
- **LSB layer**: Unlimited capacity + tamper detection

**Why zlib compression?**
- Fast (3-5x compression)
- Standard library (no dependencies)
- Deterministic (same input = same output)

**Why SHA-256 hash?**
- Verify original video integrity
- Detect any modifications
- Crypto-grade security

---

## 🤝 Contributing

Look, if you see something that could be better, just fix it. That's how we build things.

**Found a bug or have an idea?**  
[Open an issue](https://github.com/javantanna/mp5/issues). Tell us what's broken or what you want to build.

**Want to write code?**

```bash
# Fork it
git clone https://github.com/javantanna/mp5.git
cd mp5

# Make a branch
git checkout -b feature/your-thing

# Build your feature
# (Keep it clean, make it work)

# Test it
python main.py encode test.mp4 metadata.json
python main.py verify outputs/output.mp5

# Ship it
git commit -m "Add: what you built"
git push origin feature/your-thing
```

Then open a Pull Request. We'll review it and merge if it makes MP5 better.

**What we need help with:**
- Bug fixes (things that break the experience)
- Performance improvements (make it faster)
- Better GUI (make it easier to use)
- Documentation (help people understand how to use this)
- Testing on different platforms (does it work everywhere?)

The code doesn't have to be perfect. If it solves a real problem, we can work together to polish it.

That's it. Thanks for building with us.

## 📜 License

This project is released under the Apache 2.0 License. See the LICENSE file for details.

---
