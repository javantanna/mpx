import React, { useState } from 'react';
import { FileVideo, Lock, Layers, CheckCircle, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react';

const MP5Architecture = () => {
  const [expandedSection, setExpandedSection] = useState('overview');

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const Section = ({ id, title, children, icon: Icon }) => (
    <div className="mb-4 border border-gray-700 rounded-lg overflow-hidden bg-gray-800">
      <button
        onClick={() => toggleSection(id)}
        className="w-full px-6 py-4 flex items-center justify-between bg-gray-750 hover:bg-gray-700 transition-colors"
      >
        <div className="flex items-center gap-3">
          <Icon className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">{title}</h3>
        </div>
        {expandedSection === id ? (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronRight className="w-5 h-5 text-gray-400" />
        )}
      </button>
      {expandedSection === id && (
        <div className="px-6 py-4 text-gray-300">{children}</div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <FileVideo className="w-12 h-12 text-blue-500" />
            <h1 className="text-5xl font-bold text-white">.mp5</h1>
          </div>
          <p className="text-xl text-gray-400">Hybrid Steganographic Video Format</p>
          <p className="text-sm text-gray-500 mt-2">Method 3: Metadata Atoms + LSB Steganography</p>
        </div>

        {/* Overview */}
        <Section id="overview" title="System Overview" icon={Layers}>
          <div className="space-y-4">
            <div className="bg-gray-900 p-4 rounded-lg border border-blue-500/30">
              <h4 className="font-semibold text-blue-400 mb-2">Two-Layer Architecture</h4>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-blue-400 font-bold">1</span>
                  </div>
                  <div>
                    <p className="font-medium text-white">Public Layer (Metadata Atoms)</p>
                    <p className="text-sm text-gray-400">Fast access, easy extraction, visible but legitimate</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-purple-400 font-bold">2</span>
                  </div>
                  <div>
                    <p className="font-medium text-white">Hidden Layer (LSB Steganography)</p>
                    <p className="text-sm text-gray-400">Tamper-proof verification, invisible, survives casual inspection</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-900 p-4 rounded-lg">
              <h4 className="font-semibold text-green-400 mb-2">Cross-Verification System</h4>
              <p className="text-sm text-gray-400">Both layers contain checksums of each other. If metadata atoms are tampered with, LSB layer proves the original. If LSB is destroyed (re-encoding), metadata atoms remain accessible.</p>
            </div>
          </div>
        </Section>

        {/* Data Structure */}
        <Section id="structure" title="Data Structure & Format" icon={FileVideo}>
          <div className="space-y-4">
            <div className="bg-gray-900 p-4 rounded-lg font-mono text-sm">
              <pre className="text-green-400 whitespace-pre-wrap">{`{
  "mp5_version": "1.0.0",
  "created": "2025-11-09T10:30:00Z",
  "layers": {
    "atom": {
      "checksum": "sha256:abc123...",
      "location": "moov.udta.©mp5"
    },
    "lsb": {
      "checksum": "sha256:def456...",
      "frames": [0, 1, 2, 3, 4],
      "redundancy": 3
    }
  },
  
  "video_info": {
    "original_hash": "sha256:original...",
    "duration": 120.5,
    "resolution": "1920x1080",
    "fps": 30,
    "codec": "h264"
  },
  
  "ai_metadata": {
    "transcript": [...],
    "scenes": [...],
    "objects": [...],
    "embeddings": {...}
  }
}`}</pre>
            </div>

            <div className="bg-gray-900 p-4 rounded-lg">
              <h4 className="font-semibold text-yellow-400 mb-3">Compression Pipeline</h4>
              <div className="space-y-2">
                {['JSON (readable)', 'zlib compress (60-80% reduction)', 'base64 encode (safe binary)', 'Optional AES-256 encryption', 'Split into layers'].map((step, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-yellow-500/20 flex items-center justify-center flex-shrink-0">
                      <span className="text-yellow-400 text-xs">{i + 1}</span>
                    </div>
                    <span className="text-sm text-gray-300">{step}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Section>

        {/* Layer 1: Metadata Atoms */}
        <Section id="layer1" title="Layer 1: Metadata Atoms (udta)" icon={CheckCircle}>
          <div className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-blue-900/20 p-4 rounded-lg border border-blue-500/30">
                <h4 className="font-semibold text-blue-400 mb-2 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Advantages
                </h4>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>• Fast extraction (no frame processing)</li>
                  <li>• Standard MP4 structure</li>
                  <li>• Easy to implement</li>
                  <li>• Works with any MP4 tool</li>
                  <li>• No quality degradation</li>
                </ul>
              </div>
              <div className="bg-red-900/20 p-4 rounded-lg border border-red-500/30">
                <h4 className="font-semibold text-red-400 mb-2 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Limitations
                </h4>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>• Easy to strip/modify</li>
                  <li>• Visible in hex editors</li>
                  <li>• Lost during some conversions</li>
                  <li>• No stealth protection</li>
                </ul>
              </div>
            </div>

            <div className="bg-gray-900 p-4 rounded-lg">
              <h4 className="font-semibold text-white mb-2">Storage Location</h4>
              <div className="bg-black/40 p-3 rounded font-mono text-xs text-gray-400">
                <div>MP4 Container</div>
                <div className="ml-4">├── ftyp (file type)</div>
                <div className="ml-4">├── moov (movie data)</div>
                <div className="ml-8">│   ├── mvhd (header)</div>
                <div className="ml-8">│   ├── trak (tracks)</div>
                <div className="ml-8 text-blue-400">│   └── udta (user data)</div>
                <div className="ml-12 text-blue-400">│       └── ©mp5 ← YOUR DATA HERE</div>
                <div className="ml-4">└── mdat (media data)</div>
              </div>
            </div>

            <div className="bg-gray-900 p-4 rounded-lg">
              <h4 className="font-semibold text-white mb-2">What to Store</h4>
              <p className="text-sm text-gray-400 mb-3">Full AI metadata + checksum of LSB layer</p>
              <div className="bg-black/40 p-3 rounded text-xs text-green-400 font-mono">
                Compressed size: ~15-50 KB typical
              </div>
            </div>
          </div>
        </Section>

        {/* Layer 2: LSB Steganography */}
        <Section id="layer2" title="Layer 2: LSB Steganography" icon={Lock}>
          <div className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-purple-900/20 p-4 rounded-lg border border-purple-500/30">
                <h4 className="font-semibold text-purple-400 mb-2 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Advantages
                </h4>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>• Invisible to casual inspection</li>
                  <li>• Tamper-evident</li>
                  <li>• Survives basic operations</li>
                  <li>• Huge capacity (MB per second)</li>
                  <li>• Cryptographic verification</li>
                </ul>
              </div>
              <div className="bg-red-900/20 p-4 rounded-lg border border-red-500/30">
                <h4 className="font-semibold text-red-400 mb-2 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Limitations
                </h4>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>• Destroyed by re-encoding</li>
                  <li>• Slow to extract (frame processing)</li>
                  <li>• Vulnerable to compression</li>
                  <li>• Complex implementation</li>
                </ul>
              </div>
            </div>

            <div className="bg-gray-900 p-4 rounded-lg">
              <h4 className="font-semibold text-white mb-2">How LSB Works</h4>
              <div className="space-y-3">
                <div className="bg-black/40 p-3 rounded">
                  <p className="text-xs text-gray-400 mb-2">Normal Pixel RGB Value:</p>
                  <div className="font-mono text-sm text-blue-400">
                    [142, 201, 88] → Binary: [10001110, 11001001, 01011000]
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Last bit barely affects color (142 vs 143 looks identical)</p>
                </div>
                
                <div className="bg-black/40 p-3 rounded">
                  <p className="text-xs text-gray-400 mb-2">Modified with Hidden Data:</p>
                  <div className="font-mono text-sm text-purple-400">
                    [142, 200, 89] → Binary: [10001110, 11001000, 01011001]
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Changed bits: <span className="text-yellow-400">0, 1, 1</span> (stores 3 bits of data)</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-900 p-4 rounded-lg">
              <h4 className="font-semibold text-white mb-2">Storage Capacity</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">1080p frame (1920×1080)</span>
                  <span className="text-green-400 font-mono">~777 KB</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">30fps video (1 second)</span>
                  <span className="text-green-400 font-mono">~23 MB</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Typical AI metadata</span>
                  <span className="text-blue-400 font-mono">~50-100 KB</span>
                </div>
                <div className="mt-3 p-2 bg-green-900/20 rounded border border-green-500/30">
                  <p className="text-green-400 text-xs">✓ More than enough capacity! Can store in first 1-2 frames</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-900 p-4 rounded-lg">
              <h4 className="font-semibold text-white mb-2">What to Store</h4>
              <p className="text-sm text-gray-400 mb-3">Minimal verification data + checksum of metadata atoms</p>
              <div className="bg-black/40 p-3 rounded">
                <pre className="text-xs text-purple-400 font-mono whitespace-pre-wrap">{`{
  "signature": "crypto_signature_of_atom_data",
  "atom_checksum": "sha256:...",
  "timestamp": "2025-11-09T10:30:00Z",
  "frames_used": [0, 1, 2, 3, 4]
}`}</pre>
              </div>
            </div>
          </div>
        </Section>

        {/* Implementation Strategy */}
        <Section id="implementation" title="Implementation Strategy" icon={Layers}>
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 p-6 rounded-lg border border-blue-500/30">
              <h4 className="font-semibold text-white mb-4 text-lg">Development Phases</h4>
              
              <div className="space-y-4">
                {[
                  {
                    phase: "Phase 1: Core Library (Week 1-2)",
                    tasks: [
                      "Build MP4 metadata atom reader/writer",
                      "Implement basic LSB encoder/decoder",
                      "Create compression pipeline (zlib)",
                      "Test with sample videos"
                    ]
                  },
                  {
                    phase: "Phase 2: Hybrid System (Week 3-4)",
                    tasks: [
                      "Integrate both layers",
                      "Add cross-verification logic",
                      "Implement redundancy (repeat data 3x in LSB)",
                      "Create checksum system"
                    ]
                  },
                  {
                    phase: "Phase 3: CLI Tools (Week 5-6)",
                    tasks: [
                      "mp5encode: Convert MP4 → MP5",
                      "mp5decode: Extract data from MP5",
                      "mp5verify: Check integrity of both layers",
                      "mp5clean: Remove MP5 data (back to MP4)"
                    ]
                  },
                  {
                    phase: "Phase 4: AI Integration (Week 7-8)",
                    tasks: [
                      "Auto-generate transcripts (Whisper API)",
                      "Scene detection (OpenCV)",
                      "Object detection (YOLO/CLIP)",
                      "Generate embeddings for search"
                    ]
                  }
                ].map((phase, i) => (
                  <div key={i} className="bg-gray-800/50 p-4 rounded-lg">
                    <h5 className="font-semibold text-blue-400 mb-2">{phase.phase}</h5>
                    <ul className="space-y-1">
                      {phase.tasks.map((task, j) => (
                        <li key={j} className="text-sm text-gray-300 flex items-start gap-2">
                          <span className="text-green-400 mt-1">✓</span>
                          <span>{task}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-gray-900 p-4 rounded-lg">
              <h4 className="font-semibold text-white mb-3">Tech Stack</h4>
              <div className="grid md:grid-cols-2 gap-3">
                <div className="bg-black/40 p-3 rounded">
                  <p className="text-xs text-gray-400 mb-2">Core Libraries</p>
                  <div className="space-y-1 text-sm">
                    <div className="text-blue-400 font-mono">opencv-python</div>
                    <div className="text-blue-400 font-mono">moviepy</div>
                    <div className="text-blue-400 font-mono">ffmpeg-python</div>
                  </div>
                </div>
                <div className="bg-black/40 p-3 rounded">
                  <p className="text-xs text-gray-400 mb-2">Data Processing</p>
                  <div className="space-y-1 text-sm">
                    <div className="text-purple-400 font-mono">numpy</div>
                    <div className="text-purple-400 font-mono">zlib</div>
                    <div className="text-purple-400 font-mono">cryptography</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Section>

        {/* Use Cases */}
        <Section id="usecases" title="Real-World Use Cases" icon={FileVideo}>
          <div className="grid md:grid-cols-2 gap-4">
            {[
              {
                title: "Content Creators",
                desc: "Embed licensing info, usage rights, and creator attribution that survives downloads",
                color: "blue"
              },
              {
                title: "Video Archives",
                desc: "Store searchable metadata directly in video files for future AI retrieval",
                color: "green"
              },
              {
                title: "Education",
                desc: "Embed lecture transcripts, timestamps, and references within educational videos",
                color: "purple"
              },
              {
                title: "Journalism",
                desc: "Prove video authenticity with cryptographic signatures and source information",
                color: "red"
              },
              {
                title: "Surveillance",
                desc: "Embed camera ID, location, timestamp in a tamper-evident way",
                color: "yellow"
              },
              {
                title: "Media Platforms",
                desc: "Store AI-generated descriptions for accessibility without separate database",
                color: "pink"
              }
            ].map((use, i) => (
              <div key={i} className={`bg-${use.color}-900/20 p-4 rounded-lg border border-${use.color}-500/30`}>
                <h5 className={`font-semibold text-${use.color}-400 mb-2`}>{use.title}</h5>
                <p className="text-sm text-gray-400">{use.desc}</p>
              </div>
            ))}
          </div>
        </Section>

        {/* Footer */}
        <div className="mt-12 text-center text-gray-500 text-sm">
          <p>Open Source Project • MIT License</p>
          <p className="mt-2">Ready to implement? Start with Phase 1 and build incrementally.</p>
        </div>
      </div>
    </div>
  );
};

export default MP5Architecture;