import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import os
import threading
from datetime import datetime
import random
import sys
import math
import json
import pystray
from PIL import Image
import keyboard

# Hide PowerShell windows on Windows
SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0


class AnimatedOrb:
    """Animated green/black orb background inspired by Ampcode"""
    
    def __init__(self, canvas, colors):
        self.canvas = canvas
        self.colors = colors
        self.width = 900
        self.height = 650
        
        # Orb state
        self.orb_x = self.width // 2
        self.orb_y = self.height // 2
        self.orb_target_x = self.orb_x
        self.orb_target_y = self.orb_y
        self.orb_radius = 120  # Larger orb
        self.orb_pulse = 0
        
        # Mouse state
        self.mouse_x = self.width // 2
        self.mouse_y = self.height // 2
        
        # Particles - more for fuller effect
        self.particles = []
        self.num_particles = 80
        self.init_particles()
        
        # Click burst state
        self.bursts = []
        
        # Energy rings
        self.rings = []
        
        # Bind mouse events
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Configure>", self.on_resize)
        
        # Start animation
        self.animate()
    
    def init_particles(self):
        """Initialize floating particles"""
        self.particles = []
        for _ in range(self.num_particles):
            self.particles.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-0.5, 0.5),
                'size': random.uniform(1, 3),
                'brightness': random.uniform(0.3, 1.0),
                'phase': random.uniform(0, math.pi * 2),
            })
    
    def on_resize(self, event):
        self.width = event.width
        self.height = event.height
    
    def on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        self.orb_target_x = event.x
        self.orb_target_y = event.y
    
    def on_click(self, event):
        """Create burst effect on click"""
        self.bursts.append({
            'x': event.x,
            'y': event.y,
            'radius': 0,
            'max_radius': 200,
            'alpha': 1.0,
            'rings': [],
        })
        # Add shockwave rings
        for i in range(4):
            self.rings.append({
                'x': event.x,
                'y': event.y,
                'radius': i * 10,
                'alpha': 1.0,
                'speed': 8 + i * 2,
            })
        # Scatter nearby particles
        for p in self.particles:
            dx = p['x'] - event.x
            dy = p['y'] - event.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 150 and dist > 0:
                force = (150 - dist) / 15
                p['vx'] += (dx / dist) * force
                p['vy'] += (dy / dist) * force
    
    def lerp(self, a, b, t):
        return a + (b - a) * t
    
    def animate(self):
        """Main animation loop"""
        self.canvas.delete("orb_bg")
        
        # Update orb position (smooth follow)
        self.orb_x = self.lerp(self.orb_x, self.orb_target_x, 0.03)
        self.orb_y = self.lerp(self.orb_y, self.orb_target_y, 0.03)
        self.orb_pulse += 0.05
        
        # Draw outer glow layers - larger spread
        pulse_offset = math.sin(self.orb_pulse) * 15
        for i in range(8, 0, -1):
            r = self.orb_radius + i * 35 + pulse_offset
            intensity = int(25 - i * 3)
            color = f"#{0:02x}{max(0,intensity):02x}{0:02x}"
            self.canvas.create_oval(
                self.orb_x - r, self.orb_y - r,
                self.orb_x + r, self.orb_y + r,
                fill=color, outline="",
                tags="orb_bg"
            )
        
        # Draw orb core
        core_pulse = self.orb_radius + math.sin(self.orb_pulse * 1.5) * 5
        for i in range(5, 0, -1):
            r = core_pulse * (i / 5)
            g = int(80 + (5 - i) * 35)
            color = f"#{0:02x}{min(255, g):02x}{int(g*0.4):02x}"
            self.canvas.create_oval(
                self.orb_x - r, self.orb_y - r,
                self.orb_x + r, self.orb_y + r,
                fill=color, outline="",
                tags="orb_bg"
            )
        
        # Update and draw particles
        for p in self.particles:
            # Attract to orb slightly
            dx = self.orb_x - p['x']
            dy = self.orb_y - p['y']
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist > 0:
                # Orbit around orb
                attract = 0.02
                p['vx'] += (dx / dist) * attract
                p['vy'] += (dy / dist) * attract
                
                # Tangential velocity for orbit effect
                p['vx'] += (-dy / dist) * 0.01
                p['vy'] += (dx / dist) * 0.01
            
            # Mouse repulsion
            mx = p['x'] - self.mouse_x
            my = p['y'] - self.mouse_y
            mouse_dist = math.sqrt(mx*mx + my*my)
            if mouse_dist < 100 and mouse_dist > 0:
                repel = (100 - mouse_dist) / 500
                p['vx'] += (mx / mouse_dist) * repel
                p['vy'] += (my / mouse_dist) * repel
            
            # Apply velocity with damping
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vx'] *= 0.98
            p['vy'] *= 0.98
            
            # Wrap around edges
            if p['x'] < 0: p['x'] = self.width
            if p['x'] > self.width: p['x'] = 0
            if p['y'] < 0: p['y'] = self.height
            if p['y'] > self.height: p['y'] = 0
            
            # Pulsing brightness
            p['phase'] += 0.02
            brightness = p['brightness'] * (0.7 + 0.3 * math.sin(p['phase']))
            
            # Distance-based brightness
            if dist < 200:
                brightness *= (0.5 + 0.5 * (dist / 200))
            
            g = int(brightness * 255)
            color = f"#{0:02x}{g:02x}{int(g*0.5):02x}"
            
            size = p['size']
            self.canvas.create_oval(
                p['x'] - size, p['y'] - size,
                p['x'] + size, p['y'] + size,
                fill=color, outline="",
                tags="orb_bg"
            )
        
        # Draw energy connections between close particles
        for i, p1 in enumerate(self.particles[:20]):
            for p2 in self.particles[i+1:20]:
                dx = p1['x'] - p2['x']
                dy = p1['y'] - p2['y']
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 80:
                    alpha = int((1 - dist/80) * 40)
                    color = f"#{0:02x}{alpha:02x}{0:02x}"
                    self.canvas.create_line(
                        p1['x'], p1['y'], p2['x'], p2['y'],
                        fill=color, width=1,
                        tags="orb_bg"
                    )
        
        # Update and draw burst effects
        active_bursts = []
        for burst in self.bursts:
            burst['radius'] += 12
            burst['alpha'] -= 0.03
            
            if burst['alpha'] > 0:
                # Draw expanding burst
                for i in range(3):
                    r = burst['radius'] - i * 15
                    if r > 0:
                        intensity = int(burst['alpha'] * 100 * (1 - i * 0.3))
                        color = f"#{0:02x}{max(0,intensity):02x}{0:02x}"
                        self.canvas.create_oval(
                            burst['x'] - r, burst['y'] - r,
                            burst['x'] + r, burst['y'] + r,
                            outline=color, width=3-i,
                            tags="orb_bg"
                        )
                active_bursts.append(burst)
        self.bursts = active_bursts
        
        # Update and draw shockwave rings
        active_rings = []
        for ring in self.rings:
            ring['radius'] += ring['speed']
            ring['alpha'] -= 0.025
            
            if ring['alpha'] > 0:
                intensity = int(ring['alpha'] * 180)
                color = f"#{0:02x}{intensity:02x}{int(intensity*0.6):02x}"
                self.canvas.create_oval(
                    ring['x'] - ring['radius'], ring['y'] - ring['radius'],
                    ring['x'] + ring['radius'], ring['y'] + ring['radius'],
                    outline=color, width=2,
                    tags="orb_bg"
                )
                active_rings.append(ring)
        self.rings = active_rings
        
        # Continue animation
        self.canvas.after(16, self.animate)

# Minimalist ASCII banner - clean pixel-art style
ASCII_BANNER = r"""
 ╦  ╦╔═╗╔╦╗╔╦╗╔═╗╔═╗╦  ╔═╗
 ╚╗╔╝║ ║║║║ ║ ║ ║║ ║║  ╚═╗
  ╚╝ ╚═╝╩ ╩ ╩ ╚═╝╚═╝╩═╝╚═╝
"""

