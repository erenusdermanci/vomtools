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
                "name": "Suspend Task",
                "key": "F2",
                "icon": "◫",
                "command": "__suspend_task__",
                "args": [],
                "description": "Suspend/resume applications"
            },
            {
                "name": "GameDev Workspace",
                "key": "F3",
                "icon": "▶",
                "command": "powershell.exe",
                "args": ["-ExecutionPolicy", "Bypass", "-File", 
                         os.path.expanduser("~/Desktop/LaunchGameDevWorkspace.ps1")],
                "description": "Launch dev environment"
            },
            {
                "name": "System Info",
                "key": "F4",
                "icon": "◈",
                "command": "systeminfo",
                "args": [],
                "description": "Display system specs"
            },
            {
                "name": "Network Status",
                "key": "F5",
                "icon": "◎",
                "command": "ipconfig",
                "args": ["/all"],
                "description": "Network configuration"
            },
            {
                "name": "Clear Console",
                "key": "F6",
                "icon": "◇",
                "command": None,
                "args": [],
                "description": "Reset terminal output"
            }
        ]
        
        self.tray_icon = None
        self.is_visible = True
        
        self.setup_ui()
        self.setup_tray()
        self.bind_keys()
        self.start_animations()
        self.log_startup()
    
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
        
        self.console = scrolledtext.ScrolledText(
            console_border,
            font=self.small_font,
            fg=self.colors['text'],
            bg='#080808',  # Very dark to show orb glow through edges
            insertbackground=self.colors['primary'],
            selectbackground=self.colors['primary_dark'],
            selectforeground=self.colors['text'],
            border=0,
            wrap=tk.WORD,
            padx=12,
            pady=10
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
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
    
    def show_suspend_selector(self, processes):
        popup = tk.Toplevel(self.root)
        popup.title("Suspend/Resume Task")
        popup.configure(bg=self.colors['bg'])
        popup.geometry("550x450")
        popup.transient(self.root)
        popup.grab_set()
        
        icon_path = os.path.join(os.path.dirname(__file__), 'vomtools.ico')
        if os.path.exists(icon_path):
            popup.iconbitmap(icon_path)
        
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
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
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
        popup.title("Audio Device")
        popup.configure(bg=self.colors['bg'])
        popup.geometry("450x380")
        popup.transient(self.root)
        popup.grab_set()
        
        icon_path = os.path.join(os.path.dirname(__file__), 'vomtools.ico')
        if os.path.exists(icon_path):
            popup.iconbitmap(icon_path)
        
        # Header
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


def main():
    root = tk.Tk()
    app = VomTools(root)
    root.mainloop()


if __name__ == "__main__":
    main()
