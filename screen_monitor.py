import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageGrab, ImageTk
import pytesseract
import requests
import keyboard
import threading
import time
import io
import os
import re
import sys
import json
import webbrowser
import numpy as np
from datetime import datetime

# Config file path
def get_config_path():
    if getattr(sys, 'frozen', False):
        # Running as exe
        return os.path.join(os.path.dirname(sys.executable), 'config.json')
    else:
        # Running as script
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

# Set tesseract path for Windows
if sys.platform == 'win32':
    tesseract_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Tesseract-OCR', 'tesseract.exe')
    ]
    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break

class ZoneSelector(tk.Toplevel):
    """Transparent overlay window for selecting screen zone"""
    
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        # Make fullscreen transparent overlay
        self.attributes('-fullscreen', True)
        self.attributes('-alpha', 0.3)
        self.attributes('-topmost', True)
        self.configure(bg='gray')
        
        # Create canvas
        self.canvas = tk.Canvas(self, cursor='cross', bg='gray', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Bind events
        self.canvas.bind('<Button-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.bind('<Escape>', lambda e: self.destroy())
        
        # Instructions label
        self.label = tk.Label(self, text="Click and drag to select zone. Press ESC to cancel.",
                             font=('Segoe UI', 14), bg='gray', fg='white')
        self.label.place(relx=0.5, rely=0.02, anchor='n')
        
    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='#00ff00', width=3, fill='#00ff00', stipple='gray25'
        )
        
    def on_drag(self, event):
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
            
    def on_release(self, event):
        if self.start_x is not None and self.start_y is not None:
            x1 = min(self.start_x, event.x)
            y1 = min(self.start_y, event.y)
            x2 = max(self.start_x, event.x)
            y2 = max(self.start_y, event.y)
            
            if x2 - x1 > 10 and y2 - y1 > 10:
                self.callback((x1, y1, x2, y2))
        self.destroy()


class ScreenMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # App state
        self.is_running = False
        self.selected_zone = None
        self.monitor_thread = None
        self.last_detected_value = None
        self.change_count = 0
        
        # Target color (orange like in the screenshot - RGB approximately)
        self.target_color = (255, 140, 0)  # Orange color
        self.color_tolerance = 80
        
        # Default settings
        self.delay_seconds = 3.0
        
        # Load saved config
        self.load_config()
        
        # Window setup
        self.title("Screen Monitor")
        self.default_width = 450
        self.default_height = 750
        self.geometry(f"{self.default_width}x{self.default_height}")
        self.minsize(350, 600)
        self.maxsize(800, 1000)
        self.resizable(True, True)
        
        # Always on top
        self.attributes('-topmost', True)
        
        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create UI
        self.create_widgets()
        
        # Load saved values into UI
        self.apply_loaded_config()
        
        # Bind hotkeys
        self.setup_hotkeys()
        
        # Protocol for closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Main container
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Header
        self.header_frame = ctk.CTkFrame(self.main_frame, corner_radius=0, height=100)
        self.header_frame.pack(fill='x', padx=0, pady=0)
        self.header_frame.pack_propagate(False)
        
        # Title row
        self.title_row = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_row.pack(fill='x', padx=10, pady=(10, 0))
        
        self.title_label = ctk.CTkLabel(
            self.title_row, 
            text="🖥️ Screen Monitor",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(side='left', padx=10)
        
        # Switches row
        self.switches_row = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.switches_row.pack(fill='x', padx=10, pady=(5, 10))
        
        # Always on top toggle
        self.topmost_switch = ctk.CTkSwitch(
            self.switches_row,
            text="Always On Top",
            command=self.toggle_topmost,
            onvalue="on",
            offvalue="off"
        )
        self.topmost_switch.pack(side='left', padx=10)
        self.topmost_switch.select()  # Default on top
        
        # Theme toggle
        self.theme_switch = ctk.CTkSwitch(
            self.switches_row,
            text="Dark Mode",
            command=self.toggle_theme,
            onvalue="dark",
            offvalue="light"
        )
        self.theme_switch.pack(side='left', padx=20)
        self.theme_switch.select()  # Default dark mode
        
        # Scrollable container with both scrollbars
        self.scroll_container = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.scroll_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Create canvas for scrolling
        self.canvas = tk.Canvas(self.scroll_container, highlightthickness=0)
        
        # Vertical scrollbar
        self.v_scrollbar = ctk.CTkScrollbar(self.scroll_container, orientation="vertical", command=self.canvas.yview)
        self.v_scrollbar.pack(side='right', fill='y')
        
        # Horizontal scrollbar
        self.h_scrollbar = ctk.CTkScrollbar(self.scroll_container, orientation="horizontal", command=self.canvas.xview)
        self.h_scrollbar.pack(side='bottom', fill='x')
        
        # Pack canvas
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # Create content frame inside canvas
        self.content_frame = ctk.CTkFrame(self.canvas, corner_radius=10)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor='nw')
        
        # Bind events for scrolling
        self.content_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Bind mouse wheel
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind_all('<Shift-MouseWheel>', self._on_shift_mousewheel)
        
        # Update canvas background based on theme
        self._update_canvas_bg()
        
        # Subscribe Section (at top)
        self.subscribe_section = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.subscribe_section.pack(fill='x', padx=15, pady=(15, 10))
        
        self.subscribe_btn = ctk.CTkButton(
            self.subscribe_section,
            text="🔔 Subscribe to the Author",
            command=self.open_youtube,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#FF0000",
            hover_color="#CC0000"
        )
        self.subscribe_btn.pack(fill='x', padx=15, pady=15)
        
        # Zone Selection Section
        self.zone_section = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.zone_section.pack(fill='x', padx=15, pady=10)
        
        self.zone_label = ctk.CTkLabel(
            self.zone_section,
            text="📍 Zone Selection",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.zone_label.pack(anchor='w', padx=15, pady=(10, 5))
        
        self.select_zone_btn = ctk.CTkButton(
            self.zone_section,
            text="Select Zone",
            command=self.select_zone,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="#6366f1",
            hover_color="#4f46e5"
        )
        self.select_zone_btn.pack(fill='x', padx=15, pady=(5, 10))
        
        self.zone_status_label = ctk.CTkLabel(
            self.zone_section,
            text="No zone selected",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.zone_status_label.pack(anchor='w', padx=15, pady=(0, 10))
        
        # Changes Count Section
        self.changes_section = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.changes_section.pack(fill='x', padx=15, pady=10)
        
        self.changes_label = ctk.CTkLabel(
            self.changes_section,
            text="🔢 Changes Before Screenshot",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.changes_label.pack(anchor='w', padx=15, pady=(10, 5))
        
        self.changes_hint = ctk.CTkLabel(
            self.changes_section,
            text="Enter number of changes to trigger screenshot (use '-' to disable)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.changes_hint.pack(anchor='w', padx=15, pady=(0, 5))
        
        self.changes_entry = ctk.CTkEntry(
            self.changes_section,
            height=40,
            font=ctk.CTkFont(size=14),
            placeholder_text="Enter number or '-'"
        )
        self.changes_entry.pack(fill='x', padx=15, pady=(5, 10))
        self.changes_entry.insert(0, "5")
        
        # Webhook Section
        self.webhook_section = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.webhook_section.pack(fill='x', padx=15, pady=10)
        
        self.webhook_label = ctk.CTkLabel(
            self.webhook_section,
            text="🔗 Discord Webhook",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.webhook_label.pack(anchor='w', padx=15, pady=(10, 5))
        
        self.webhook_entry = ctk.CTkEntry(
            self.webhook_section,
            height=40,
            font=ctk.CTkFont(size=12),
            placeholder_text="https://discord.com/api/webhooks/..."
        )
        self.webhook_entry.pack(fill='x', padx=15, pady=(5, 5))
        
        # Paste button for webhook
        self.paste_btn = ctk.CTkButton(
            self.webhook_section,
            text="📋 Paste from Clipboard",
            command=self.paste_webhook,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="#4a5568",
            hover_color="#2d3748"
        )
        self.paste_btn.pack(fill='x', padx=15, pady=(0, 10))
        
        # Delay Section
        self.delay_section = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.delay_section.pack(fill='x', padx=15, pady=10)
        
        self.delay_label = ctk.CTkLabel(
            self.delay_section,
            text="⏱️ Delay Before Screenshot (seconds)",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.delay_label.pack(anchor='w', padx=15, pady=(10, 5))
        
        self.delay_entry = ctk.CTkEntry(
            self.delay_section,
            height=40,
            font=ctk.CTkFont(size=14),
            placeholder_text="Enter delay in seconds"
        )
        self.delay_entry.pack(fill='x', padx=15, pady=(5, 10))
        self.delay_entry.insert(0, "3")
        
        # Control Buttons Section
        self.controls_section = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.controls_section.pack(fill='x', padx=15, pady=10)
        
        self.controls_label = ctk.CTkLabel(
            self.controls_section,
            text="⚡ Controls",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.controls_label.pack(anchor='w', padx=15, pady=(10, 5))
        
        self.buttons_frame = ctk.CTkFrame(self.controls_section, fg_color="transparent")
        self.buttons_frame.pack(fill='x', padx=15, pady=(5, 10))
        
        self.start_btn = ctk.CTkButton(
            self.buttons_frame,
            text="▶ Start (F1)",
            command=self.start_monitoring,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#22c55e",
            hover_color="#16a34a"
        )
        self.start_btn.pack(side='left', expand=True, fill='x', padx=(0, 5))
        
        self.stop_btn = ctk.CTkButton(
            self.buttons_frame,
            text="⏹ Stop (F3)",
            command=self.stop_monitoring,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#ef4444",
            hover_color="#dc2626",
            state="disabled"
        )
        self.stop_btn.pack(side='right', expand=True, fill='x', padx=(5, 0))
        
        # Status Section
        self.status_section = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.status_section.pack(fill='x', padx=15, pady=(10, 15))
        
        self.status_label = ctk.CTkLabel(
            self.status_section,
            text="📊 Status",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.status_label.pack(anchor='w', padx=15, pady=(10, 5))
        
        self.status_text = ctk.CTkLabel(
            self.status_section,
            text="Ready. Select a zone and press Start.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_text.pack(anchor='w', padx=15, pady=(0, 5))
        
        self.detected_value_label = ctk.CTkLabel(
            self.status_section,
            text="Detected value: --",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.detected_value_label.pack(anchor='w', padx=15, pady=(0, 5))
        
        self.changes_count_label = ctk.CTkLabel(
            self.status_section,
            text="Changes: 0",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.changes_count_label.pack(anchor='w', padx=15, pady=(0, 10))
        
        # Window Size Section
        self.size_section = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.size_section.pack(fill='x', padx=15, pady=(10, 15))
        
        self.size_label = ctk.CTkLabel(
            self.size_section,
            text="📐 Window Size",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.size_label.pack(anchor='w', padx=15, pady=(10, 5))
        
        # Width slider
        self.width_frame = ctk.CTkFrame(self.size_section, fg_color="transparent")
        self.width_frame.pack(fill='x', padx=15, pady=(5, 0))
        
        self.width_label = ctk.CTkLabel(
            self.width_frame,
            text="Width: 450",
            font=ctk.CTkFont(size=12)
        )
        self.width_label.pack(side='left')
        
        self.width_slider = ctk.CTkSlider(
            self.width_frame,
            from_=350,
            to=800,
            number_of_steps=45,
            command=self.on_width_change
        )
        self.width_slider.pack(side='right', expand=True, fill='x', padx=(10, 0))
        self.width_slider.set(450)
        
        # Height slider
        self.height_frame = ctk.CTkFrame(self.size_section, fg_color="transparent")
        self.height_frame.pack(fill='x', padx=15, pady=(5, 10))
        
        self.height_label = ctk.CTkLabel(
            self.height_frame,
            text="Height: 750",
            font=ctk.CTkFont(size=12)
        )
        self.height_label.pack(side='left')
        
        self.height_slider = ctk.CTkSlider(
            self.height_frame,
            from_=600,
            to=1000,
            number_of_steps=40,
            command=self.on_height_change
        )
        self.height_slider.pack(side='right', expand=True, fill='x', padx=(10, 0))
        self.height_slider.set(750)
        
        # Made by Sayson label at bottom
        self.credits_label = ctk.CTkLabel(
            self.content_frame,
            text="Made by Sayson",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="gray"
        )
        self.credits_label.pack(pady=(10, 20))
        
    def open_youtube(self):
        """Open author's YouTube channel"""
        webbrowser.open("https://www.youtube.com/@sayson6129")
        
    def _on_frame_configure(self, event):
        """Update scroll region when content changes"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        
    def _on_canvas_configure(self, event):
        """Update canvas window width when canvas resizes"""
        # Set minimum width for content
        min_width = max(event.width, 400)
        self.canvas.itemconfig(self.canvas_window, width=min_width)
        
    def _on_mousewheel(self, event):
        """Vertical scroll with mouse wheel"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        
    def _on_shift_mousewheel(self, event):
        """Horizontal scroll with Shift + mouse wheel"""
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), 'units')
        
    def _update_canvas_bg(self):
        """Update canvas background to match theme"""
        if ctk.get_appearance_mode() == "Dark":
            self.canvas.configure(bg='#2b2b2b')
        else:
            self.canvas.configure(bg='#dbdbdb')
        
    def on_width_change(self, value):
        width = int(value)
        self.width_label.configure(text=f"Width: {width}")
        self.geometry(f"{width}x{self.winfo_height()}")
        
    def on_height_change(self, value):
        height = int(value)
        self.height_label.configure(text=f"Height: {height}")
        self.geometry(f"{self.winfo_width()}x{height}")
        
    def toggle_topmost(self):
        if self.topmost_switch.get() == "on":
            self.attributes('-topmost', True)
        else:
            self.attributes('-topmost', False)
        
    def toggle_theme(self):
        if self.theme_switch.get() == "dark":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
        self._update_canvas_bg()
    
    def paste_webhook(self):
        """Paste webhook URL from clipboard"""
        try:
            clipboard_text = self.clipboard_get()
            self.webhook_entry.delete(0, 'end')
            self.webhook_entry.insert(0, clipboard_text)
        except:
            pass
    
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            config_path = get_config_path()
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.saved_webhook = config.get('webhook', '')
                    self.saved_changes = config.get('changes', '5')
                    self.saved_delay = config.get('delay', '3')
                    self.saved_zone = config.get('zone', None)
                    self.delay_seconds = float(config.get('delay', 3))
                    if self.saved_zone:
                        self.selected_zone = tuple(self.saved_zone)
            else:
                self.saved_webhook = ''
                self.saved_changes = '5'
                self.saved_delay = '3'
                self.saved_zone = None
        except Exception as e:
            print(f"Error loading config: {e}")
            self.saved_webhook = ''
            self.saved_changes = '5'
            self.saved_delay = '3'
            self.saved_zone = None
    
    def apply_loaded_config(self):
        """Apply loaded config to UI elements"""
        try:
            if hasattr(self, 'saved_webhook') and self.saved_webhook:
                self.webhook_entry.delete(0, 'end')
                self.webhook_entry.insert(0, self.saved_webhook)
            if hasattr(self, 'saved_changes') and self.saved_changes:
                self.changes_entry.delete(0, 'end')
                self.changes_entry.insert(0, self.saved_changes)
            if hasattr(self, 'saved_delay') and self.saved_delay:
                self.delay_entry.delete(0, 'end')
                self.delay_entry.insert(0, self.saved_delay)
            if self.selected_zone:
                self.zone_status_label.configure(
                    text=f"Zone: ({self.selected_zone[0]}, {self.selected_zone[1]}) to ({self.selected_zone[2]}, {self.selected_zone[3]})",
                    text_color="#22c55e"
                )
        except Exception as e:
            print(f"Error applying config: {e}")
    
    def save_config(self):
        """Save configuration to JSON file"""
        try:
            config = {
                'webhook': self.webhook_entry.get().strip(),
                'changes': self.changes_entry.get().strip(),
                'delay': self.delay_entry.get().strip(),
                'zone': list(self.selected_zone) if self.selected_zone else None
            }
            config_path = get_config_path()
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_delay(self):
        """Get delay value from entry"""
        try:
            return float(self.delay_entry.get().strip())
        except:
            return 3.0
            
    def setup_hotkeys(self):
        keyboard.add_hotkey('F1', self.start_monitoring)
        keyboard.add_hotkey('F3', self.stop_monitoring)
        
    def select_zone(self):
        self.withdraw()  # Hide main window
        time.sleep(0.3)  # Small delay
        
        def on_zone_selected(zone):
            self.selected_zone = zone
            self.deiconify()  # Show main window
            self.zone_status_label.configure(
                text=f"Zone: ({zone[0]}, {zone[1]}) to ({zone[2]}, {zone[3]})",
                text_color="#22c55e"
            )
            self.update_status("Zone selected. Ready to start.")
            
        selector = ZoneSelector(on_zone_selected)
        selector.wait_window()
        self.deiconify()
        
    def get_changes_threshold(self):
        value = self.changes_entry.get().strip()
        if value == "-":
            return None  # Disabled
        try:
            return int(value)
        except ValueError:
            return None
            
    def extract_orange_text(self, image):
        """Extract text that has orange/yellow colored text from the image"""
        try:
            img_array = np.array(image)
            from PIL import ImageOps
            
            # Check minimum size
            if img_array.shape[0] < 5 or img_array.shape[1] < 5:
                return None
            
            r, g, b = img_array[:,:,0].astype(float), img_array[:,:,1].astype(float), img_array[:,:,2].astype(float)
            
            # Orange-yellow text detection (like "8191" "8192")
            orange_yellow_mask = (
                (r >= 170) &           
                (g >= 80) &           
                (g <= 220) &           
                (b <= 130) &           
                (r > b + 50) &         
                (r >= g - 50)          
            )
            
            # Brighter orange
            bright_orange_mask = (
                (r >= 190) &
                (g >= 70) & (g <= 210) &
                (b <= 110)
            )
            
            # Combine masks
            combined_mask = orange_yellow_mask | bright_orange_mask
            
            # Create binary image
            result = np.zeros((img_array.shape[0], img_array.shape[1]), dtype=np.uint8)
            result[combined_mask] = 255
            
            # Convert to PIL Image
            filtered_image = Image.fromarray(result)
            
            # Scale up for better OCR
            width, height = filtered_image.size
            scale = 4
            new_width = max(width * scale, 20)
            new_height = max(height * scale, 20)
            filtered_image = filtered_image.resize((new_width, new_height), Image.Resampling.NEAREST)
            
            # Invert for OCR (black text on white)
            filtered_image = ImageOps.invert(filtered_image)
            
            # OCR configurations
            configs = [
                r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789',
                r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789', 
                r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789',
            ]
            
            best_result = None
            for config in configs:
                try:
                    text = pytesseract.image_to_string(filtered_image, config=config)
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        longest = max(numbers, key=len)
                        if best_result is None or len(longest) > len(best_result):
                            best_result = longest
                except:
                    continue
            
            return best_result
        except Exception as e:
            print(f"Extract error: {e}")
            return None
        
    def capture_zone(self):
        """Capture the selected zone"""
        if self.selected_zone:
            return ImageGrab.grab(bbox=self.selected_zone)
        return None
        
    def capture_fullscreen(self):
        """Capture full screen"""
        return ImageGrab.grab()
        
    def send_to_discord(self, screenshot, detected_value):
        """Send screenshot to Discord webhook"""
        webhook_url = self.webhook_entry.get().strip()
        
        if not webhook_url:
            self.update_status("Error: No webhook URL provided")
            return False
            
        try:
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Prepare the message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"📸 **Screen Capture**\n🔢 Detected Value: **{detected_value}**\n⏰ Time: {timestamp}"
            
            # Send to Discord
            files = {'file': ('screenshot.png', img_byte_arr, 'image/png')}
            data = {'content': message}
            
            response = requests.post(webhook_url, data=data, files=files)
            
            if response.status_code in [200, 204]:
                self.update_status(f"Screenshot sent! Value: {detected_value}")
                return True
            else:
                self.update_status(f"Webhook error: {response.status_code}")
                return False
                
        except Exception as e:
            self.update_status(f"Error sending: {str(e)}")
            return False
            
    def monitor_loop(self):
        """Main monitoring loop"""
        self.last_detected_value = None
        self.change_count = 0
        self.stable_value = None
        self.stable_count = 0
        STABILITY_THRESHOLD = 2  # Value must be the same 2 times to be considered stable
        
        while self.is_running:
            try:
                # Capture zone
                zone_image = self.capture_zone()
                if zone_image is None:
                    time.sleep(0.5)
                    continue
                    
                # Extract text
                detected = self.extract_orange_text(zone_image)
                
                if detected:
                    # Update UI with current detection
                    self.after(0, lambda v=detected: self.detected_value_label.configure(
                        text=f"Detected value: {v}"
                    ))
                    
                    # Stability check - only count as real value if detected multiple times
                    if detected == self.stable_value:
                        self.stable_count += 1
                    else:
                        self.stable_value = detected
                        self.stable_count = 1
                    
                    # Only process if value is stable (detected multiple times in a row)
                    if self.stable_count >= STABILITY_THRESHOLD:
                        # If this is the first stable value, just record it
                        if self.last_detected_value is None:
                            self.last_detected_value = self.stable_value
                            self.after(0, lambda v=self.stable_value: self.update_status(f"Initial value: {v}"))
                        # Check for actual change from last confirmed value
                        elif self.stable_value != self.last_detected_value:
                            self.change_count += 1
                            self.after(0, lambda c=self.change_count: self.changes_count_label.configure(
                                text=f"Changes: {c}"
                            ))
                            self.after(0, lambda old=self.last_detected_value, new=self.stable_value: 
                                self.update_status(f"Change detected: {old} → {new}"))
                            
                            # Update last confirmed value BEFORE checking threshold
                            self.last_detected_value = self.stable_value
                            
                            # Check threshold
                            threshold = self.get_changes_threshold()
                            if threshold is not None and self.change_count >= threshold:
                                # Wait for delay before taking screenshot
                                delay = self.get_delay()
                                self.after(0, lambda d=delay: self.update_status(f"Waiting {d}s before screenshot..."))
                                time.sleep(delay)
                                
                                # Take full screenshot and send
                                self.after(0, lambda: self.update_status("Taking screenshot..."))
                                fullscreen = self.capture_fullscreen()
                                self.send_to_discord(fullscreen, self.stable_value)
                                self.change_count = 0
                                self.after(0, lambda: self.changes_count_label.configure(text="Changes: 0"))
                    
                time.sleep(0.3)  # Poll interval
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(1)
                
    def start_monitoring(self):
        if self.is_running:
            return
            
        if self.selected_zone is None:
            messagebox.showwarning("Warning", "Please select a zone first!")
            return
            
        threshold = self.get_changes_threshold()
        if threshold is None and self.changes_entry.get().strip() != "-":
            messagebox.showwarning("Warning", "Please enter a valid number or '-' to disable!")
            return
            
        self.is_running = True
        self.change_count = 0
        self.last_detected_value = None
        
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.update_status("Monitoring started...")
        self.changes_count_label.configure(text="Changes: 0")
        
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        if not self.is_running:
            return
            
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.update_status("Monitoring stopped.")
        
    def update_status(self, text):
        self.status_text.configure(text=text)
        
    def on_closing(self):
        self.save_config()
        self.is_running = False
        keyboard.unhook_all()
        self.destroy()


if __name__ == "__main__":
    app = ScreenMonitorApp()
    app.mainloop()
