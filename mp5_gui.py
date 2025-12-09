#!/usr/bin/env python3
"""
MP5 GUI Application
A tkinter-based desktop application for playing MP5 files,
displaying metadata, and encoding/decoding/verifying videos.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import cv2
from PIL import Image, ImageTk
import threading
import json
import os
import tempfile
from datetime import datetime
import subprocess

# Import MP5 modules
from src.MP5Config import MP5Config
from src.MP5Encoder import MP5Encoder
from src.MP5Decoder import MP5Decoder
from src.MP5Verifier import MP5Verifier


class VideoPlayer:
    """Video player component using OpenCV with audio support via ffplay"""
    
    def __init__(self, canvas, on_metadata_update=None):
        self.canvas = canvas
        self.on_metadata_update = on_metadata_update
        self.cap = None
        self.is_playing = False
        self.current_frame = None
        self.photo = None
        self.video_path = None
        self.fps = 30
        self.frame_delay = 33  # ms
        self.audio_process = None  # ffplay process for audio
        
    def load_video(self, video_path):
        """Load a video file"""
        self.stop()  # Stop any existing playback
        
        if self.cap:
            self.cap.release()
        
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            messagebox.showerror("Error", f"Cannot open video: {video_path}")
            return False
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.frame_delay = int(1000 / self.fps)
        
        # Show first frame
        self._show_frame()
        return True
    
    def _show_frame(self):
        """Display current frame on canvas"""
        if self.cap is None:
            return
        
        ret, frame = self.cap.read()
        if not ret:
            # Loop video
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._restart_audio()
            ret, frame = self.cap.read()
            if not ret:
                self.stop()
                return
        
        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize to fit canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            h, w = frame.shape[:2]
            scale = min(canvas_width / w, canvas_height / h)
            new_w, new_h = int(w * scale), int(h * scale)
            frame = cv2.resize(frame, (new_w, new_h))
        
        # Convert to PhotoImage
        image = Image.fromarray(frame)
        self.photo = ImageTk.PhotoImage(image)
        
        # Display on canvas
        self.canvas.delete("all")
        self.canvas.create_image(
            self.canvas.winfo_width() // 2,
            self.canvas.winfo_height() // 2,
            image=self.photo,
            anchor=tk.CENTER
        )
        
        # Schedule next frame if playing
        if self.is_playing:
            self.canvas.after(self.frame_delay, self._show_frame)
    
    def _start_audio(self):
        """Start audio playback using ffplay"""
        if self.video_path:
            try:
                # Kill existing audio process
                self._stop_audio()
                # Start ffplay for audio only (no video window)
                self.audio_process = subprocess.Popen([
                    'ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet',
                    self.video_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"Audio playback failed: {e}")
    
    def _stop_audio(self):
        """Stop audio playback"""
        if self.audio_process:
            try:
                self.audio_process.terminate()
                self.audio_process.wait(timeout=1)
            except:
                try:
                    self.audio_process.kill()
                except:
                    pass
            self.audio_process = None
    
    def _restart_audio(self):
        """Restart audio for video loop"""
        if self.is_playing:
            self._start_audio()
    
    def play(self):
        """Start playback"""
        if self.cap and not self.is_playing:
            self.is_playing = True
            self._start_audio()
            self._show_frame()
    
    def pause(self):
        """Pause playback"""
        self.is_playing = False
        self._stop_audio()
    
    def stop(self):
        """Stop playback and reset"""
        self.is_playing = False
        self._stop_audio()
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._show_frame()
    
    def release(self):
        """Release video capture and cleanup"""
        self.is_playing = False
        self._stop_audio()
        if self.cap:
            self.cap.release()
            self.cap = None


class MP5GUI:
    """Main MP5 GUI Application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("MP5 Player & Editor")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("Title.TLabel", font=("Helvetica", 16, "bold"))
        self.style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))
        
        # MP5 components
        self.config = MP5Config()
        self.encoder = MP5Encoder(self.config)
        self.decoder = MP5Decoder(self.config)
        self.verifier = MP5Verifier(self.config)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self._create_player_tab()
        self._create_encode_tab()
        self._create_decode_tab()
        self._create_verify_tab()
        
    def _create_player_tab(self):
        """Create the Player tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="▶ Player")
        
        # Main paned window
        paned = ttk.PanedWindow(tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left side: Video player
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=3)
        
        # Video canvas
        self.video_canvas = tk.Canvas(left_frame, bg="black", width=640, height=480)
        self.video_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create video player
        self.player = VideoPlayer(self.video_canvas)
        
        # Controls frame
        controls = ttk.Frame(left_frame)
        controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(controls, text="📂 Open", command=self._open_video).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text="▶ Play", command=self.player.play).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text="⏸ Pause", command=self.player.pause).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text="⏹ Stop", command=self.player.stop).pack(side=tk.LEFT, padx=2)
        
        # Right side: Metadata panel
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        ttk.Label(right_frame, text="📋 Metadata", style="Header.TLabel").pack(pady=5)
        
        self.metadata_text = scrolledtext.ScrolledText(right_frame, width=40, height=30, wrap=tk.WORD)
        self.metadata_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(right_frame, text="🔄 Refresh Metadata", command=self._refresh_metadata).pack(pady=5)
        
    def _create_encode_tab(self):
        """Create the Encode tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔒 Encode")
        
        # Title
        ttk.Label(tab, text="Encode Video with Metadata", style="Title.TLabel").pack(pady=10)
        
        # Input video selection
        input_frame = ttk.LabelFrame(tab, text="Input Video")
        input_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.encode_input_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.encode_input_var, width=60).pack(side=tk.LEFT, padx=5, pady=10)
        ttk.Button(input_frame, text="Browse...", command=self._browse_encode_input).pack(side=tk.LEFT, padx=5)
        
        # Metadata file selection
        meta_frame = ttk.LabelFrame(tab, text="Metadata JSON")
        meta_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.encode_meta_var = tk.StringVar()
        ttk.Entry(meta_frame, textvariable=self.encode_meta_var, width=60).pack(side=tk.LEFT, padx=5, pady=10)
        ttk.Button(meta_frame, text="Browse...", command=self._browse_encode_meta).pack(side=tk.LEFT, padx=5)
        
        # Output path
        output_frame = ttk.LabelFrame(tab, text="Output Path (optional)")
        output_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.encode_output_var = tk.StringVar(value="outputs/output.mp5")
        ttk.Entry(output_frame, textvariable=self.encode_output_var, width=60).pack(side=tk.LEFT, padx=5, pady=10)
        
        # Encode button
        ttk.Button(tab, text="🚀 Encode Video", command=self._encode_video).pack(pady=20)
        
        # Status
        self.encode_status = ttk.Label(tab, text="")
        self.encode_status.pack(pady=10)
        
        # Progress
        self.encode_progress = ttk.Progressbar(tab, mode='indeterminate', length=400)
        self.encode_progress.pack(pady=10)
        
    def _create_decode_tab(self):
        """Create the Decode tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔓 Decode")
        
        # Title
        ttk.Label(tab, text="Decode MP5 File", style="Title.TLabel").pack(pady=10)
        
        # Input file selection
        input_frame = ttk.LabelFrame(tab, text="MP5 File")
        input_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.decode_input_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.decode_input_var, width=60).pack(side=tk.LEFT, padx=5, pady=10)
        ttk.Button(input_frame, text="Browse...", command=self._browse_decode_input).pack(side=tk.LEFT, padx=5)
        
        # Decode button
        ttk.Button(tab, text="🔓 Decode", command=self._decode_video).pack(pady=20)
        
        # Output
        output_frame = ttk.LabelFrame(tab, text="Decoded Metadata")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.decode_output = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD)
        self.decode_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def _create_verify_tab(self):
        """Create the Verify tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="✅ Verify")
        
        # Title
        ttk.Label(tab, text="Verify MP5 File", style="Title.TLabel").pack(pady=10)
        
        # Input file selection
        input_frame = ttk.LabelFrame(tab, text="MP5 File")
        input_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.verify_input_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.verify_input_var, width=60).pack(side=tk.LEFT, padx=5, pady=10)
        ttk.Button(input_frame, text="Browse...", command=self._browse_verify_input).pack(side=tk.LEFT, padx=5)
        
        # Verify button
        ttk.Button(tab, text="✅ Verify", command=self._verify_video).pack(pady=20)
        
        # Status display
        self.verify_status_frame = ttk.LabelFrame(tab, text="Verification Result")
        self.verify_status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.verify_result = ttk.Label(self.verify_status_frame, text="", font=("Helvetica", 14))
        self.verify_result.pack(pady=20)
        
        self.verify_details = scrolledtext.ScrolledText(self.verify_status_frame, wrap=tk.WORD, height=15)
        self.verify_details.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    # ==================== Actions ====================
    
    def _open_video(self):
        """Open video file for playback"""
        filepath = filedialog.askopenfilename(
            title="Open Video",
            filetypes=[("MP5 Files", "*.mp5"), ("MP4 Files", "*.mp4"), ("All Files", "*.*")]
        )
        if filepath:
            if self.player.load_video(filepath):
                self._refresh_metadata()
    
    def _refresh_metadata(self):
        """Refresh metadata display"""
        if not self.player.video_path:
            return
        
        self.metadata_text.delete(1.0, tk.END)
        
        try:
            result = self.decoder.decode(self.player.video_path)
            
            # Format and display
            self.metadata_text.insert(tk.END, "=== File Info ===\n\n")
            
            if result.get("file_info"):
                info = result["file_info"]
                self.metadata_text.insert(tk.END, f"Version: {info.get('mp5_version', 'N/A')}\n")
                
                created = info.get('created', '')
                try:
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    created = dt.strftime('%b %d, %Y at %I:%M %p')
                except:
                    pass
                self.metadata_text.insert(tk.END, f"Created: {created}\n")
                self.metadata_text.insert(tk.END, f"Hash: {info.get('original_hash', 'N/A')[:16]}...\n\n")
                
                if info.get("video_info"):
                    vi = info["video_info"]
                    self.metadata_text.insert(tk.END, "=== Video Info ===\n\n")
                    self.metadata_text.insert(tk.END, f"Resolution: {vi.get('width')}x{vi.get('height')}\n")
                    self.metadata_text.insert(tk.END, f"FPS: {vi.get('fps', 0):.2f}\n")
                    self.metadata_text.insert(tk.END, f"Duration: {vi.get('duration', 0):.2f}s\n")
                    self.metadata_text.insert(tk.END, f"Frames: {vi.get('frame_count', 0)}\n\n")
            
            if result.get("ai_metadata"):
                ai = result["ai_metadata"]
                self.metadata_text.insert(tk.END, "=== AI Features ===\n\n")
                
                if ai.get("auto_features"):
                    for key, value in ai["auto_features"].items():
                        if isinstance(value, float):
                            self.metadata_text.insert(tk.END, f"{key}: {value:.4f}\n")
                        else:
                            self.metadata_text.insert(tk.END, f"{key}: {value}\n")
                
                if ai.get("user_metadata"):
                    self.metadata_text.insert(tk.END, "\n=== User Metadata ===\n\n")
                    self.metadata_text.insert(tk.END, json.dumps(ai["user_metadata"], indent=2))
                    
        except Exception as e:
            self.metadata_text.insert(tk.END, f"Error reading metadata:\n{str(e)}")
    
    def _browse_encode_input(self):
        filepath = filedialog.askopenfilename(
            title="Select Input Video",
            filetypes=[("Video Files", "*.mp4 *.mov *.avi"), ("All Files", "*.*")]
        )
        if filepath:
            self.encode_input_var.set(filepath)
    
    def _browse_encode_meta(self):
        filepath = filedialog.askopenfilename(
            title="Select Metadata JSON",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if filepath:
            self.encode_meta_var.set(filepath)
    
    def _encode_video(self):
        """Encode video in background thread"""
        input_path = self.encode_input_var.get()
        meta_path = self.encode_meta_var.get()
        output_path = self.encode_output_var.get()
        
        if not input_path or not meta_path:
            messagebox.showerror("Error", "Please select input video and metadata file")
            return
        
        def encode_task():
            try:
                self.encode_status.config(text="Encoding... Please wait")
                self.encode_progress.start()
                
                with open(meta_path, 'r') as f:
                    metadata = json.load(f)
                
                result = self.encoder.encode(input_path, metadata, output_path)
                
                self.encode_progress.stop()
                self.encode_status.config(text=f"✓ Encoded successfully! Output: {result['output_file']}")
                messagebox.showinfo("Success", f"Encoding complete!\nOutput: {result['output_file']}")
                
            except Exception as e:
                self.encode_progress.stop()
                self.encode_status.config(text=f"✗ Error: {str(e)}")
                messagebox.showerror("Error", str(e))
        
        threading.Thread(target=encode_task, daemon=True).start()
    
    def _browse_decode_input(self):
        filepath = filedialog.askopenfilename(
            title="Select MP5 File",
            filetypes=[("MP5 Files", "*.mp5"), ("All Files", "*.*")]
        )
        if filepath:
            self.decode_input_var.set(filepath)
    
    def _decode_video(self):
        """Decode MP5 file"""
        input_path = self.decode_input_var.get()
        
        if not input_path:
            messagebox.showerror("Error", "Please select an MP5 file")
            return
        
        try:
            result = self.decoder.decode(input_path)
            
            self.decode_output.delete(1.0, tk.END)
            self.decode_output.insert(tk.END, json.dumps(result, indent=2))
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _browse_verify_input(self):
        filepath = filedialog.askopenfilename(
            title="Select MP5 File",
            filetypes=[("MP5 Files", "*.mp5"), ("All Files", "*.*")]
        )
        if filepath:
            self.verify_input_var.set(filepath)
    
    def _verify_video(self):
        """Verify MP5 file"""
        input_path = self.verify_input_var.get()
        
        if not input_path:
            messagebox.showerror("Error", "Please select an MP5 file")
            return
        
        try:
            result = self.verifier.verify(input_path)
            
            overall = result.get('overall', 'unknown')
            
            if overall == 'verified':
                self.verify_result.config(text="✅ VERIFICATION PASSED", foreground="green")
            elif overall == 'partial':
                self.verify_result.config(text="⚠️ PARTIAL VERIFICATION", foreground="orange")
            else:
                self.verify_result.config(text="❌ VERIFICATION FAILED", foreground="red")
            
            self.verify_details.delete(1.0, tk.END)
            self.verify_details.insert(tk.END, f"File: {result.get('file', 'N/A')}\n\n")
            self.verify_details.insert(tk.END, f"LSB Layer: {result.get('lsb_layer', {}).get('status', 'unknown')}\n")
            self.verify_details.insert(tk.END, f"Atom Layer: {result.get('atom_layer', {}).get('status', 'unknown')}\n")
            self.verify_details.insert(tk.END, f"\nOverall: {overall.upper()}\n")
            
            if result.get('error'):
                self.verify_details.insert(tk.END, f"\nError: {result['error']}")
                
        except Exception as e:
            self.verify_result.config(text="❌ ERROR", foreground="red")
            self.verify_details.delete(1.0, tk.END)
            self.verify_details.insert(tk.END, f"Error: {str(e)}")
    
    def on_closing(self):
        """Handle window close"""
        self.player.release()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = MP5GUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
