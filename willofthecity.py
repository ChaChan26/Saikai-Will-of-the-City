import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
import random
import time
import os
import sys


# Try to import audio libraries
audio_available = False
try:
    import vlc
    import threading
    audio_available = True
    print("✓ python-vlc loaded successfully")
except ImportError:
    print("✗ python-vlc not available. Install with: pip install python-vlc")

# Song lyrics with OFFICIAL timestamps from .LRC file
# SAIKAI - MILI (Limbus Company)
# Format: (start_time, duration, lyric_text)
lyrics = [
    (2, 5, "SAIKAI - MILI"),
    (29.44, 7.43, "When I was young and lost"),
    (36.87, 7.47, "You showed up, and had my doors unlocked"),
    (44.34, 6.79, "Like threads, petals unfold"),
    (51.13, 7.91, "A red kawara-nadeshiko"),
    (59.04, 14.82, "You have shown me that I am still capable of caring for someone else"),
    (73.86, 12.60, "That I still bare the same innocence inside"),
    (86.46, 2.81, "'Cause now I know that"),
    (89.27, 2.87, "Pain cannot define the past"),
    (92.14, 5.24, "We are built to overcome endless mishaps"),
    (97.38, 4.52, "You know, it is not so bad"),
    (101.90, 1.87, "When you are with me"),
    (103.77, 3.01, "Cherish as long as we last"),
    (106.78, 4.83, "'Cause S is not for sayonara"),
    (111.61, 7.05, "Let memories play back"),
    # Instrumental break (118.66 to 142.60)
    (142.60, 7.14, "I knew I must step up"),
    (149.74, 7.37, "You deserve the world and more"),
    (157.11, 7.07, "The truth is that you'd rather"),
    (164.18, 7.54, "Spend our limited time together"),
    (171.72, 7.37, "Protection alone is not enough"),
    (179.09, 7.62, "Providing cannot fill an empty cup"),
    (186.71, 3.58, "Thirsting for love"),
    (190.29, 4.00, "I questioned myself a lot"),
    # Instrumental break (194.29 to 222.19)
    (222.19, 4.51, "What do I know about love?"),
    (226.70, 4.88, "How can I recreate what I've never had?"),
    (231.58, 6.44, "All I know is that I must keep you thriving"),
    (238.02, 3.11, "If nutrients are what you lack"),
    (241.13, 9.36, "I will water you with every drop of blood I have"),
    (250.49, 2.11, "But now I know that"),
    (252.60, 3.13, "Sacrifice is the easy path"),
    (255.73, 4.73, "My absence cannot ever change the fact"),
    (260.46, 6.71, "I wanted the very best for you, believe me"),
    (267.17, 3.17, "Our threads in red can never be cut"),
    (270.34, 5.59, "And S is not for sayonara"),
    (275.93, 7.78, "Will you forgive me at last?"),
    # Instrumental outro with glitch effects
    (283.71, 40.28, "[INSTRUMENTAL_GLITCH]"),  # Special marker for glitch mode
]