class VomTools:
    def __init__(self, root):
        self.root = root
        self.root.title("VomTools")
        self.root.configure(bg="#0c0c0c")
        self.root.resizable(True, True)
        self.root.overrideredirect(True)  # Remove window title bar
        self.root.attributes('-topmost', True)  # Always on top
        
        # Position window at bottom center of screen
        win_width, win_height = 900, 650
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - win_width) // 2
        y = screen_height - win_height
        self.root.geometry(f"{win_width}x{win_height}+{x}+{y}")
        
        # Set icon
        icon_path = os.path.join(os.path.dirname(__file__), 'vomtools.ico')
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        
        # Modern monospace fonts
        self.hacker_fonts = [
            "JetBrains Mono", "Fira Code", "Cascadia Code", "Consolas",
            "SF Mono", "Menlo", "Monaco", "Courier New"
        ]
        self.main_font = self.get_available_font(11)
        self.small_font = self.get_available_font(10)
        self.banner_font = self.get_available_font(12)
        self.tiny_font = self.get_available_font(8)
        
        # Sleek cyberpunk color palette
        self.colors = {
            'bg': '#0c0c0c',
            'bg_secondary': '#111111',
            'bg_elevated': '#0f0f0f',   # Darker for less obstruction
            'bg_hover': '#141414',
            'bg_trans': '#0c0c0c',      # "Transparent" (matches canvas)
            'primary': '#00ff9f',       # Neon mint
            'primary_dim': '#00aa6b',
            'primary_dark': '#004d31',
            'secondary': '#00d4ff',     # Cyan accent
            'text': '#e0e0e0',
            'text_dim': '#666666',
            'text_muted': '#444444',
            'error': '#ff3366',
            'warning': '#ffaa00',
            'success': '#00ff9f',
            'border': '#1f1f1f',
            'glow': '#00ff9f',
        }
        
        # Animation state
        self.cursor_visible = True
        self.animated_orb = None
        
        # Clipboard history for clipboard manager
        self.clipboard_history = []
        self.last_clipboard = ""
        
        # Quick launcher apps (customizable)
        self.quick_launch_apps = [
            {"name": "Notepad", "path": "notepad.exe", "icon": "📝"},
            {"name": "Calculator", "path": "calc.exe", "icon": "🔢"},
            {"name": "Explorer", "path": "explorer.exe", "icon": "📁"},
            {"name": "Task Manager", "path": "taskmgr.exe", "icon": "📊"},
            {"name": "Command Prompt", "path": "cmd.exe", "icon": "⌨"},
            {"name": "PowerShell", "path": "powershell.exe", "icon": "⚡"},
            {"name": "Control Panel", "path": "control.exe", "icon": "⚙"},
            {"name": "Settings", "path": "ms-settings:", "icon": "🔧"},
        ]
        
        # Define tasks
        self.tasks = [
            {
                "name": "Audio Devices",
                "key": "F1",
                "icon": "♪",
                "command": "__audio_devices__",
                "args": [],
                "description": "Manage audio output"
            },
            {
                "name": "Quick Launch",
                "key": "F2",
                "icon": "▶",
                "command": "__quick_launch__",
                "args": [],
                "description": "Launch applications"
            },
            {
                "name": "Clipboard",
                "key": "F3",
                "icon": "◫",
                "command": "__clipboard__",
                "args": [],
                "description": "Clipboard history"
            },
            {
                "name": "Network Info",
                "key": "F4",
                "icon": "◎",
                "command": "__network_info__",
                "args": [],
                "description": "Network details & speed"
            },
            {
                "name": "System Monitor",
                "key": "F5",
                "icon": "◈",
                "command": "__system_monitor__",
                "args": [],
                "description": "CPU/RAM/Disk dashboard"
            },
            {
                "name": "Process Killer",
                "key": "F6",
                "icon": "✕",
                "command": "__process_killer__",
                "args": [],
                "description": "Kill processes"
            },
            {
                "name": "Suspend Task",
                "key": "F7",
                "icon": "⏸",
                "command": "__suspend_task__",
                "args": [],
                "description": "Suspend/resume apps"
            },
            {
                "name": "Clear Console",
                "key": "F8",
                "icon": "◇",
                "command": None,
                "args": [],
                "description": "Reset terminal output"
            }
        ]
        
        self.tray_icon = None
        self.is_visible = True
        
        self.setup_scrollbar_style()
        self.setup_ui()
        self.setup_tray()
        self.bind_keys()
        self.start_animations()
        self.start_clipboard_monitor()
        self.log_startup()
    
    def setup_scrollbar_style(self):
        """Configure ttk scrollbar to match the dark theme"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure(
            "Dark.Vertical.TScrollbar",
            background=self.colors['bg_elevated'],
            troughcolor=self.colors['bg'],
            bordercolor=self.colors['bg'],
            arrowcolor=self.colors['primary_dim'],
            lightcolor=self.colors['bg'],
            darkcolor=self.colors['bg']
        )
        style.map(
            "Dark.Vertical.TScrollbar",
            background=[('active', self.colors['primary_dark']), ('pressed', self.colors['primary_dim'])],
            arrowcolor=[('active', self.colors['primary'])]
        )
    
    def get_available_font(self, size):
        import tkinter.font as tkfont
        available = set(f.lower() for f in tkfont.families())
        for font in self.hacker_fonts:
            if font.lower() in available:
                return (font, size)
        return ("Consolas", size)
    
    def setup_ui(self):
        # Use a single canvas for everything - both animation and UI
        self.bg_canvas = tk.Canvas(
            self.root, 
            bg=self.colors['bg'], 
            highlightthickness=0
        )
        self.bg_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initialize animated orb background
        self.animated_orb = AnimatedOrb(self.bg_canvas, self.colors)
        
        # All UI placed on canvas with canvas bg for transparency effect
        canvas_bg = self.colors['bg']
        
        # Header - banner  
        self.banner_label = tk.Label(
            self.root,
            text=ASCII_BANNER,
            font=self.banner_font,
            fg=self.colors['primary'],
            bg=canvas_bg,
            justify=tk.CENTER
        )
        self.banner_label.place(relx=0.5, y=15, anchor='n')
        
        # Tagline
        self.tagline_label = tk.Label(
            self.root,
            text="─── SYSTEM AUTOMATION TOOLKIT ───",
            font=self.tiny_font,
            fg=self.colors['text_dim'],
            bg=canvas_bg
        )
        self.tagline_label.place(relx=0.5, y=95, anchor='n')
        
        # Commands section header
        self.commands_header = tk.Label(
            self.root,
            text="◢ COMMANDS",
            font=self.tiny_font,
            fg=self.colors['primary_dim'],
            bg=canvas_bg
        )
        self.commands_header.place(x=20, y=130)
        
        # Task buttons - minimal transparent styling
        self.tasks_container = tk.Frame(self.root, bg=self.colors['bg'])
        self.tasks_container.place(x=20, y=155, width=240, relheight=0.55)
        
        for i, task in enumerate(self.tasks):
            self.create_task_button(task, i)
        
        # Output section header
        self.output_header = tk.Label(
            self.root,
            text="◢ OUTPUT",
            font=self.tiny_font,
            fg=self.colors['secondary'],
            bg=canvas_bg
        )
        self.output_header.place(x=280, y=130)
        
        self.cursor_label = tk.Label(
            self.root,
            text=" █",
            font=self.tiny_font,
            fg=self.colors['primary'],
            bg=canvas_bg
        )
        self.cursor_label.place(x=355, y=130)
        
        # Console - darker background with border glow effect
        console_border = tk.Frame(self.root, bg=self.colors['primary_dark'])
        console_border.place(x=278, y=153, relwidth=0.655, relheight=0.66)
        
        console_inner = tk.Frame(console_border, bg='#080808')
        console_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        self.console = tk.Text(
            console_inner,
            font=self.small_font,
            fg=self.colors['text'],
            bg='#080808',
            insertbackground=self.colors['primary'],
            selectbackground=self.colors['primary_dark'],
            selectforeground=self.colors['text'],
            border=0,
            wrap=tk.WORD,
            padx=12,
            pady=10
        )
        
        console_scrollbar = ttk.Scrollbar(
            console_inner,
            orient="vertical",
            command=self.console.yview,
            style="Dark.Vertical.TScrollbar"
        )
        self.console.configure(yscrollcommand=console_scrollbar.set)
        
        console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure text tags
        self.console.tag_configure("timestamp", foreground=self.colors['text_muted'])
        self.console.tag_configure("success", foreground=self.colors['success'])
        self.console.tag_configure("error", foreground=self.colors['error'])
        self.console.tag_configure("warn", foreground=self.colors['warning'])
        self.console.tag_configure("dim", foreground=self.colors['text_dim'])
        self.console.tag_configure("accent", foreground=self.colors['primary'])
        self.console.tag_configure("info", foreground=self.colors['secondary'])
        
        # Status bar - bottom
        self.status_indicator = tk.Label(
            self.root,
            text="●",
            font=self.tiny_font,
            fg=self.colors['primary'],
            bg=canvas_bg
        )
        self.status_indicator.place(x=20, rely=0.95, anchor='w')
        
        self.status_label = tk.Label(
            self.root,
            text=" READY",
            font=self.tiny_font,
            fg=self.colors['text_dim'],
            bg=canvas_bg
        )
        self.status_label.place(x=35, rely=0.95, anchor='w')
        
        # ESC hint
        self.esc_hint = tk.Label(
            self.root,
            text="ESC hide  |  Ctrl+NumDel toggle",
            font=self.tiny_font,
            fg=self.colors['text_muted'],
            bg=canvas_bg
        )
        self.esc_hint.place(relx=0.98, rely=0.95, anchor='e')
    
    def create_task_button(self, task, index):
        """Create a minimal transparent task button"""
        # Use Label-based button for minimal footprint
        btn_bg = self.colors['bg']
        btn_hover = self.colors['bg_hover']
        
        btn_frame = tk.Frame(self.tasks_container, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, pady=1)
        
        # Single-line compact button
        btn = tk.Label(
            btn_frame,
            text=f" {task['key']}  {task['icon']}  {task['name']}",
            font=self.small_font,
            fg=self.colors['text'],
            bg=btn_bg,
            anchor='w',
            cursor="hand2",
            padx=8,
            pady=6
        )
        btn.pack(fill=tk.X)
        
        def on_enter(e):
            btn.configure(bg=btn_hover, fg=self.colors['primary'])
        
        def on_leave(e):
            btn.configure(bg=btn_bg, fg=self.colors['text'])
        
        def on_click(e):
            self.execute_task(task)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", on_click)
    
    def setup_tray(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'vomtools.ico')
        if os.path.exists(icon_path):
            image = Image.open(icon_path)
        else:
            image = Image.new('RGB', (64, 64), color='#00ff9f')
        
        menu = pystray.Menu(
            pystray.MenuItem("Show/Hide", self.toggle_visibility, default=True),
            pystray.MenuItem("Quit", self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("VomTools", image, "VomTools", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
        keyboard.add_hotkey('ctrl+decimal', self.on_global_hotkey)
    
    def on_global_hotkey(self):
        self.root.after(0, self.toggle_visibility)
    
    def toggle_visibility(self, icon=None, item=None):
        if self.is_visible:
            self.hide_to_tray()
        else:
            self.show_from_tray()
    
    def hide_to_tray(self):
        self.is_visible = False
        self.root.withdraw()
    
    def show_from_tray(self):
        self.is_visible = True
        self.root.deiconify()
        self.root.attributes('-topmost', True)  # Ensure always on top
        self.root.lift()
        self.root.focus_force()
    
    def quit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
    
    def bind_keys(self):
        for task in self.tasks:
            self.root.bind(f"<{task['key']}>", lambda e, t=task: self.execute_task(t))
        self.root.bind("<Escape>", lambda e: self.hide_to_tray())
    
    def start_animations(self):
        """Start background animations"""
        self.scan_line_y = 0
        self.animate_cursor()
        self.animate_scanline()
    
    def start_clipboard_monitor(self):
        """Monitor clipboard for history"""
        def monitor():
            self.update_clipboard_history()
            self.root.after(1000, monitor)
        monitor()
    
    def animate_cursor(self):
        """Blinking cursor animation"""
        self.cursor_visible = not self.cursor_visible
        self.cursor_label.config(
            fg=self.colors['primary'] if self.cursor_visible else self.colors['bg']
        )
        self.root.after(530, self.animate_cursor)
    
    def animate_scanline(self):
        """Subtle scanline effect"""
        self.bg_canvas.delete("scanline")
        self.scan_line_y = (self.scan_line_y + 2) % max(1, self.root.winfo_height())
        self.bg_canvas.create_line(
            0, self.scan_line_y,
            self.root.winfo_width(), self.scan_line_y,
            fill='#1a1a1a', width=1, tags="scanline"
        )
        self.bg_canvas.tag_raise("scanline")
        self.root.after(16, self.animate_scanline)
    
    def log(self, message, tag="success"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.insert(tk.END, f"{timestamp} ", "timestamp")
        self.console.insert(tk.END, f"│ {message}\n", tag)
        self.console.see(tk.END)
    
    def log_raw(self, message, tag="dim"):
        """Log without timestamp"""
        self.console.insert(tk.END, f"       │ {message}\n", tag)
        self.console.see(tk.END)
    
    def log_startup(self):
        self.console.insert(tk.END, "\n", "dim")
        self.log("VomTools initialized", "accent")
        self.log_raw("Ready to execute commands", "dim")
        self.console.insert(tk.END, "\n", "dim")
    
    def set_status(self, text, is_error=False, is_warning=False):
        if is_error:
            color = self.colors['error']
        elif is_warning:
            color = self.colors['warning']
        else:
            color = self.colors['primary']
        
        self.status_indicator.config(fg=color)
        self.status_label.config(text=f" {text}", fg=self.colors['text_dim'])
    
    def execute_task(self, task):
        if task["command"] is None:
            self.console.delete(1.0, tk.END)
            self.log_startup()
            self.log("Console cleared", "info")
            return
        
        if task["command"] == "__audio_devices__":
            self.show_audio_devices()
            return
        
        if task["command"] == "__suspend_task__":
            self.show_suspend_task()
            return
        
        if task["command"] == "__quick_launch__":
            self.show_quick_launch()
            return
        
        if task["command"] == "__clipboard__":
            self.show_clipboard_manager()
            return
        
        if task["command"] == "__network_info__":
            self.show_network_info()
            return
        
        if task["command"] == "__system_monitor__":
            self.show_system_monitor()
            return
        
        if task["command"] == "__process_killer__":
            self.show_process_killer()
            return
        
        self.log(f"Executing: {task['name']}", "warn")
        self.set_status(f"RUNNING: {task['name']}", is_warning=True)
        
        def run():
            try:
                cmd = [task["command"]] + task["args"]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=300
                )
                self.root.after(0, lambda: self.handle_result(task, result))
            except subprocess.TimeoutExpired:
                self.root.after(0, lambda: self.log("Task timed out (300s limit)", "error"))
                self.root.after(0, lambda: self.set_status("TIMEOUT", True))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {str(e)}", "error"))
                self.root.after(0, lambda: self.set_status("ERROR", True))
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def handle_result(self, task, result):
        if result.stdout:
            for line in result.stdout.strip().split('\n')[:50]:
                self.log_raw(line, "success")
        if result.stderr:
            for line in result.stderr.strip().split('\n')[:20]:
                self.log_raw(line, "error")
        
        if result.returncode == 0:
            self.log(f"Completed: {task['name']}", "accent")
            self.set_status("READY")
        else:
            self.log(f"Failed with code: {result.returncode}", "error")
            self.set_status("FAILED", True)
    
    # ─── SUSPEND TASK MANAGEMENT ──────────────────────────────────────────
    def show_suspend_task(self):
        self.log("Scanning visible windows...", "info")
        self.set_status("SCANNING", is_warning=True)
        self.suspended_pids = getattr(self, 'suspended_pids', set())
        
        def scan():
            try:
                ps_script = '''
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;

public class WindowEnumerator {
    [DllImport("user32.dll")]
    private static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    
    [DllImport("user32.dll")]
    private static extern bool IsWindowVisible(IntPtr hWnd);
    
    [DllImport("user32.dll", SetLastError = true)]
    private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    private static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    
    [DllImport("user32.dll")]
    private static extern int GetWindowTextLength(IntPtr hWnd);
    
    private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    
    private static List<uint> processIds = new List<uint>();
    
    private static bool EnumWindowCallback(IntPtr hWnd, IntPtr lParam) {
        if (!IsWindowVisible(hWnd)) return true;
        
        int length = GetWindowTextLength(hWnd);
        if (length == 0) return true;
        
        uint processId;
        GetWindowThreadProcessId(hWnd, out processId);
        
        if (!processIds.Contains(processId)) {
            processIds.Add(processId);
        }
        return true;
    }
    
    public static uint[] GetVisibleWindowProcessIds() {
        processIds.Clear();
        EnumWindows(new EnumWindowsProc(EnumWindowCallback), IntPtr.Zero);
        return processIds.ToArray();
    }
}
"@

$procIds = [WindowEnumerator]::GetVisibleWindowProcessIds()
$results = @()
$seen = @{}

foreach ($procId in $procIds) {
    try {
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($proc -and $proc.MainWindowTitle -and -not $seen.ContainsKey($proc.Id)) {
            $seen[$proc.Id] = $true
            $results += @{
                "PID" = $proc.Id
                "Name" = $proc.ProcessName
                "Title" = $proc.MainWindowTitle
            }
        }
    } catch {}
}

$results | ConvertTo-Json -Compress
'''
                result = subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                    capture_output=True, text=True, timeout=30,
                    creationflags=SUBPROCESS_FLAGS
                )
                self.root.after(0, lambda: self.display_suspend_tasks(result.stdout, result.stderr))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
                self.root.after(0, lambda: self.set_status("ERROR", True))
        
        thread = threading.Thread(target=scan, daemon=True)
        thread.start()
    
    def display_suspend_tasks(self, json_output, stderr=""):
        self.log("Applications with windows:", "accent")
        
        if stderr:
            self.log_raw(f"Warning: {stderr[:200]}", "warn")
        
        try:
            processes = json.loads(json_output) if json_output.strip() else []
            if not isinstance(processes, list):
                processes = [processes]
            
            if not processes:
                self.log_raw("No visible windows found", "warn")
                self.set_status("NO WINDOWS", True)
                return
            
            for proc in processes:
                name = proc.get('Name', 'Unknown')
                pid = proc.get('PID', 0)
                status = "⏸ SUSPENDED" if pid in self.suspended_pids else ""
                self.log_raw(f"[{pid}] {name} {status}", "success")
            
            self.show_suspend_selector(processes)
            self.set_status("SELECT APP")
            
        except json.JSONDecodeError:
            self.log_raw("Could not parse process list", "error")
            self.set_status("PARSE ERROR", True)
    
    def center_popup(self, popup, width, height):
        """Center a popup window over the main application window"""
        popup.withdraw()
        self.root.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        x = main_x + (main_w - width) // 2
        y = main_y + (main_h - height) // 2
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.update_idletasks()
        popup.attributes('-topmost', True)
        popup.deiconify()
        popup.lift()
        popup.grab_set()
        popup.focus_force()
        popup.bind("<Escape>", lambda e: popup.destroy())
    
    def bind_mousewheel(self, canvas):
        """Bind mouse wheel scrolling to a canvas"""
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        def unbind_mousewheel(event=None):
            canvas.unbind_all("<MouseWheel>")
        canvas.bind("<Destroy>", unbind_mousewheel)
    
    def show_suspend_selector(self, processes):
        popup = tk.Toplevel(self.root)
        popup.configure(bg=self.colors['bg'])
        popup.overrideredirect(True)
        self.center_popup(popup, 550, 450)
        
        header = tk.Frame(popup, bg=self.colors['bg'])
        header.pack(fill=tk.X, padx=20, pady=(20, 15))
        
        tk.Label(
            header,
            text="◫",
            font=self.tiny_font,
            fg=self.colors['primary'],
            bg=self.colors['bg']
        ).pack(side=tk.LEFT)
        
        tk.Label(
            header,
            text=" SUSPEND / RESUME APPLICATION",
            font=self.tiny_font,
            fg=self.colors['text_dim'],
            bg=self.colors['bg']
        ).pack(side=tk.LEFT)
        
        list_frame = tk.Frame(popup, bg=self.colors['bg'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        canvas = tk.Canvas(list_frame, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview, style="Dark.Vertical.TScrollbar")
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.bind_mousewheel(canvas)
        
        for proc in processes:
            name = proc.get('Name', 'Unknown')
            title = proc.get('Title', '')
            pid = proc.get('PID', 0)
            is_suspended = pid in self.suspended_pids
            
            btn = tk.Frame(scrollable_frame, bg=self.colors['bg_elevated'], cursor="hand2")
            btn.pack(fill=tk.X, pady=2)
            
            content = tk.Frame(btn, bg=self.colors['bg_elevated'])
            content.pack(fill=tk.X, padx=12, pady=10)
            
            status_icon = tk.Label(
                content,
                text="⏸" if is_suspended else "▶",
                font=self.tiny_font,
                fg=self.colors['warning'] if is_suspended else self.colors['primary'],
                bg=self.colors['bg_elevated'],
                width=2
            )
            status_icon.pack(side=tk.LEFT)
            
            name_lbl = tk.Label(
                content,
                text=f"{name} (PID: {pid})",
                font=self.small_font,
                fg=self.colors['warning'] if is_suspended else self.colors['text'],
                bg=self.colors['bg_elevated'],
                anchor='w'
            )
            name_lbl.pack(side=tk.LEFT, padx=(10, 0))
            
            if title and len(title) < 50:
                title_lbl = tk.Label(
                    content,
                    text=f"  {title[:40]}",
                    font=self.tiny_font,
                    fg=self.colors['text_muted'],
                    bg=self.colors['bg_elevated'],
                    anchor='w'
                )
                title_lbl.pack(side=tk.LEFT, padx=(5, 0))
            else:
                title_lbl = None
            
            widgets = [btn, content, status_icon, name_lbl]
            if title_lbl:
                widgets.append(title_lbl)
            
            def on_enter(e, w=widgets):
                for widget in w:
                    widget.configure(bg=self.colors['bg_hover'])
            
            def on_leave(e, w=widgets):
                for widget in w:
                    widget.configure(bg=self.colors['bg_elevated'])
            
            def on_click(e, p=proc, pop=popup):
                self.toggle_suspend(p, pop)
            
            for w in widgets:
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.bind("<Button-1>", on_click)
        
        cancel_frame = tk.Frame(popup, bg=self.colors['bg'])
        cancel_frame.pack(fill=tk.X, padx=20, pady=15)
        
        cancel_btn = tk.Label(
            cancel_frame,
            text="Cancel",
            font=self.tiny_font,
            fg=self.colors['text_muted'],
            bg=self.colors['bg'],
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.RIGHT)
        cancel_btn.bind("<Button-1>", lambda e: popup.destroy())
        cancel_btn.bind("<Enter>", lambda e: cancel_btn.configure(fg=self.colors['error']))
        cancel_btn.bind("<Leave>", lambda e: cancel_btn.configure(fg=self.colors['text_muted']))
    
    def toggle_suspend(self, proc, popup):
        popup.destroy()
        
        pid = proc.get('PID', 0)
        name = proc.get('Name', 'Unknown')
        is_suspended = pid in self.suspended_pids
        
        action = "Resuming" if is_suspended else "Suspending"
        self.log(f"{action}: {name} (PID: {pid})", "warn")
        self.set_status(f"{action.upper()}", is_warning=True)
        
        def do_toggle():
            try:
                if is_suspended:
                    ps_script = f'''
$proc = Get-Process -Id {pid} -ErrorAction Stop
$handle = $proc.Handle
$result = [System.Diagnostics.Process]::GetProcessById({pid})
foreach ($thread in $result.Threads) {{
    $tHandle = [IntPtr]::Zero
    try {{
        Add-Type @"
using System;
using System.Runtime.InteropServices;
public class ThreadControl {{
    [DllImport("kernel32.dll")]
    public static extern IntPtr OpenThread(int dwDesiredAccess, bool bInheritHandle, int dwThreadId);
    [DllImport("kernel32.dll")]
    public static extern uint ResumeThread(IntPtr hThread);
    [DllImport("kernel32.dll")]
    public static extern bool CloseHandle(IntPtr hObject);
}}
"@ -ErrorAction SilentlyContinue
        $tHandle = [ThreadControl]::OpenThread(0x0002, $false, $thread.Id)
        if ($tHandle -ne [IntPtr]::Zero) {{
            [ThreadControl]::ResumeThread($tHandle) | Out-Null
            [ThreadControl]::CloseHandle($tHandle) | Out-Null
        }}
    }} catch {{}}
}}
Write-Output "SUCCESS"
'''
                else:
                    ps_script = f'''
$proc = Get-Process -Id {pid} -ErrorAction Stop
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class ThreadControl {{
    [DllImport("kernel32.dll")]
    public static extern IntPtr OpenThread(int dwDesiredAccess, bool bInheritHandle, int dwThreadId);
    [DllImport("kernel32.dll")]
    public static extern uint SuspendThread(IntPtr hThread);
    [DllImport("kernel32.dll")]
    public static extern bool CloseHandle(IntPtr hObject);
}}
"@ -ErrorAction SilentlyContinue
foreach ($thread in $proc.Threads) {{
    $tHandle = [ThreadControl]::OpenThread(0x0002, $false, $thread.Id)
    if ($tHandle -ne [IntPtr]::Zero) {{
        [ThreadControl]::SuspendThread($tHandle) | Out-Null
        [ThreadControl]::CloseHandle($tHandle) | Out-Null
    }}
}}
Write-Output "SUCCESS"
'''
                result = subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                    capture_output=True, text=True, timeout=30,
                    creationflags=SUBPROCESS_FLAGS
                )
                self.root.after(0, lambda: self.handle_suspend_result(pid, name, is_suspended, result))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
                self.root.after(0, lambda: self.set_status("ERROR", True))
        
        thread = threading.Thread(target=do_toggle, daemon=True)
        thread.start()
    
    def handle_suspend_result(self, pid, name, was_suspended, result):
        output = result.stdout.strip() if result.stdout else ""
        
        if "SUCCESS" in output:
            if was_suspended:
                self.suspended_pids.discard(pid)
                self.log(f"Resumed: {name}", "accent")
            else:
                self.suspended_pids.add(pid)
                self.log(f"Suspended: {name}", "accent")
            self.set_status("READY")
        else:
            self.log(f"Failed to toggle suspend state", "error")
            if result.stderr:
                self.log_raw(result.stderr.strip()[:100], "error")
            self.set_status("FAILED", True)

    # ─── AUDIO DEVICE MANAGEMENT ──────────────────────────────────────────
    def show_audio_devices(self):
        self.log("Scanning audio devices...", "info")
        self.set_status("SCANNING", is_warning=True)
        
        def scan():
            try:
                ps_script = '''
$results = @()
$renderKey = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\MMDevices\\Audio\\Render"

if (Test-Path $renderKey) {
    foreach ($device in Get-ChildItem $renderKey) {
        $deviceGuid = $device.PSChildName
        $deviceKey = $device.PSPath
        
        $devProps = Get-ItemProperty -Path $deviceKey -ErrorAction SilentlyContinue
        $state = $devProps.DeviceState
        
        if ($state -ne 1) { continue }
        
        $propsKey = Join-Path $deviceKey "Properties"
        if (-not (Test-Path $propsKey)) { continue }
        
        $props = Get-ItemProperty -Path $propsKey -ErrorAction SilentlyContinue
        
        $shortName = $null
        $deviceDesc = $null
        foreach ($prop in $props.PSObject.Properties) {
            if ($prop.Name -eq "{a45c254e-df1c-4efd-8020-67d146a850e0},2") {
                $shortName = $prop.Value
            }
            if ($prop.Name -eq "{b3f8fa53-0004-438e-9003-51a46e139bfc},6") {
                $deviceDesc = $prop.Value
            }
        }
        $friendlyName = if ($shortName -and $deviceDesc) { "$shortName ($deviceDesc)" } elseif ($shortName) { $shortName } else { $deviceDesc }
        
        if ($friendlyName) {
            $fullId = "{0.0.0.00000000}." + $deviceGuid
            $results += @{
                "ID" = $fullId
                "Name" = $friendlyName
            }
        }
    }
}

$results | ConvertTo-Json -Compress
'''
                result = subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                    capture_output=True, text=True, timeout=30,
                    creationflags=SUBPROCESS_FLAGS
                )
                self.root.after(0, lambda: self.display_audio_devices(result.stdout, result.stderr))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
                self.root.after(0, lambda: self.set_status("ERROR", True))
        
        thread = threading.Thread(target=scan, daemon=True)
        thread.start()
    
    def display_audio_devices(self, json_output, stderr=""):
        import json
        
        self.log("Audio playback devices:", "accent")
        
        if stderr:
            self.log_raw(f"Warning: {stderr[:200]}", "warn")
        
        try:
            devices = json.loads(json_output) if json_output.strip() else []
            if not isinstance(devices, list):
                devices = [devices]
            
            self.audio_devices = devices
            
            if not devices:
                self.log_raw("No devices found", "warn")
                self.set_status("NO DEVICES", True)
                return
            
            for i, dev in enumerate(devices):
                name = dev.get('Name', 'Unknown')
                self.log_raw(f"[{i+1}] {name}", "success")
            
            self.show_device_selector(devices)
            self.set_status("SELECT DEVICE")
            
        except json.JSONDecodeError:
            self.log_raw("Could not parse device list", "error")
            self.set_status("PARSE ERROR", True)
    
    def show_device_selector(self, devices):
        """Modern device selector popup"""
        popup = tk.Toplevel(self.root)
        popup.configure(bg=self.colors['bg'])
        popup.overrideredirect(True)
        self.center_popup(popup, 450, 380)
        
        header = tk.Frame(popup, bg=self.colors['bg'])
        header.pack(fill=tk.X, padx=20, pady=(20, 15))
        
        tk.Label(
            header,
            text="◢",
            font=self.tiny_font,
            fg=self.colors['primary'],
            bg=self.colors['bg']
        ).pack(side=tk.LEFT)
        
        tk.Label(
            header,
            text=" SELECT AUDIO OUTPUT",
            font=self.tiny_font,
            fg=self.colors['text_dim'],
            bg=self.colors['bg']
        ).pack(side=tk.LEFT)
        
        # Role selector
        role_frame = tk.Frame(popup, bg=self.colors['bg'])
        role_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.selected_role = tk.IntVar(value=1)
        roles = [("Multimedia", 1), ("Console", 0), ("Comms", 2)]
        
        for role_name, role_val in roles:
            rb = tk.Radiobutton(
                role_frame,
                text=role_name,
                variable=self.selected_role,
                value=role_val,
                font=self.tiny_font,
                fg=self.colors['text'],
                bg=self.colors['bg'],
                activeforeground=self.colors['primary'],
                activebackground=self.colors['bg'],
                selectcolor=self.colors['bg_elevated'],
                cursor="hand2",
                highlightthickness=0
            )
            rb.pack(side=tk.LEFT, padx=(0, 15))
        
        # Devices list
        devices_frame = tk.Frame(popup, bg=self.colors['bg'])
        devices_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        for i, dev in enumerate(devices):
            name = dev.get('Name', 'Unknown')
            
            btn = tk.Frame(devices_frame, bg=self.colors['bg_elevated'], cursor="hand2")
            btn.pack(fill=tk.X, pady=2)
            
            content = tk.Frame(btn, bg=self.colors['bg_elevated'])
            content.pack(fill=tk.X, padx=12, pady=10)
            
            num = tk.Label(
                content,
                text=f"{i+1}",
                font=self.tiny_font,
                fg=self.colors['primary'],
                bg=self.colors['bg_elevated'],
                width=2
            )
            num.pack(side=tk.LEFT)
            
            name_lbl = tk.Label(
                content,
                text=name,
                font=self.small_font,
                fg=self.colors['text'],
                bg=self.colors['bg_elevated'],
                anchor='w'
            )
            name_lbl.pack(side=tk.LEFT, padx=(10, 0))
            
            widgets = [btn, content, num, name_lbl]
            
            def on_enter(e, w=widgets):
                for widget in w:
                    widget.configure(bg=self.colors['bg_hover'])
            
            def on_leave(e, w=widgets):
                for widget in w:
                    widget.configure(bg=self.colors['bg_elevated'])
            
            def on_click(e, d=dev, p=popup):
                self.set_default_audio(d, p, self.selected_role.get())
            
            for w in widgets:
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.bind("<Button-1>", on_click)
        
        # Cancel button
        cancel_frame = tk.Frame(popup, bg=self.colors['bg'])
        cancel_frame.pack(fill=tk.X, padx=20, pady=15)
        
        cancel_btn = tk.Label(
            cancel_frame,
            text="Cancel",
            font=self.tiny_font,
            fg=self.colors['text_muted'],
            bg=self.colors['bg'],
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.RIGHT)
        cancel_btn.bind("<Button-1>", lambda e: popup.destroy())
        cancel_btn.bind("<Enter>", lambda e: cancel_btn.configure(fg=self.colors['error']))
        cancel_btn.bind("<Leave>", lambda e: cancel_btn.configure(fg=self.colors['text_muted']))
    
    def set_default_audio(self, device, popup, role=1):
        popup.destroy()
        
        name = device.get('Name', 'Unknown')
        device_id = device.get('ID', '')
        role_names = {0: "Console", 1: "Multimedia", 2: "Communications"}
        role_name = role_names.get(role, "Unknown")
        
        self.log(f"Setting {role_name}: {name}", "warn")
        self.set_status(f"SETTING DEVICE", is_warning=True)
        
        def set_device():
            try:
                ps_script = f'''
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

[ComImport, Guid("870AF99C-171D-4F9E-AF0D-E63DF40C2BC9")]
class PolicyConfigClient {{}}

[Guid("F8679F50-850A-41CF-9C72-430F290290C8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPolicyConfig {{
    void Reserved1();
    void Reserved2(); 
    void Reserved3();
    void Reserved4();
    void Reserved5();
    void Reserved6();
    void Reserved7();
    void Reserved8();
    void Reserved9();
    void Reserved10();
    [PreserveSig]
    int SetDefaultEndpoint([MarshalAs(UnmanagedType.LPWStr)] string deviceId, int role);
}}

public class AudioSwitcher {{
    public static int SetDefaultDevice(string deviceId, int role) {{
        try {{
            var policyConfig = new PolicyConfigClient();
            var config = (IPolicyConfig)policyConfig;
            int hr = config.SetDefaultEndpoint(deviceId, role);
            Marshal.ReleaseComObject(policyConfig);
            return hr;
        }} catch (Exception ex) {{
            Console.Error.WriteLine(ex.Message);
            return -1;
        }}
    }}
}}
"@

$deviceId = "{device_id}"
$role = {role}
$result = [AudioSwitcher]::SetDefaultDevice($deviceId, $role)
if ($result -eq 0) {{
    Write-Output "SUCCESS"
}} else {{
    Write-Output "ERROR:$result"
}}
'''
                result = subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                    capture_output=True, text=True, timeout=30,
                    creationflags=SUBPROCESS_FLAGS
                )
                self.root.after(0, lambda: self.handle_audio_set_result(name, result))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
                self.root.after(0, lambda: self.set_status("ERROR", True))
        
        thread = threading.Thread(target=set_device, daemon=True)
        thread.start()
    
    def handle_audio_set_result(self, device_name, result):
        output = result.stdout.strip() if result.stdout else ""
        
        if "SUCCESS" in output:
            self.log(f"Audio set: {device_name}", "accent")
            self.set_status("READY")
        else:
            self.log(f"Failed to set device", "error")
            if result.stderr:
                self.log_raw(result.stderr.strip()[:100], "error")
            self.set_status("FAILED", True)

    # ─── QUICK LAUNCHER ────────────────────────────────────────────────────
    def show_quick_launch(self):
        self.log("Quick Launcher", "accent")
        self.set_status("SELECT APP")
        
        popup = tk.Toplevel(self.root)
        popup.configure(bg=self.colors['bg'])
        popup.overrideredirect(True)
        self.center_popup(popup, 400, 420)
        
        header = tk.Frame(popup, bg=self.colors['bg'])
        header.pack(fill=tk.X, padx=20, pady=(20, 15))
        
        tk.Label(header, text="▶", font=self.tiny_font, fg=self.colors['primary'], bg=self.colors['bg']).pack(side=tk.LEFT)
        tk.Label(header, text=" QUICK LAUNCHER", font=self.tiny_font, fg=self.colors['text_dim'], bg=self.colors['bg']).pack(side=tk.LEFT)
        
        list_frame = tk.Frame(popup, bg=self.colors['bg'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        for app in self.quick_launch_apps:
            btn = tk.Frame(list_frame, bg=self.colors['bg_elevated'], cursor="hand2")
            btn.pack(fill=tk.X, pady=2)
            
            content = tk.Frame(btn, bg=self.colors['bg_elevated'])
            content.pack(fill=tk.X, padx=12, pady=10)
            
            tk.Label(content, text=app['icon'], font=self.small_font, fg=self.colors['primary'], bg=self.colors['bg_elevated'], width=3).pack(side=tk.LEFT)
            tk.Label(content, text=app['name'], font=self.small_font, fg=self.colors['text'], bg=self.colors['bg_elevated'], anchor='w').pack(side=tk.LEFT, padx=(10, 0))
            
            widgets = [btn, content]
            
            def on_enter(e, w=widgets):
                for widget in w:
                    try: widget.configure(bg=self.colors['bg_hover'])
                    except: pass
            
            def on_leave(e, w=widgets):
                for widget in w:
                    try: widget.configure(bg=self.colors['bg_elevated'])
                    except: pass
            
            def on_click(e, a=app, p=popup):
                self.launch_app(a, p)
            
            for w in [btn, content]:
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.bind("<Button-1>", on_click)
        
        cancel_frame = tk.Frame(popup, bg=self.colors['bg'])
        cancel_frame.pack(fill=tk.X, padx=20, pady=15)
        
        cancel_btn = tk.Label(cancel_frame, text="Cancel", font=self.tiny_font, fg=self.colors['text_muted'], bg=self.colors['bg'], cursor="hand2")
        cancel_btn.pack(side=tk.RIGHT)
        cancel_btn.bind("<Button-1>", lambda e: popup.destroy())
        cancel_btn.bind("<Enter>", lambda e: cancel_btn.configure(fg=self.colors['error']))
        cancel_btn.bind("<Leave>", lambda e: cancel_btn.configure(fg=self.colors['text_muted']))
    
    def launch_app(self, app, popup):
        popup.destroy()
        self.log(f"Launching: {app['name']}", "warn")
        self.set_status("LAUNCHING", is_warning=True)
        
        def run():
            try:
                if app['path'].startswith('ms-'):
                    os.startfile(app['path'])
                else:
                    subprocess.Popen(app['path'], creationflags=SUBPROCESS_FLAGS)
                self.root.after(0, lambda: self.log(f"Launched: {app['name']}", "accent"))
                self.root.after(0, lambda: self.set_status("READY"))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
                self.root.after(0, lambda: self.set_status("FAILED", True))
        
        threading.Thread(target=run, daemon=True).start()

    # ─── CLIPBOARD MANAGER ─────────────────────────────────────────────────
    def show_clipboard_manager(self):
        self.log("Clipboard Manager", "accent")
        self.update_clipboard_history()
        self.set_status("SELECT ITEM")
        
        popup = tk.Toplevel(self.root)
        popup.configure(bg=self.colors['bg'])
        popup.overrideredirect(True)
        self.center_popup(popup, 500, 450)
        
        header = tk.Frame(popup, bg=self.colors['bg'])
        header.pack(fill=tk.X, padx=20, pady=(20, 15))
        
        tk.Label(header, text="◫", font=self.tiny_font, fg=self.colors['primary'], bg=self.colors['bg']).pack(side=tk.LEFT)
        tk.Label(header, text=" CLIPBOARD HISTORY", font=self.tiny_font, fg=self.colors['text_dim'], bg=self.colors['bg']).pack(side=tk.LEFT)
        
        list_frame = tk.Frame(popup, bg=self.colors['bg'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        canvas = tk.Canvas(list_frame, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview, style="Dark.Vertical.TScrollbar")
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=450)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.bind_mousewheel(canvas)
        
        if not self.clipboard_history:
            tk.Label(scrollable_frame, text="No clipboard history", font=self.small_font, fg=self.colors['text_muted'], bg=self.colors['bg']).pack(pady=20)
        else:
            for i, item in enumerate(self.clipboard_history[:20]):
                preview = item[:60] + "..." if len(item) > 60 else item
                preview = preview.replace('\n', ' ').replace('\r', '')
                
                btn = tk.Frame(scrollable_frame, bg=self.colors['bg_elevated'], cursor="hand2")
                btn.pack(fill=tk.X, pady=2)
                
                content = tk.Frame(btn, bg=self.colors['bg_elevated'])
                content.pack(fill=tk.X, padx=12, pady=8)
                
                num_lbl = tk.Label(content, text=f"{i+1}", font=self.tiny_font, fg=self.colors['primary'], bg=self.colors['bg_elevated'], width=2)
                num_lbl.pack(side=tk.LEFT)
                
                text_lbl = tk.Label(content, text=preview, font=self.small_font, fg=self.colors['text'], bg=self.colors['bg_elevated'], anchor='w')
                text_lbl.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
                
                widgets = [btn, content, num_lbl, text_lbl]
                
                def on_enter(e, w=widgets):
                    for widget in w:
                        widget.configure(bg=self.colors['bg_hover'])
                
                def on_leave(e, w=widgets):
                    for widget in w:
                        widget.configure(bg=self.colors['bg_elevated'])
                
                def on_click(e, text=item, p=popup):
                    self.paste_from_history(text, p)
                
                for w in widgets:
                    w.bind("<Enter>", on_enter)
                    w.bind("<Leave>", on_leave)
                    w.bind("<Button-1>", on_click)
        
        btn_frame = tk.Frame(popup, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, padx=20, pady=15)
        
        clear_btn = tk.Label(btn_frame, text="Clear All", font=self.tiny_font, fg=self.colors['error'], bg=self.colors['bg'], cursor="hand2")
        clear_btn.pack(side=tk.LEFT)
        clear_btn.bind("<Button-1>", lambda e: self.clear_clipboard_history(popup))
        
        cancel_btn = tk.Label(btn_frame, text="Close", font=self.tiny_font, fg=self.colors['text_muted'], bg=self.colors['bg'], cursor="hand2")
        cancel_btn.pack(side=tk.RIGHT)
        cancel_btn.bind("<Button-1>", lambda e: popup.destroy())
    
    def update_clipboard_history(self):
        try:
            current = self.root.clipboard_get()
            if current and current != self.last_clipboard:
                self.last_clipboard = current
                if current not in self.clipboard_history:
                    self.clipboard_history.insert(0, current)
                    if len(self.clipboard_history) > 50:
                        self.clipboard_history = self.clipboard_history[:50]
        except:
            pass
    
    def paste_from_history(self, text, popup):
        popup.destroy()
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.log(f"Copied: {text[:40]}...", "accent")
        self.set_status("COPIED")
    
    def clear_clipboard_history(self, popup):
        self.clipboard_history = []
        popup.destroy()
        self.log("Clipboard history cleared", "info")
        self.set_status("READY")

    # ─── NETWORK INFO ──────────────────────────────────────────────────────
    def show_network_info(self):
        self.log("Gathering network info...", "info")
        self.set_status("SCANNING", is_warning=True)
        
        def scan():
            try:
                ps_script = '''
$results = @{}

# Get network adapters
$adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Select-Object Name, InterfaceDescription, MacAddress, LinkSpeed

# Get IP configuration
$ipConfigs = Get-NetIPAddress | Where-Object { $_.AddressFamily -eq "IPv4" -and $_.IPAddress -ne "127.0.0.1" }

# Get default gateway
$gateway = (Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue | Select-Object -First 1).NextHop

# Get DNS servers
$dns = (Get-DnsClientServerAddress -AddressFamily IPv4 | Where-Object { $_.ServerAddresses } | Select-Object -First 1).ServerAddresses -join ", "

# Get public IP
try {
    $publicIP = (Invoke-RestMethod -Uri "https://api.ipify.org?format=json" -TimeoutSec 5).ip
} catch {
    $publicIP = "Unable to fetch"
}

# Network stats
$stats = Get-NetAdapterStatistics | Select-Object -First 1

$results = @{
    "Adapters" = @($adapters | ForEach-Object { @{ "Name" = $_.Name; "Desc" = $_.InterfaceDescription; "MAC" = $_.MacAddress; "Speed" = $_.LinkSpeed } })
    "IPs" = @($ipConfigs | ForEach-Object { @{ "IP" = $_.IPAddress; "Prefix" = $_.PrefixLength; "Interface" = $_.InterfaceAlias } })
    "Gateway" = $gateway
    "DNS" = $dns
    "PublicIP" = $publicIP
    "BytesSent" = if ($stats) { $stats.SentBytes } else { 0 }
    "BytesRecv" = if ($stats) { $stats.ReceivedBytes } else { 0 }
}

$results | ConvertTo-Json -Depth 3 -Compress
'''
                result = subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                    capture_output=True, text=True, timeout=30,
                    creationflags=SUBPROCESS_FLAGS
                )
                self.root.after(0, lambda: self.display_network_info(result.stdout, result.stderr))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
                self.root.after(0, lambda: self.set_status("ERROR", True))
        
        threading.Thread(target=scan, daemon=True).start()
    
    def display_network_info(self, json_output, stderr=""):
        try:
            data = json.loads(json_output) if json_output.strip() else {}
            
            self.log("Network Information:", "accent")
            
            # Public IP
            public_ip = data.get('PublicIP', 'N/A')
            self.log_raw(f"Public IP: {public_ip}", "success")
            
            # Gateway
            gateway = data.get('Gateway', 'N/A')
            self.log_raw(f"Gateway: {gateway}", "success")
            
            # DNS
            dns = data.get('DNS', 'N/A')
            self.log_raw(f"DNS: {dns}", "success")
            
            # Local IPs
            ips = data.get('IPs', [])
            for ip_info in ips:
                self.log_raw(f"Local IP: {ip_info.get('IP', 'N/A')}/{ip_info.get('Prefix', '')} ({ip_info.get('Interface', '')})", "info")
            
            # Adapters
            adapters = data.get('Adapters', [])
            for adapter in adapters:
                self.log_raw(f"Adapter: {adapter.get('Name', 'N/A')} @ {adapter.get('Speed', 'N/A')}", "dim")
            
            # Traffic stats
            sent = data.get('BytesSent', 0)
            recv = data.get('BytesRecv', 0)
            sent_mb = sent / (1024 * 1024)
            recv_mb = recv / (1024 * 1024)
            self.log_raw(f"Traffic: ↑{sent_mb:.1f}MB ↓{recv_mb:.1f}MB", "warn")
            
            self.set_status("READY")
            
        except json.JSONDecodeError:
            self.log_raw("Could not parse network info", "error")
            self.set_status("PARSE ERROR", True)

    # ─── SYSTEM MONITOR (htop-style) ───────────────────────────────────────
    def show_system_monitor(self):
        self.log("System Monitor", "accent")
        self.set_status("MONITORING")
        
        popup = tk.Toplevel(self.root)
        popup.configure(bg=self.colors['bg'])
        popup.overrideredirect(True)
        self.center_popup(popup, 600, 500)
        
        self.monitor_popup = popup
        self.monitor_running = True
        
        header = tk.Frame(popup, bg=self.colors['bg'])
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        tk.Label(header, text="◈", font=self.tiny_font, fg=self.colors['primary'], bg=self.colors['bg']).pack(side=tk.LEFT)
        tk.Label(header, text=" SYSTEM MONITOR", font=self.tiny_font, fg=self.colors['text_dim'], bg=self.colors['bg']).pack(side=tk.LEFT)
        
        # CPU Section
        cpu_frame = tk.Frame(popup, bg=self.colors['bg'])
        cpu_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(cpu_frame, text="CPU", font=self.small_font, fg=self.colors['secondary'], bg=self.colors['bg'], width=6, anchor='w').pack(side=tk.LEFT)
        
        self.cpu_bar_canvas = tk.Canvas(cpu_frame, height=20, bg=self.colors['bg'], highlightthickness=0)
        self.cpu_bar_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        self.cpu_label = tk.Label(cpu_frame, text="0%", font=self.small_font, fg=self.colors['primary'], bg=self.colors['bg'], width=6)
        self.cpu_label.pack(side=tk.RIGHT)
        
        # RAM Section
        ram_frame = tk.Frame(popup, bg=self.colors['bg'])
        ram_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(ram_frame, text="RAM", font=self.small_font, fg=self.colors['secondary'], bg=self.colors['bg'], width=6, anchor='w').pack(side=tk.LEFT)
        
        self.ram_bar_canvas = tk.Canvas(ram_frame, height=20, bg=self.colors['bg'], highlightthickness=0)
        self.ram_bar_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        self.ram_label = tk.Label(ram_frame, text="0%", font=self.small_font, fg=self.colors['primary'], bg=self.colors['bg'], width=6)
        self.ram_label.pack(side=tk.RIGHT)
        
        # Disk Section
        disk_frame = tk.Frame(popup, bg=self.colors['bg'])
        disk_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(disk_frame, text="DISK", font=self.small_font, fg=self.colors['secondary'], bg=self.colors['bg'], width=6, anchor='w').pack(side=tk.LEFT)
        
        self.disk_bar_canvas = tk.Canvas(disk_frame, height=20, bg=self.colors['bg'], highlightthickness=0)
        self.disk_bar_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        self.disk_label = tk.Label(disk_frame, text="0%", font=self.small_font, fg=self.colors['primary'], bg=self.colors['bg'], width=6)
        self.disk_label.pack(side=tk.RIGHT)
        
        # Separator
        tk.Frame(popup, bg=self.colors['border'], height=1).pack(fill=tk.X, padx=20, pady=15)
        
        # Top Processes
        proc_header = tk.Frame(popup, bg=self.colors['bg'])
        proc_header.pack(fill=tk.X, padx=20)
        
        tk.Label(proc_header, text="TOP PROCESSES", font=self.tiny_font, fg=self.colors['text_dim'], bg=self.colors['bg']).pack(side=tk.LEFT)
        
        self.proc_frame = tk.Frame(popup, bg=self.colors['bg'])
        self.proc_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Process list header
        header_row = tk.Frame(self.proc_frame, bg=self.colors['bg'])
        header_row.pack(fill=tk.X)
        tk.Label(header_row, text="PID", font=self.tiny_font, fg=self.colors['text_muted'], bg=self.colors['bg'], width=8, anchor='w').pack(side=tk.LEFT)
        tk.Label(header_row, text="NAME", font=self.tiny_font, fg=self.colors['text_muted'], bg=self.colors['bg'], width=20, anchor='w').pack(side=tk.LEFT)
        tk.Label(header_row, text="CPU%", font=self.tiny_font, fg=self.colors['text_muted'], bg=self.colors['bg'], width=8, anchor='e').pack(side=tk.LEFT)
        tk.Label(header_row, text="MEM%", font=self.tiny_font, fg=self.colors['text_muted'], bg=self.colors['bg'], width=8, anchor='e').pack(side=tk.LEFT)
        
        self.proc_rows = []
        for i in range(8):
            row = tk.Frame(self.proc_frame, bg=self.colors['bg'])
            row.pack(fill=tk.X, pady=1)
            pid_lbl = tk.Label(row, text="", font=self.small_font, fg=self.colors['text_dim'], bg=self.colors['bg'], width=8, anchor='w')
            pid_lbl.pack(side=tk.LEFT)
            name_lbl = tk.Label(row, text="", font=self.small_font, fg=self.colors['text'], bg=self.colors['bg'], width=20, anchor='w')
            name_lbl.pack(side=tk.LEFT)
            cpu_lbl = tk.Label(row, text="", font=self.small_font, fg=self.colors['warning'], bg=self.colors['bg'], width=8, anchor='e')
            cpu_lbl.pack(side=tk.LEFT)
            mem_lbl = tk.Label(row, text="", font=self.small_font, fg=self.colors['secondary'], bg=self.colors['bg'], width=8, anchor='e')
            mem_lbl.pack(side=tk.LEFT)
            self.proc_rows.append((pid_lbl, name_lbl, cpu_lbl, mem_lbl))
        
        # Close button
        btn_frame = tk.Frame(popup, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, padx=20, pady=15)
        
        close_btn = tk.Label(btn_frame, text="Close", font=self.tiny_font, fg=self.colors['text_muted'], bg=self.colors['bg'], cursor="hand2")
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: self.stop_monitor(popup))
        close_btn.bind("<Enter>", lambda e: close_btn.configure(fg=self.colors['primary']))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(fg=self.colors['text_muted']))
        
        popup.protocol("WM_DELETE_WINDOW", lambda: self.stop_monitor(popup))
        
        self.update_system_monitor()
    
    def stop_monitor(self, popup):
        self.monitor_running = False
        popup.destroy()
        self.set_status("READY")
    
    def draw_bar(self, canvas, percent, color):
        canvas.delete("all")
        canvas.update_idletasks()
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        # Background
        canvas.create_rectangle(0, 0, width, height, fill=self.colors['bg_elevated'], outline="")
        
        # Filled bar
        fill_width = int((percent / 100) * width)
        if fill_width > 0:
            # Gradient effect with blocks
            block_width = 4
            for i in range(0, fill_width, block_width + 1):
                intensity = 0.5 + (i / width) * 0.5
                canvas.create_rectangle(i, 2, min(i + block_width, fill_width), height - 2, fill=color, outline="")
    
    def update_system_monitor(self):
        if not self.monitor_running:
            return
        
        def get_stats():
            try:
                ps_script = '''
$cpu = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
$os = Get-CimInstance Win32_OperatingSystem
$ramUsed = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 1)
$ramTotal = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
$ramUsedGB = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / 1MB, 1)

$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
$diskUsed = [math]::Round((($disk.Size - $disk.FreeSpace) / $disk.Size) * 100, 1)

$procs = Get-Process | Sort-Object CPU -Descending | Select-Object -First 8 Id, ProcessName, @{N='CPU';E={[math]::Round($_.CPU,1)}}, @{N='Mem';E={[math]::Round($_.WorkingSet64/1MB,1)}}

@{
    "CPU" = $cpu
    "RAM" = $ramUsed
    "RAMUsed" = $ramUsedGB
    "RAMTotal" = $ramTotal
    "Disk" = $diskUsed
    "Procs" = @($procs | ForEach-Object { @{ "PID" = $_.Id; "Name" = $_.ProcessName; "CPU" = $_.CPU; "Mem" = $_.Mem } })
} | ConvertTo-Json -Depth 3 -Compress
'''
                result = subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                    capture_output=True, text=True, timeout=10,
                    creationflags=SUBPROCESS_FLAGS
                )
                if result.stdout:
                    self.root.after(0, lambda: self.update_monitor_display(result.stdout))
            except:
                pass
        
        threading.Thread(target=get_stats, daemon=True).start()
        
        if self.monitor_running:
            self.root.after(2000, self.update_system_monitor)
    
    def update_monitor_display(self, json_output):
        if not self.monitor_running:
            return
        
        try:
            data = json.loads(json_output)
            
            cpu = data.get('CPU', 0) or 0
            ram = data.get('RAM', 0) or 0
            disk = data.get('Disk', 0) or 0
            ram_used = data.get('RAMUsed', 0)
            ram_total = data.get('RAMTotal', 0)
            
            # Update bars
            self.draw_bar(self.cpu_bar_canvas, cpu, self.colors['primary'])
            self.draw_bar(self.ram_bar_canvas, ram, self.colors['secondary'])
            self.draw_bar(self.disk_bar_canvas, disk, self.colors['warning'])
            
            # Update labels
            self.cpu_label.config(text=f"{cpu:.0f}%")
            self.ram_label.config(text=f"{ram:.0f}%")
            self.disk_label.config(text=f"{disk:.0f}%")
            
            # Update processes
            procs = data.get('Procs', [])
            for i, (pid_lbl, name_lbl, cpu_lbl, mem_lbl) in enumerate(self.proc_rows):
                if i < len(procs):
                    p = procs[i]
                    pid_lbl.config(text=str(p.get('PID', '')))
                    name_lbl.config(text=p.get('Name', '')[:18])
                    cpu_lbl.config(text=f"{p.get('CPU', 0):.1f}")
                    mem_lbl.config(text=f"{p.get('Mem', 0):.0f}MB")
                else:
                    pid_lbl.config(text="")
                    name_lbl.config(text="")
                    cpu_lbl.config(text="")
                    mem_lbl.config(text="")
        except:
            pass

    # ─── PROCESS KILLER ────────────────────────────────────────────────────
    def show_process_killer(self):
        self.log("Scanning processes...", "info")
        self.set_status("SCANNING", is_warning=True)
        
        def scan():
            try:
                ps_script = '''
$procs = Get-Process | Where-Object { $_.MainWindowTitle -ne "" -or $_.CPU -gt 10 } | 
    Sort-Object CPU -Descending | 
    Select-Object -First 30 Id, ProcessName, @{N='CPU';E={[math]::Round($_.CPU,1)}}, @{N='Mem';E={[math]::Round($_.WorkingSet64/1MB,0)}}, MainWindowTitle

$procs | ForEach-Object {
    @{
        "PID" = $_.Id
        "Name" = $_.ProcessName
        "CPU" = $_.CPU
        "Mem" = $_.Mem
        "Title" = if ($_.MainWindowTitle) { $_.MainWindowTitle.Substring(0, [Math]::Min(40, $_.MainWindowTitle.Length)) } else { "" }
    }
} | ConvertTo-Json -Compress
'''
                result = subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                    capture_output=True, text=True, timeout=30,
                    creationflags=SUBPROCESS_FLAGS
                )
                self.root.after(0, lambda: self.display_process_killer(result.stdout))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
                self.root.after(0, lambda: self.set_status("ERROR", True))
        
        threading.Thread(target=scan, daemon=True).start()
    
    def display_process_killer(self, json_output):
        try:
            procs = json.loads(json_output) if json_output.strip() else []
            if not isinstance(procs, list):
                procs = [procs]
            
            if not procs:
                self.log_raw("No killable processes found", "warn")
                self.set_status("NO PROCESSES", True)
                return
            
            self.show_process_killer_popup(procs)
            self.set_status("SELECT PROCESS")
            
        except json.JSONDecodeError:
            self.log_raw("Could not parse process list", "error")
            self.set_status("PARSE ERROR", True)
    
    def show_process_killer_popup(self, processes):
        popup = tk.Toplevel(self.root)
        popup.configure(bg=self.colors['bg'])
        popup.overrideredirect(True)
        self.center_popup(popup, 550, 480)
        
        header = tk.Frame(popup, bg=self.colors['bg'])
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        tk.Label(header, text="✕", font=self.tiny_font, fg=self.colors['error'], bg=self.colors['bg']).pack(side=tk.LEFT)
        tk.Label(header, text=" PROCESS KILLER", font=self.tiny_font, fg=self.colors['text_dim'], bg=self.colors['bg']).pack(side=tk.LEFT)
        
        tk.Label(header, text="⚠ Click to kill", font=self.tiny_font, fg=self.colors['warning'], bg=self.colors['bg']).pack(side=tk.RIGHT)
        
        list_frame = tk.Frame(popup, bg=self.colors['bg'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        canvas = tk.Canvas(list_frame, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview, style="Dark.Vertical.TScrollbar")
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=500)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.bind_mousewheel(canvas)
        
        for proc in processes:
            pid = proc.get('PID', 0)
            name = proc.get('Name', 'Unknown')
            cpu = proc.get('CPU', 0)
            mem = proc.get('Mem', 0)
            title = proc.get('Title', '')
            
            btn = tk.Frame(scrollable_frame, bg=self.colors['bg_elevated'], cursor="hand2")
            btn.pack(fill=tk.X, pady=1)
            
            content = tk.Frame(btn, bg=self.colors['bg_elevated'])
            content.pack(fill=tk.X, padx=10, pady=6)
            
            pid_lbl = tk.Label(content, text=f"{pid}", font=self.tiny_font, fg=self.colors['text_muted'], bg=self.colors['bg_elevated'], width=6, anchor='w')
            pid_lbl.pack(side=tk.LEFT)
            
            name_lbl = tk.Label(content, text=name[:15], font=self.small_font, fg=self.colors['text'], bg=self.colors['bg_elevated'], width=15, anchor='w')
            name_lbl.pack(side=tk.LEFT)
            
            cpu_lbl = tk.Label(content, text=f"CPU:{cpu:.0f}", font=self.tiny_font, fg=self.colors['warning'], bg=self.colors['bg_elevated'], width=8)
            cpu_lbl.pack(side=tk.LEFT)
            
            mem_lbl = tk.Label(content, text=f"MEM:{mem}MB", font=self.tiny_font, fg=self.colors['secondary'], bg=self.colors['bg_elevated'], width=10)
            mem_lbl.pack(side=tk.LEFT)
            
            widgets = [btn, content, pid_lbl, name_lbl, cpu_lbl, mem_lbl]
            
            def on_enter(e, w=widgets):
                for widget in w:
                    widget.configure(bg=self.colors['bg_hover'])
            
            def on_leave(e, w=widgets):
                for widget in w:
                    widget.configure(bg=self.colors['bg_elevated'])
            
            def on_click(e, p=proc, pop=popup):
                self.kill_process(p, pop)
            
            for w in widgets:
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.bind("<Button-1>", on_click)
        
        btn_frame = tk.Frame(popup, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, padx=20, pady=15)
        
        cancel_btn = tk.Label(btn_frame, text="Cancel", font=self.tiny_font, fg=self.colors['text_muted'], bg=self.colors['bg'], cursor="hand2")
        cancel_btn.pack(side=tk.RIGHT)
        cancel_btn.bind("<Button-1>", lambda e: popup.destroy())
        cancel_btn.bind("<Enter>", lambda e: cancel_btn.configure(fg=self.colors['error']))
        cancel_btn.bind("<Leave>", lambda e: cancel_btn.configure(fg=self.colors['text_muted']))
    
    def kill_process(self, proc, popup):
        popup.destroy()
        
        pid = proc.get('PID', 0)
        name = proc.get('Name', 'Unknown')
        
        self.log(f"Killing: {name} (PID: {pid})", "warn")
        self.set_status("KILLING", is_warning=True)
        
        def do_kill():
            try:
                result = subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True, text=True, timeout=10,
                    creationflags=SUBPROCESS_FLAGS
                )
                if result.returncode == 0:
                    self.root.after(0, lambda: self.log(f"Killed: {name}", "accent"))
                    self.root.after(0, lambda: self.set_status("READY"))
                else:
                    self.root.after(0, lambda: self.log(f"Failed to kill: {name}", "error"))
                    self.root.after(0, lambda: self.set_status("FAILED", True))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
                self.root.after(0, lambda: self.set_status("ERROR", True))
        
        threading.Thread(target=do_kill, daemon=True).start()


def main():
    root = tk.Tk()
    app = VomTools(root)
    root.mainloop()


if __name__ == "__main__":
    main()
