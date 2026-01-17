import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import os
import threading
from datetime import datetime
import random
import sys

# Hide PowerShell windows on Windows
SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0

ASCII_BANNER = r"""
██╗   ██╗ ██████╗ ███╗   ███╗████████╗ ██████╗  ██████╗ ██╗     ███████╗
██║   ██║██╔═══██╗████╗ ████║╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔════╝
██║   ██║██║   ██║██╔████╔██║   ██║   ██║   ██║██║   ██║██║     ███████╗
╚██╗ ██╔╝██║   ██║██║╚██╔╝██║   ██║   ██║   ██║██║   ██║██║     ╚════██║
 ╚████╔╝ ╚██████╔╝██║ ╚═╝ ██║   ██║   ╚██████╔╝╚██████╔╝███████╗███████║
  ╚═══╝   ╚═════╝ ╚═╝     ╚═╝   ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚══════╝
"""

DIVIDER = "═" * 72
THIN_DIVIDER = "─" * 72

class VomTools:
    def __init__(self, root):
        self.root = root
        self.root.title("VomTools v1.0")
        self.root.geometry("800x600")
        self.root.configure(bg="#0a0a0a")
        self.root.resizable(True, True)
        
        # Set icon
        icon_path = os.path.join(os.path.dirname(__file__), 'vomtools.ico')
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        
        # Classic hacker fonts - Courier is the tried-and-true terminal font
        self.hacker_fonts = [
            "Courier New",        # THE classic hacker/terminal font
            "Courier",            # Original Courier
            "Lucida Console",     # Classic Windows console font
            "Fixedsys",           # Windows fixed-width pixel font  
            "Terminal",           # Classic DOS terminal font
            "Consolas",           # Fallback
        ]
        self.main_font = self.get_available_font(11)
        self.small_font = self.get_available_font(9)
        self.banner_font = self.get_available_font(7)
        
        # Animation state
        self.ripples = []
        self.matrix_chars = []
        
        # Colors
        self.bg_color = "#0a0a0a"
        self.fg_color = "#00ff00"
        self.accent_color = "#00aa00"
        self.dim_color = "#006600"
        self.error_color = "#ff3333"
        self.warn_color = "#ffaa00"
        
        # Define tasks/presets
        self.tasks = [
            {
                "name": "Launch GameDev Workspace",
                "key": "F1",
                "command": "powershell.exe",
                "args": ["-ExecutionPolicy", "Bypass", "-File", 
                         os.path.expanduser("~/Desktop/LaunchGameDevWorkspace.ps1")],
                "description": "Initialize game development environment"
            },
            {
                "name": "System Info",
                "key": "F2", 
                "command": "systeminfo",
                "args": [],
                "description": "Display system information"
            },
            {
                "name": "Network Status",
                "key": "F3",
                "command": "ipconfig",
                "args": ["/all"],
                "description": "Show network configuration"
            },
            {
                "name": "Clear Console",
                "key": "F4",
                "command": None,
                "args": [],
                "description": "Clear the output console"
            },
            {
                "name": "Audio Devices",
                "key": "F5",
                "command": "__audio_devices__",
                "args": [],
                "description": "List/set default audio output device"
            },
        ]
        
        self.setup_ui()
        self.bind_keys()
        self.log_startup()
    
    def get_available_font(self, size):
        """Find first available hacker-style font"""
        import tkinter.font as tkfont
        available = set(f.lower() for f in tkfont.families())
        for font in self.hacker_fonts:
            if font.lower() in available:
                return (font, size)
        return ("Consolas", size)
    
    def setup_ui(self):
        # Animation canvas (background layer)
        self.anim_canvas = tk.Canvas(
            self.root, 
            bg=self.bg_color, 
            highlightthickness=0
        )
        self.anim_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Bind click for ripple animation
        self.root.bind("<Button-1>", self.on_click_animation)
        
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ASCII Banner
        banner_label = tk.Label(
            main_frame, 
            text=ASCII_BANNER,
            font=self.banner_font,
            fg=self.fg_color,
            bg=self.bg_color,
            justify=tk.LEFT
        )
        banner_label.pack(pady=(0, 5))
        
        # Subtitle
        subtitle = tk.Label(
            main_frame,
            text="[ SYSTEM AUTOMATION TOOLKIT ]",
            font=self.main_font,
            fg=self.dim_color,
            bg=self.bg_color
        )
        subtitle.pack()
        
        # Divider
        divider_label = tk.Label(
            main_frame,
            text=DIVIDER,
            font=self.main_font,
            fg=self.dim_color,
            bg=self.bg_color
        )
        divider_label.pack(pady=5)
        
        # Tasks frame
        tasks_frame = tk.Frame(main_frame, bg=self.bg_color)
        tasks_frame.pack(fill=tk.X, pady=5)
        
        tasks_header = tk.Label(
            tasks_frame,
            text="┌─[ AVAILABLE TASKS ]" + "─" * 50 + "┐",
            font=self.main_font,
            fg=self.accent_color,
            bg=self.bg_color,
            anchor="w"
        )
        tasks_header.pack(fill=tk.X)
        
        # Task buttons
        for i, task in enumerate(self.tasks):
            task_row = tk.Frame(tasks_frame, bg=self.bg_color)
            task_row.pack(fill=tk.X, pady=2)
            
            btn = tk.Button(
                task_row,
                text=f"│ [{task['key']}] {task['name']}",
                font=self.main_font,
                fg=self.fg_color,
                bg="#1a1a1a",
                activeforeground="#ffffff",
                activebackground="#003300",
                border=0,
                cursor="hand2",
                anchor="w",
                width=35,
                command=lambda t=task: self.execute_task(t)
            )
            btn.pack(side=tk.LEFT)
            
            desc_label = tk.Label(
                task_row,
                text=f"  → {task['description']}",
                font=self.small_font,
                fg=self.dim_color,
                bg=self.bg_color,
                anchor="w"
            )
            desc_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tasks_footer = tk.Label(
            tasks_frame,
            text="└" + "─" * 70 + "┘",
            font=self.main_font,
            fg=self.accent_color,
            bg=self.bg_color,
            anchor="w"
        )
        tasks_footer.pack(fill=tk.X)
        
        # Console output
        console_header = tk.Label(
            main_frame,
            text="┌─[ CONSOLE OUTPUT ]" + "─" * 51 + "┐",
            font=self.main_font,
            fg=self.accent_color,
            bg=self.bg_color,
            anchor="w"
        )
        console_header.pack(fill=tk.X, pady=(10, 0))
        
        self.console = scrolledtext.ScrolledText(
            main_frame,
            font=self.small_font,
            fg=self.fg_color,
            bg="#0d0d0d",
            insertbackground=self.fg_color,
            selectbackground=self.accent_color,
            height=15,
            border=0,
            wrap=tk.WORD
        )
        self.console.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Configure text tags for colors
        self.console.tag_configure("success", foreground=self.fg_color)
        self.console.tag_configure("error", foreground=self.error_color)
        self.console.tag_configure("warn", foreground=self.warn_color)
        self.console.tag_configure("dim", foreground=self.dim_color)
        self.console.tag_configure("accent", foreground=self.accent_color)
        
        # Status bar
        status_frame = tk.Frame(main_frame, bg=self.bg_color)
        status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(
            status_frame,
            text="└─[ READY ]" + "─" * 61 + "┘",
            font=self.main_font,
            fg=self.accent_color,
            bg=self.bg_color,
            anchor="w"
        )
        self.status_label.pack(fill=tk.X)
    
    def bind_keys(self):
        for task in self.tasks:
            self.root.bind(f"<{task['key']}>", lambda e, t=task: self.execute_task(t))
        self.root.bind("<Escape>", lambda e: self.root.quit())
    
    # ─── ANIMATION SYSTEM ─────────────────────────────────────────────────
    def on_click_animation(self, event):
        """Spawn dark green ripple animation on click"""
        x, y = event.x_root - self.root.winfo_rootx(), event.y_root - self.root.winfo_rooty()
        self.spawn_ripple(x, y)
        self.spawn_matrix_burst(x, y)
    
    def spawn_ripple(self, x, y):
        """Create expanding ring ripple effect"""
        ripple = {
            'x': x, 'y': y, 
            'radius': 5, 
            'max_radius': 80,
            'alpha': 255
        }
        self.ripples.append(ripple)
        if len(self.ripples) == 1:
            self.animate_ripples()
    
    def animate_ripples(self):
        """Animate all active ripples"""
        self.anim_canvas.delete("ripple")
        
        active_ripples = []
        for ripple in self.ripples:
            ripple['radius'] += 4
            ripple['alpha'] -= 12
            
            if ripple['alpha'] > 0 and ripple['radius'] < ripple['max_radius']:
                # Calculate green intensity based on alpha
                intensity = max(0, min(255, int(ripple['alpha'] * 0.6)))
                color = f"#{0:02x}{intensity:02x}{0:02x}"
                
                self.anim_canvas.create_oval(
                    ripple['x'] - ripple['radius'],
                    ripple['y'] - ripple['radius'],
                    ripple['x'] + ripple['radius'],
                    ripple['y'] + ripple['radius'],
                    outline=color,
                    width=2,
                    tags="ripple"
                )
                active_ripples.append(ripple)
        
        self.ripples = active_ripples
        
        if self.ripples:
            self.root.after(25, self.animate_ripples)
    
    def spawn_matrix_burst(self, x, y):
        """Spawn falling matrix-style characters from click point"""
        chars = "01アイウエオカキクケコ"
        for _ in range(8):
            char_data = {
                'x': x + random.randint(-30, 30),
                'y': y,
                'char': random.choice(chars),
                'speed': random.uniform(3, 7),
                'alpha': 255,
                'id': None
            }
            self.matrix_chars.append(char_data)
        
        if len(self.matrix_chars) <= 8:
            self.animate_matrix()
    
    def animate_matrix(self):
        """Animate falling matrix characters"""
        self.anim_canvas.delete("matrix")
        
        active_chars = []
        for char in self.matrix_chars:
            char['y'] += char['speed']
            char['alpha'] -= 8
            
            if char['alpha'] > 0:
                intensity = max(0, min(255, int(char['alpha'] * 0.5)))
                color = f"#{0:02x}{intensity:02x}{0:02x}"
                
                self.anim_canvas.create_text(
                    char['x'], char['y'],
                    text=char['char'],
                    font=self.small_font,
                    fill=color,
                    tags="matrix"
                )
                active_chars.append(char)
        
        self.matrix_chars = active_chars
        
        if self.matrix_chars:
            self.root.after(30, self.animate_matrix)
    
    def log(self, message, tag="success"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] ", "dim")
        self.console.insert(tk.END, f"{message}\n", tag)
        self.console.see(tk.END)
    
    def log_startup(self):
        self.console.insert(tk.END, THIN_DIVIDER + "\n", "dim")
        self.log("VomTools initialized successfully", "accent")
        self.log("Press ESC to exit | Function keys to execute tasks", "dim")
        self.console.insert(tk.END, THIN_DIVIDER + "\n", "dim")
    
    def set_status(self, text, is_error=False):
        color = self.error_color if is_error else self.accent_color
        self.status_label.config(
            text=f"└─[ {text} ]" + "─" * (61 - len(text)) + "┘",
            fg=color
        )
    
    def execute_task(self, task):
        if task["command"] is None:
            # Special case: clear console
            self.console.delete(1.0, tk.END)
            self.log_startup()
            self.log("Console cleared", "accent")
            return
        
        if task["command"] == "__audio_devices__":
            self.show_audio_devices()
            return
        
        self.log(f"Executing: {task['name']}", "warn")
        self.set_status(f"RUNNING: {task['name']}")
        
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
            for line in result.stdout.strip().split('\n')[:50]:  # Limit output
                self.log(line, "success")
        if result.stderr:
            for line in result.stderr.strip().split('\n')[:20]:
                self.log(line, "error")
        
        if result.returncode == 0:
            self.log(f"✓ Task completed: {task['name']}", "accent")
            self.set_status("READY")
        else:
            self.log(f"✗ Task failed with code: {result.returncode}", "error")
            self.set_status("FAILED", True)
    
    # ─── AUDIO DEVICE MANAGEMENT ──────────────────────────────────────────
    def show_audio_devices(self):
        """Show audio playback devices and allow setting default"""
        self.log("Scanning audio playback devices...", "warn")
        self.set_status("SCANNING AUDIO DEVICES")
        
        def scan():
            try:
                # Use PowerShell registry approach for reliable audio endpoint enumeration
                ps_script = '''
$results = @()
$renderKey = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\MMDevices\\Audio\\Render"

if (Test-Path $renderKey) {
    foreach ($device in Get-ChildItem $renderKey) {
        $deviceGuid = $device.PSChildName
        $deviceKey = $device.PSPath
        
        # Check device state directly on device key (1 = active, others = disabled/unplugged)
        $devProps = Get-ItemProperty -Path $deviceKey -ErrorAction SilentlyContinue
        $state = $devProps.DeviceState
        
        # Only include active devices (state 1)
        if ($state -ne 1) { continue }
        
        $propsKey = Join-Path $deviceKey "Properties"
        if (-not (Test-Path $propsKey)) { continue }
        
        $props = Get-ItemProperty -Path $propsKey -ErrorAction SilentlyContinue
        
        # Get friendly name: {a45c254e...},2 = short name, {b3f8fa53...},6 = device description
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
            # Build the proper device ID format that PolicyConfig expects
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
                self.root.after(0, lambda: self.log(f"Error scanning devices: {e}", "error"))
                self.root.after(0, lambda: self.set_status("ERROR", True))
        
        thread = threading.Thread(target=scan, daemon=True)
        thread.start()
    
    def display_audio_devices(self, json_output, stderr=""):
        """Display audio devices and create selection buttons"""
        import json
        
        self.log(THIN_DIVIDER, "dim")
        self.log("AUDIO PLAYBACK DEVICES:", "accent")
        
        if stderr:
            self.log(f"Warning: {stderr[:200]}", "warn")
        
        try:
            devices = json.loads(json_output) if json_output.strip() else []
            if not isinstance(devices, list):
                devices = [devices]
            
            self.audio_devices = devices
            
            if not devices:
                self.log("No audio devices found", "warn")
                self.set_status("NO DEVICES FOUND", True)
                return
            
            for i, dev in enumerate(devices):
                name = dev.get('Name', 'Unknown Device')
                self.log(f"  [{i+1}] {name}", "success")
            
            self.log("", "dim")
            self.log("Select a device to set as default:", "dim")
            self.log(THIN_DIVIDER, "dim")
            
            # Create device selection popup
            self.show_device_selector(devices)
            self.set_status("SELECT AUDIO DEVICE")
            
        except json.JSONDecodeError:
            self.log("Could not parse device list", "error")
            self.log("Raw output:", "dim")
            self.log(json_output[:500] if json_output else "(empty)", "dim")
            self.set_status("PARSE ERROR", True)
    
    def show_device_selector(self, devices):
        """Show a popup to select audio device"""
        popup = tk.Toplevel(self.root)
        popup.title("Select Audio Device")
        popup.configure(bg=self.bg_color)
        popup.geometry("500x400")
        popup.transient(self.root)
        popup.grab_set()
        
        # Set icon
        icon_path = os.path.join(os.path.dirname(__file__), 'vomtools.ico')
        if os.path.exists(icon_path):
            popup.iconbitmap(icon_path)
        
        header = tk.Label(
            popup,
            text="┌─[ SELECT DEFAULT AUDIO OUTPUT ]─────────────────┐",
            font=self.main_font,
            fg=self.accent_color,
            bg=self.bg_color
        )
        header.pack(pady=(10, 5))
        
        # Role selection
        role_frame = tk.Frame(popup, bg=self.bg_color)
        role_frame.pack(fill=tk.X, padx=20, pady=5)
        
        role_label = tk.Label(
            role_frame,
            text="Audio Role:",
            font=self.small_font,
            fg=self.dim_color,
            bg=self.bg_color
        )
        role_label.pack(side=tk.LEFT)
        
        self.selected_role = tk.IntVar(value=1)  # Default to Multimedia
        roles = [("Multimedia", 1), ("Console", 0), ("Communications", 2)]
        
        for role_name, role_val in roles:
            rb = tk.Radiobutton(
                role_frame,
                text=role_name,
                variable=self.selected_role,
                value=role_val,
                font=self.small_font,
                fg=self.fg_color,
                bg=self.bg_color,
                activeforeground="#ffffff",
                activebackground=self.bg_color,
                selectcolor="#1a1a1a",
                cursor="hand2"
            )
            rb.pack(side=tk.LEFT, padx=10)
        
        # Scrollable frame for devices
        canvas = tk.Canvas(popup, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.bg_color)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for i, dev in enumerate(devices):
            name = dev.get('Name', 'Unknown Device')
            btn = tk.Button(
                scroll_frame,
                text=f"  [{i+1}] {name}  ",
                font=self.main_font,
                fg=self.fg_color,
                bg="#1a1a1a",
                activeforeground="#ffffff",
                activebackground="#003300",
                border=0,
                cursor="hand2",
                anchor="w",
                command=lambda d=dev, p=popup: self.set_default_audio(d, p, self.selected_role.get())
            )
            btn.pack(fill=tk.X, padx=20, pady=3)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")
        
        # Cancel button
        cancel_btn = tk.Button(
            popup,
            text="[ CANCEL ]",
            font=self.main_font,
            fg=self.error_color,
            bg="#1a1a1a",
            activeforeground="#ffffff",
            activebackground="#330000",
            border=0,
            cursor="hand2",
            command=popup.destroy
        )
        cancel_btn.pack(pady=10)
    
    def set_default_audio(self, device, popup, role=1):
        """Set the selected device as default audio output"""
        popup.destroy()
        
        name = device.get('Name', 'Unknown')
        device_id = device.get('ID', '')
        role_names = {0: "Console", 1: "Multimedia", 2: "Communications"}
        role_name = role_names.get(role, "Unknown")
        
        self.log(f"Setting {role_name} audio device: {name}", "warn")
        self.set_status(f"SETTING: {name[:30]}")
        
        def set_device():
            try:
                # Use PolicyConfigClient COM interface to set default audio device
                # Using the Windows 10/11 IPolicyConfig interface
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
    Write-Output "SUCCESS: Default audio device changed"
}} else {{
    Write-Output "ERROR: Failed to set default device (HRESULT: $result)"
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
        """Handle the result of setting audio device"""
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if "SUCCESS" in line:
                    self.log(line, "accent")
                elif "ERROR" in line:
                    self.log(line, "error")
                else:
                    self.log(line, "success")
        
        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                self.log(line, "error")
        
        if result.returncode == 0 and "SUCCESS" in (result.stdout or ""):
            self.log(f"✓ Audio device set: {device_name}", "accent")
            self.set_status("READY")
        else:
            self.set_status("FAILED", True)


def main():
    root = tk.Tk()
    app = VomTools(root)
    root.mainloop()


if __name__ == "__main__":
    main()