class LyricTerminal:
    def __init__(self, root):
        self.root = root
        self.root.title("INDEX_LOOM_TERMINAL // SAIKAI")
        self.root.geometry("1000x850")
        self.root.configure(bg="#000000")
        
        self.is_revealing = False
        self.is_playing = False
        self.current_lyric_index = 0
        self.song_start_time = None
        self.paused_time = 0
        self.sync_timer = None
        self.audio_file = None
        self.audio_thread = None
        self.audio_playing = False
        
        # Glitch state
        self.glitch_layers = []
        self.glitch_intensity = 0
        
        # Main Container
        self.main_frame = tk.Frame(root, bg="#000000", highlightbackground="#1e1e1e", highlightthickness=1)
        self.main_frame.pack(expand=True, fill="both", padx=40, pady=40)
        
        # Now create glow labels after main_frame exists
        self.glow_labels = []
        for i in range(4):
            lbl = tk.Label(self.main_frame, text="", font=("Fixedsys", 20, "bold"),
                fg=["#00FFFF","#FF00FF","#4FACFF","#FFFFFF"][i],
                bg="#000000")
            lbl.place(relx=0.5, rely=0.5, anchor="center")
            self.glow_labels.append(lbl)

        # Load Icon
        self.load_index_icon()
        
        # Progress bar
        self.progress_frame = tk.Frame(self.main_frame, bg="#000000")
        self.progress_frame.pack(pady=10, fill="x", padx=20)
        
        self.progress_bar = tk.Canvas(self.progress_frame, height=8, bg="#1e1e1e", highlightthickness=0)
        self.progress_bar.pack(fill="x")
        self.progress_fill = self.progress_bar.create_rectangle(0, 0, 0, 8, fill="#4FACFF", outline="")
        self.progress_bar.bind("<Button-1>", self.on_progress_click)
        
        # Time display
        self.time_label = tk.Label(
            self.main_frame, text="0:00 / 5:24", 
            font=("Consolas", 9), fg="#555555", bg="#000000"
        )
        self.time_label.pack(pady=(5, 10))
        
        # Current lyric display - CENTERED
        self.lyric_label = tk.Label(
            self.main_frame, text="", font=("Fixedsys", 20, "bold"),
            fg="#A9A9A9", bg="#000000", justify="center",
            wraplength=800, padx=20, pady=30, anchor="center"
        )
        self.lyric_label.pack(expand=True, fill="both")
        
        # Next lyric preview (dimmed)
        self.next_lyric_label = tk.Label(
            self.main_frame, text="", font=("Fixedsys", 11),
            fg="#333333", bg="#000000", justify="center",
            wraplength=700
        )
        self.next_lyric_label.pack(pady=(0, 15))
        
        # Control buttons frame
        self.control_frame = tk.Frame(root, bg="#000000")
        self.control_frame.pack(pady=15)
        
        # Load audio button
        self.load_btn = tk.Button(
            self.control_frame, text="[ 📁 LOAD AUDIO ]", command=self.load_audio_file,
            font=("Consolas", 10), bg="#000000", fg="#888888",
            activebackground="#888888", activeforeground="#000000",
            relief="flat", bd=0, highlightthickness=1, highlightbackground="#888888",
            padx=15
        )
        self.load_btn.pack(side="left", padx=5)
        
        # Play button
        self.play_btn = tk.Button(
            self.control_frame, text="[ ▶ START ]", command=self.toggle_playback,
            font=("Consolas", 12), bg="#000000", fg="#4FACFF",
            activebackground="#4FACFF", activeforeground="#000000",
            relief="flat", bd=0, highlightthickness=1, highlightbackground="#4FACFF",
            padx=20
        )
        self.play_btn.pack(side="left", padx=5)
        
        # Reset button
        self.reset_btn = tk.Button(
            self.control_frame, text="[ ⟲ RESET ]", command=self.reset_song,
            font=("Consolas", 10), bg="#000000", fg="#8b0000",
            activebackground="#8b0000", activeforeground="#000000",
            relief="flat", bd=0, highlightthickness=1, highlightbackground="#8b0000",
            padx=15
        )
        self.reset_btn.pack(side="left", padx=5)
        
        # Status label
        self.status_label = tk.Label(
            root, text="", 
            font=("Consolas", 9), fg="#555555", bg="#000000"
        )
        self.status_label.pack(pady=(0, 10))
        
        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Check for audio file
        self.check_audio_file()

    def create_icon_image(self):
        """Creates a cryptic eye/portal icon"""
        size = 240
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        center = size // 2
        
        # Outer ring
        draw.ellipse([15, 15, 225, 225], outline="#4FACFF", width=4)
        draw.ellipse([37, 37, 203, 203], outline="#4FACFF", width=3)
        draw.ellipse([63, 63, 177, 177], outline="#8b0000", width=3)
        
        # Central pupil
        draw.ellipse([90, 90, 150, 150], fill="#000000", outline="#4FACFF", width=4)
        
        # Radiating lines
        import math
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x1 = center + 78 * math.cos(rad)
            y1 = center + 78 * math.sin(rad)
            x2 = center + 112 * math.cos(rad)
            y2 = center + 112 * math.sin(rad)
            draw.line([x1, y1, x2, y2], fill="#4FACFF", width=3)
        
        # Scan line
        draw.line([15, center, 225, center], fill="#8b0000", width=2)
        
        return img

    def load_index_icon(self):
        """Loads or creates the Index Icon"""
        try:
            img = Image.open("index_icon.png")
            img = img.resize((240, 240), Image.Resampling.LANCZOS)
        except:
            img = self.create_icon_image()
        
        self.photo = ImageTk.PhotoImage(img)
        self.icon_label = tk.Label(self.main_frame, image=self.photo, bg="#000000")
        self.icon_label.pack(pady=(10, 5))

    def check_audio_file(self):
        """Check if audio file exists"""
        audio_files = ["saikai.mp3", "SAIKAI.mp3", "song.mp3", "music.mp3"]
        
        for filename in audio_files:
            if os.path.exists(filename):
                self.audio_file = filename
                self.status_label.config(
                    text=f"♪ Loaded: {filename} | Press START to play with music", 
                    fg="#4FACFF"
                )
                return
        
        if audio_available:
            self.status_label.config(
                text="Click LOAD AUDIO to select your music file, or START for lyrics only", 
                fg="#888888"
            )
        else:
            self.status_label.config(
                text="Install 'python-vlc' for audio: pip install python-vlc | or START for lyrics only", 
                fg="#888888"
            )
    
    def load_audio_file(self):
        """Open file dialog to select audio"""
        filename = filedialog.askopenfilename(
            title="Select SAIKAI audio file",
            filetypes=[("Audio Files", "*.mp3 *.wav *.m4a"), ("All Files", "*.*")]
        )
        
        if filename:
            self.audio_file = filename
            basename = os.path.basename(filename)
            self.status_label.config(
                text=f"♪ Loaded: {basename} | Press START to play", 
                fg="#4FACFF"
            )
    
    def play_audio_thread(self):
        """Play audio in separate thread using VLC"""
        if audio_available and self.audio_file and not self.audio_playing:
            try:
                self.audio_playing = True
                print(f"Playing: {self.audio_file}")
                
                # Create VLC instance and media player
                instance = vlc.Instance()
                self.media = instance.media_list_new()
                media = instance.media_new(self.audio_file)
                self.media.add_media(media)
                
                self.player = instance.media_list_player_new()
                self.player.set_media_list(self.media)
                self.player.play()
                
                # Keep audio playing while lyrics are playing
                while self.audio_playing and self.is_playing:
                    time.sleep(0.1)
                
                print("Playback finished or stopped")
            except Exception as e:
                print(f"Audio playback error: {e}")
            finally:
                self.audio_playing = False

    def toggle_playback(self):
        """Start or pause playback"""
        if not self.is_playing:
            self.start_playback()
        else:
            self.pause_playback()

    def start_playback(self):
        """Start playing the lyrics"""
        self.is_playing = True
        
        # If resuming, adjust start time to account for paused duration
        if self.paused_time > 0:
            self.song_start_time = time.time() - self.paused_time
            # Unpause VLC player
            if hasattr(self, 'player') and self.player:
                self.player.play()
                print("Audio resumed")
            self.status_label.config(text="♪ Resuming...", fg="#4FACFF")
        else:
            self.song_start_time = time.time()
            self.status_label.config(text="♪ Playing lyrics...", fg="#4FACFF")
            
            # Play audio if available (only on first start, not on resume)
            if self.audio_file and audio_available and not self.audio_playing:
                self.audio_thread = threading.Thread(target=self.play_audio_thread, daemon=True)
                self.audio_thread.start()
                self.status_label.config(text="♪ Playing with audio...", fg="#4FACFF")
        
        self.play_btn.config(text="[ ⏸ PAUSE ]")
        
        # Start lyric sync
        self.sync_lyrics()

    def pause_playback(self):
        """Pause the playback"""
        self.is_playing = False
        
        # Pause VLC player
        if hasattr(self, 'player') and self.player:
            self.player.pause()
            print("Audio paused")
        
        # Save the current elapsed time
        if self.song_start_time:
            self.paused_time = time.time() - self.song_start_time
        
        self.play_btn.config(text="[ ▶ RESUME ]")
        
        if self.sync_timer:
            self.root.after_cancel(self.sync_timer)
        
        self.status_label.config(text="Paused", fg="#888888")

    def reset_song(self):
        """Reset to beginning"""
        if self.sync_timer:
            self.root.after_cancel(self.sync_timer)
        
        # Proper VLC cleanup
        if hasattr(self, 'player') and self.player:
            self.player.stop()
            try:
                self.player.release()
            except:
                pass
        if hasattr(self, 'media'):
            try:
                self.media.release()
            except:
                pass
        
        self.audio_playing = False
            
        self.is_playing = False
        self.current_lyric_index = 0
        self.song_start_time = None
        self.paused_time = 0
        self.play_btn.config(text="[ ▶ START ]")
        self.lyric_label.config(text="")
        self.next_lyric_label.config(text="")
        self.time_label.config(text="0:00 / 5:24")
        
        if self.audio_file:
            self.status_label.config(text=f"♪ Ready | Press START to play", fg="#4FACFF")
        else:
            self.status_label.config(text="Click LOAD AUDIO or press START for lyrics only", fg="#888888")
        
        self.progress_bar.coords(self.progress_fill, 0, 0, 0, 8)

    def on_closing(self):
        """Handle window close"""
        self.audio_playing = False
        if hasattr(self, 'player') and self.player:
            try:
                self.player.stop()
                self.player.release()
            except:
                pass
        self.root.destroy()

    def sync_lyrics(self):
        """Sync lyrics with timeline"""
        if not self.is_playing:
            return
            
        current_time = time.time() - self.song_start_time
        
        # Update progress bar
        if len(lyrics) > 0:
            total_duration = lyrics[-1][0] + lyrics[-1][1]
            progress_width = self.progress_bar.winfo_width()
            fill_width = (current_time / total_duration) * progress_width
            self.progress_bar.coords(self.progress_fill, 0, 0, fill_width, 8)
            
            # Update time display
            current_min = int(current_time // 60)
            current_sec = int(current_time % 60)
            total_min = int(total_duration // 60)
            total_sec = int(total_duration % 60)
            self.time_label.config(text=f"{current_min}:{current_sec:02d} / {total_min}:{total_sec:02d}")
        
        # Check if it's time for next lyric
        if self.current_lyric_index < len(lyrics):
            lyric_time, duration, text = lyrics[self.current_lyric_index]
            
            if current_time >= lyric_time:
                # Reveal this lyric
                self.reveal_lyric(text)
                
                # Show next lyric preview
                if self.current_lyric_index + 1 < len(lyrics):
                    next_text = lyrics[self.current_lyric_index + 1][2]
                    self.next_lyric_label.config(text=f"↓ {next_text}")
                else:
                    self.next_lyric_label.config(text="")
                
                self.current_lyric_index += 1
        
        # Check if song is finished
        if current_time >= lyrics[-1][0] + lyrics[-1][1]:
            self.on_song_end()
            return
        
        # Continue syncing
        self.sync_timer = self.root.after(50, self.sync_lyrics)

    def on_song_end(self):
        """Called when song ends"""
        self.is_playing = False
        self.play_btn.config(text="[ ▶ REPLAY ]")
        self.status_label.config(text="♪ Sequence complete", fg="#4FACFF")

    def reveal_lyric(self, text):
        """Reveal a lyric with glitch effect"""
        # Check if this is the instrumental glitch section
        if text == "[INSTRUMENTAL_GLITCH]":
            self.start_glitch_mode()
            return
            
        self.target_text = text.upper()
        self.current_display = [" " for _ in self.target_text]
        self.revealed_indices = set()
        self.is_revealing = True
        self.reveal_step()

    def apply_bloom(self, text):
        offsets = [(-3,-3), (3,3), (-2,2), (2,-2)]  # chromatic separation
        alphas  = [30, 25, 40, 20]   # 0–255
    
        for i, lbl in enumerate(self.glow_labels):
            lbl.config(text=text)
            lbl.place(x=500 + offsets[i][0], y=300 + offsets[i][1])

    def start_glitch_mode(self):
        """Start continuous glitch animation for instrumental outro"""
        self.is_revealing = True
        self.glitch_intensity = 0
        self.glitch_animation()
    
    def glitch_animation(self):
        """Display chaotic multi-layered glitching during instrumental"""
        if not self.is_playing or not self.is_revealing:
            return
        
        # Check current time - stop glitching 10 seconds before song ends
        current_time = time.time() - self.song_start_time
        total_duration = lyrics[-1][0] + lyrics[-1][1]
        
        if current_time >= total_duration - 10:
            self.lyric_label.config(text="", fg="#4FACFF")
            self.is_revealing = False
            return
        
        # Increase intensity over time for more chaos
        elapsed = current_time - lyrics[-1][0]
        self.glitch_intensity = min(1.0, elapsed / 20.0)
        
        # Generate multiple layers of glitch
        layers = []
        num_layers = random.randint(2, 5)
        
        glitch_sets = [
            "█▓▒░",
            "▀▄▌▐",
            "<>[]{}()",
            "/\\|--",
            "=+*^",
            "%$#@!",
            "~`'\"",
            ".,;:",
            "0123456789",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "ERROR_NULL_VOID_INDEX",
        ]
        
        for layer in range(num_layers):
            # Random length based on intensity
            min_len = int(5 + self.glitch_intensity * 15)
            max_len = int(20 + self.glitch_intensity * 60)
            length = random.randint(min_len, max_len)
            
            # Mix character sets based on intensity
            if random.random() < self.glitch_intensity:
                # High intensity: mix multiple sets
                char_set = ''.join(random.choice(glitch_sets) for _ in range(random.randint(2, 4)))
            else:
                # Low intensity: single set
                char_set = random.choice(glitch_sets)
            
            layer_text = ''.join(random.choice(char_set) for _ in range(length))
            layers.append(layer_text)
        
        # Combine layers with spacing
        glitch_text = "   ".join(layers)
        
        # Random color flickering
        colors = ["#4FACFF", "#8b0000", "#FF00FF", "#00FF00", "#FFFF00", "#FFFFFF"]
        if random.random() < self.glitch_intensity * 0.3:
            color = random.choice(colors)
        else:
            color = "#4FACFF"
        
        self.lyric_label.config(text=glitch_text, fg=color)
        
        # Random next lyric glitching
        if random.random() < self.glitch_intensity * 0.5:
            next_glitch = ''.join(random.choice("░▒▓█") for _ in range(random.randint(10, 30)))
            self.next_lyric_label.config(text=next_glitch, fg=random.choice(["#333333", "#8b0000"]))
        else:
            self.next_lyric_label.config(text="", fg="#333333")
        
        # Variable timing based on intensity - ULTRA FAST
        min_delay = max(5, int(25 - self.glitch_intensity * 15))
        max_delay = max(15, int(50 - self.glitch_intensity * 30))
        delay = random.randint(min_delay, max_delay)
        
        # Continue glitching
        self.root.after(delay, self.glitch_animation)

    def get_intense_glitch_char(self):
        """Get a glitch character from expanded set"""
        glitch_sets = [
            "█▓▒░",
            "▀▄▌▐■□",
            "<>[]{}()",
            "/\\|--",
            "=+*^~",
            "%$#@!?",
            "0123456789",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        ]
        return random.choice(random.choice(glitch_sets))
    
    def get_glitch_char(self):
        return random.choice("█▓▒░<>[]/\\|--=+*^%$#@!")

    def reveal_step(self):
        """Animate lyric reveal with intense glitch effect"""
        if len(self.revealed_indices) >= len(self.target_text):
            self.lyric_label.config(text=self.target_text, fg="#4FACFF")
            self.is_revealing = False
            return
        
        # Reveal 1-2 characters at a time (slower reveal for longer glitch time)
        for _ in range(random.randint(1, 2)):
            available = [i for i in range(len(self.target_text)) if i not in self.revealed_indices]
            if available:
                idx = random.choice(available)
                self.revealed_indices.add(idx)
                self.current_display[idx] = self.target_text[idx]
        
        # Create INTENSE glitch effect with multi-layered chaos
        flicker_text = list(self.current_display)
        
        # Add random complete corruption occasionally
        if random.random() < 0.3:
            # Full screen corruption
            glitch_length = len(self.target_text) + random.randint(-10, 20)
            glitch_chars = "█▓▒░<>[]{}()/\\|--=+*^%$#@!~`'\".,:;0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            flicker_text = [random.choice(glitch_chars) for _ in range(max(1, glitch_length))]
        else:
            # Normal glitching with extra chaos
            for i in range(len(flicker_text)):
                if i not in self.revealed_indices:
                    if random.random() > 0.2:  # More glitch density (was 0.4)
                        flicker_text[i] = self.get_intense_glitch_char()
                    
            # Add random insertions
            if random.random() < 0.4:
                insert_pos = random.randint(0, len(flicker_text))
                extra_glitch = ''.join(self.get_intense_glitch_char() for _ in range(random.randint(3, 8)))
                flicker_text.insert(insert_pos, extra_glitch)
        
        # Random color flicker during reveal
        colors = ["#4FACFF", "#b30000", "#FF00FF", "#00FF00", "#F0F080"]
        if random.random() < 0.25:
            color = random.choice(colors)
        else:
            color = "#3CA1F9"
        
        display_text = "".join(str(c) for c in flicker_text)
        self.lyric_label.config(text=display_text, fg=color)
        
        # FASTER updates for more intense glitching (was 35-60)
        self.root.after(random.randint(20, 35), self.reveal_step)

    def on_progress_click(self, event):
        """Handle progress bar click to seek to position"""
        if not lyrics:
            return
        
        # Calculate clicked position
        progress_width = self.progress_bar.winfo_width()
        click_ratio = event.x / progress_width if progress_width > 0 else 0
        
        # Get total duration
        total_duration = lyrics[-1][0] + lyrics[-1][1]
        new_time = click_ratio * total_duration
        
        # Update internal time tracking
        if self.song_start_time:
            self.song_start_time = time.time() - new_time
            self.paused_time = new_time
            
            # Seek VLC player if available
            if hasattr(self, 'player') and self.player:
                try:
                    self.player.get_media_player().set_time(int(new_time * 1000))
                except:
                    pass
            
            # Reset lyric index to find correct starting point
            self.current_lyric_index = 0
            for i, (lyric_time, duration, text) in enumerate(lyrics):
                if lyric_time <= new_time < lyric_time + duration:
                    self.current_lyric_index = i
                    self.reveal_lyric(text)
                    break
                elif lyric_time > new_time:
                    self.current_lyric_index = i
                    break