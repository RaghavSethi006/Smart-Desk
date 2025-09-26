import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, font
import json
import os
from datetime import datetime, timedelta
import threading
import time
from abc import ABC, abstractmethod
import subprocess
import sys
from PIL import Image, ImageTk
import win32gui
import win32con
import win32api

class ModernButton(tk.Frame):
    """Modern Material Design 3 button"""
    def __init__(self, parent, text, command, style="filled", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.command = command
        self.style = style
        
        # Material Design 3 colors
        colors = {
            "filled": {"bg": "#6750A4", "fg": "#FFFFFF", "hover": "#7965AF"},
            "outlined": {"bg": "#FFFFFF", "fg": "#6750A4", "hover": "#F7F2FA", "border": "#79747E"},
            "text": {"bg": "#FFFFFF", "fg": "#6750A4", "hover": "#F7F2FA"},
            "tonal": {"bg": "#E8DEF8", "fg": "#1D192B", "hover": "#DDD1EB"},
            "danger": {"bg": "#B3261E", "fg": "#FFFFFF", "hover": "#C5362E"}
        }
        
        self.colors = colors.get(style, colors["filled"])
        
        self.configure(bg=self.colors["bg"], relief="flat", bd=0)
        
        self.label = tk.Label(
            self, 
            text=text, 
            bg=self.colors["bg"], 
            fg=self.colors["fg"],
            font=("Segoe UI", 10, "normal"),
            cursor="hand2",
            pady=8,
            padx=16
        )
        self.label.pack(fill="both", expand=True)
        
        # Add border for outlined style
        if style == "outlined":
            self.configure(highlightbackground=self.colors["border"], highlightthickness=1)
        
        # Bind events
        self.label.bind("<Button-1>", self._on_click)
        self.label.bind("<Enter>", self._on_enter)
        self.label.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        
        # Add subtle shadow for filled buttons
        if style == "filled":
            self.configure(relief="solid", bd=0)
    
    def _on_click(self, event):
        if self.command:
            self.command()
    
    def _on_enter(self, event):
        hover_color = self.colors.get("hover", self.colors["bg"])
        self.configure(bg=hover_color)
        self.label.configure(bg=hover_color)
    
    def _on_leave(self, event):
        self.configure(bg=self.colors["bg"])
        self.label.configure(bg=self.colors["bg"])

class ModernCard(tk.Frame):
    """Modern Material Design 3 card"""
    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, bg="#FFFFFF", relief="solid", bd=0, **kwargs)
        
        # Add subtle shadow effect with multiple frames
        shadow_frame = tk.Frame(parent, bg="#E0E0E0", height=2)
        shadow_frame.pack(fill="x")
        
        if title:
            title_frame = tk.Frame(self, bg="#FFFFFF", pady=16, padx=20)
            title_frame.pack(fill="x")
            
            title_label = tk.Label(
                title_frame,
                text=title,
                font=("Segoe UI", 14, "bold"),
                bg="#FFFFFF",
                fg="#1C1B1F"
            )
            title_label.pack(anchor="w")

class DesktopWidget:
    """Represents a widget that can be pinned to desktop"""
    def __init__(self, widget_instance, x=100, y=100):
        self.widget_instance = widget_instance
        self.x = x
        self.y = y
        self.desktop_window = None
        self.is_pinned = False
    
    def pin_to_desktop(self):
        """Pin widget to desktop as desktop extension (behind other apps)"""
        if self.is_pinned:
            return
        
        # Create desktop window
        self.desktop_window = tk.Toplevel()
        self.desktop_window.title("")
        self.desktop_window.overrideredirect(True)  # Remove window decorations
        
        # Make window stay behind other applications (desktop level)
        self.desktop_window.wm_attributes("-topmost", False)
        self.desktop_window.wm_attributes("-alpha", self.widget_instance.config.get('opacity', 0.9))
        
        # Position on desktop
        self.desktop_window.geometry(f"+{self.x}+{self.y}")
        
        # Create widget content
        widget_frame = self.widget_instance.create_widget(self.desktop_window)
        widget_frame.pack()
        
        # Send to desktop level (behind all other windows)
        self._send_to_desktop_level()
        
        # Make draggable
        self._make_draggable()
        
        self.is_pinned = True
    
    def _send_to_desktop_level(self):
        """Send window to desktop level using Windows API"""
        try:
            import win32gui
            import win32con
            
            # Get window handle
            hwnd = int(self.desktop_window.wm_frame(), 16)
            
            # Set window to bottom of Z-order (desktop level)
            win32gui.SetWindowPos(
                hwnd, 
                win32con.HWND_BOTTOM,  # Place at bottom
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
            )
            
            # Additional: Set as desktop child window
            desktop_hwnd = win32gui.GetDesktopWindow()
            win32gui.SetParent(hwnd, desktop_hwnd)
            
        except ImportError:
            print("win32gui not available - widgets will stay on top")
        except Exception as e:
            print(f"Could not send to desktop level: {e}")
    
    def _make_draggable(self):
        """Make the widget draggable"""
        def start_drag(event):
            self.desktop_window.start_x = event.x
            self.desktop_window.start_y = event.y
        
        def do_drag(event):
            x = self.desktop_window.winfo_x() + event.x - self.desktop_window.start_x
            y = self.desktop_window.winfo_y() + event.y - self.desktop_window.start_y
            self.desktop_window.geometry(f"+{x}+{y}")
            self.x, self.y = x, y
        
        self.desktop_window.bind("<Button-1>", start_drag)
        self.desktop_window.bind("<B1-Motion>", do_drag)
    
    def unpin_from_desktop(self):
        """Remove widget from desktop"""
        if self.desktop_window:
            self.desktop_window.destroy()
            self.desktop_window = None
            self.is_pinned = False

class BaseWidget(ABC):
    """Abstract base class for all widgets with modern styling"""
    
    def __init__(self, master, config=None):
        self.master = master
        self.config = config or self.get_default_config()
        self.frame = None
        self.update_job = None
        
    @abstractmethod
    def get_default_config(self):
        """Return default configuration for the widget"""
        pass
    
    @abstractmethod
    def create_widget(self, parent):
        """Create the widget UI"""
        pass
    
    @abstractmethod
    def update_content(self):
        """Update widget content"""
        pass
    
    def apply_modern_styling(self, widget):
        """Apply modern Material Design styling"""
        if hasattr(widget, 'configure'):
            # Material Design 3 color tokens
            bg_color = self.config.get('bg_color', '#FFFFFF')
            text_color = self.config.get('text_color', '#1C1B1F')
            
            widget.configure(
                bg=bg_color,
                fg=text_color,
                font=("Segoe UI", self.config.get('font_size', 12)),
                relief="flat",
                bd=0
            )

class ClockWidget(BaseWidget):
    """Modern digital clock widget"""
    
    def get_default_config(self):
        return {
            'width': 280,
            'height': 120,
            'bg_color': '#1C1B1F',
            'text_color': '#FFFFFF',
            'accent_color': '#D0BCFF',
            'font_family': 'Segoe UI',
            'font_size': 18,
            'opacity': 0.95,
            'format_12h': True,
            'corner_radius': 16
        }
    
    def create_widget(self, parent):
        # Main container with rounded corners effect
        self.frame = tk.Frame(
            parent, 
            bg=self.config['bg_color'],
            relief="flat",
            bd=0,
            padx=20,
            pady=16
        )
        self.frame.configure(width=self.config['width'], height=self.config['height'])
        
        # Time display
        self.time_label = tk.Label(
            self.frame,
            text="00:00:00",
            bg=self.config['bg_color'],
            fg=self.config['text_color'],
            font=(self.config['font_family'], self.config['font_size'] + 8, 'normal'),
            anchor='center'
        )
        self.time_label.pack(expand=True, pady=(8, 4))
        
        # Date display
        self.date_label = tk.Label(
            self.frame,
            text="",
            bg=self.config['bg_color'],
            fg=self.config['accent_color'],
            font=(self.config['font_family'], self.config['font_size'] - 2, 'normal'),
            anchor='center'
        )
        self.date_label.pack(expand=True, pady=(0, 8))
        
        self.update_content()
        return self.frame
    
    def update_content(self):
        if hasattr(self, 'time_label') and self.time_label.winfo_exists():
            now = datetime.now()
            if self.config.get('format_12h', True):
                time_str = now.strftime("%I:%M:%S %p")
            else:
                time_str = now.strftime("%H:%M:%S")
            
            date_str = now.strftime("%A, %B %d")
            
            self.time_label.configure(text=time_str)
            self.date_label.configure(text=date_str)
            
            # Schedule next update
            self.master.after(1000, self.update_content)

class TodoWidget(BaseWidget):
    """Modern to-do list widget"""
    
    def get_default_config(self):
        return {
            'width': 320,
            'height': 400,
            'bg_color': '#FFFFFF',
            'text_color': '#1C1B1F',
            'accent_color': '#6750A4',
            'surface_color': '#F7F2FA',
            'font_family': 'Segoe UI',
            'font_size': 11,
            'opacity': 0.95,
            'max_items': 10
        }
    
    def create_widget(self, parent):
        self.frame = tk.Frame(
            parent, 
            bg=self.config['bg_color'],
            relief="flat",
            bd=0,
            padx=16,
            pady=16
        )
        self.frame.configure(width=self.config['width'], height=self.config['height'])
        
        # Header
        header_frame = tk.Frame(self.frame, bg=self.config['bg_color'])
        header_frame.pack(fill='x', pady=(0, 12))
        
        title = tk.Label(
            header_frame,
            text="Tasks",
            bg=self.config['bg_color'],
            fg=self.config['text_color'],
            font=(self.config['font_family'], self.config['font_size'] + 6, 'bold')
        )
        title.pack(anchor='w')
        
        # Input section
        input_frame = tk.Frame(self.frame, bg=self.config['surface_color'], relief="flat")
        input_frame.pack(fill='x', pady=(0, 16))
        input_frame.configure(padx=12, pady=8)
        
        self.entry = tk.Entry(
            input_frame,
            bg=self.config['surface_color'],
            fg=self.config['text_color'],
            font=(self.config['font_family'], self.config['font_size']),
            relief="flat",
            bd=0,
            insertbackground=self.config['accent_color']
        )
        self.entry.pack(side='left', fill='x', expand=True, padx=(0, 8))
        self.entry.bind('<Return>', self.add_task)
        
        add_btn = ModernButton(
            input_frame,
            text="Add",
            command=self.add_task,
            style="filled"
        )
        add_btn.pack(side='right')
        
        # Tasks container
        tasks_container = tk.Frame(self.frame, bg=self.config['bg_color'])
        tasks_container.pack(fill='both', expand=True)
        
        # Custom listbox styling
        self.tasks_frame = tk.Frame(tasks_container, bg=self.config['bg_color'])
        self.tasks_frame.pack(fill='both', expand=True)
        
        self.tasks = []
        self.task_widgets = []
        self.update_content()
        return self.frame
    
    def add_task(self, event=None):
        task_text = self.entry.get().strip()
        if task_text:
            self.tasks.append({'text': task_text, 'completed': False})
            self.entry.delete(0, 'end')
            self.update_content()
    
    def toggle_task(self, index):
        if 0 <= index < len(self.tasks):
            self.tasks[index]['completed'] = not self.tasks[index]['completed']
            self.update_content()
    
    def delete_task(self, index):
        if 0 <= index < len(self.tasks):
            del self.tasks[index]
            self.update_content()
    
    def update_content(self):
        # Clear existing task widgets
        for widget in self.task_widgets:
            widget.destroy()
        self.task_widgets = []
        
        # Create task items
        for i, task in enumerate(self.tasks):
            task_item = tk.Frame(self.tasks_frame, bg=self.config['surface_color'], pady=8, padx=12)
            task_item.pack(fill='x', pady=2)
            
            # Checkbox effect
            checkbox = tk.Label(
                task_item,
                text="✓" if task['completed'] else "○",
                bg=self.config['surface_color'],
                fg=self.config['accent_color'] if task['completed'] else self.config['text_color'],
                font=(self.config['font_family'], self.config['font_size'] + 2),
                cursor="hand2"
            )
            checkbox.pack(side='left', padx=(0, 8))
            checkbox.bind("<Button-1>", lambda e, idx=i: self.toggle_task(idx))
            
            # Task text
            text_color = '#79747E' if task['completed'] else self.config['text_color']
            font_style = 'overstrike' if task['completed'] else 'normal'
            
            task_label = tk.Label(
                task_item,
                text=task['text'],
                bg=self.config['surface_color'],
                fg=text_color,
                font=(self.config['font_family'], self.config['font_size'], font_style),
                anchor='w'
            )
            task_label.pack(side='left', fill='x', expand=True)
            
            # Delete button
            delete_btn = tk.Label(
                task_item,
                text="×",
                bg=self.config['surface_color'],
                fg='#B3261E',
                font=(self.config['font_family'], self.config['font_size'] + 4),
                cursor="hand2"
            )
            delete_btn.pack(side='right')
            delete_btn.bind("<Button-1>", lambda e, idx=i: self.delete_task(idx))
            
            self.task_widgets.append(task_item)

class WeatherWidget(BaseWidget):
    """Modern weather widget"""
    
    def get_default_config(self):
        return {
            'width': 300,
            'height': 200,
            'bg_color': '#E3F2FD',
            'text_color': '#1565C0',
            'accent_color': '#2196F3',
            'font_family': 'Segoe UI',
            'font_size': 12,
            'opacity': 0.95,
            'location': 'Calgary, AB'
        }
    
    def create_widget(self, parent):
        self.frame = tk.Frame(
            parent,
            bg=self.config['bg_color'],
            relief="flat",
            bd=0,
            padx=20,
            pady=16
        )
        self.frame.configure(width=self.config['width'], height=self.config['height'])
        
        # Location header
        self.location_label = tk.Label(
            self.frame,
            text=self.config['location'],
            bg=self.config['bg_color'],
            fg=self.config['text_color'],
            font=(self.config['font_family'], self.config['font_size'], 'bold')
        )
        self.location_label.pack(pady=(0, 8))
        
        # Main weather info
        main_frame = tk.Frame(self.frame, bg=self.config['bg_color'])
        main_frame.pack(expand=True)
        
        # Temperature
        self.temp_label = tk.Label(
            main_frame,
            text="--°C",
            bg=self.config['bg_color'],
            fg=self.config['accent_color'],
            font=(self.config['font_family'], self.config['font_size'] + 16, 'normal')
        )
        self.temp_label.pack()
        
        # Condition
        self.condition_label = tk.Label(
            main_frame,
            text="--",
            bg=self.config['bg_color'],
            fg=self.config['text_color'],
            font=(self.config['font_family'], self.config['font_size'] + 2)
        )
        self.condition_label.pack(pady=8)
        
        # Additional info
        info_frame = tk.Frame(self.frame, bg=self.config['bg_color'])
        info_frame.pack(fill='x')
        
        self.humidity_label = tk.Label(
            info_frame,
            text="Humidity: --%",
            bg=self.config['bg_color'],
            fg=self.config['text_color'],
            font=(self.config['font_family'], self.config['font_size'] - 1)
        )
        self.humidity_label.pack()
        
        self.update_content()
        return self.frame
    
    def update_content(self):
        # Simulate weather data
        import random
        temperatures = [-10, -5, 0, 5, 10, 15, 20, 25]
        conditions = ["Sunny", "Cloudy", "Partly Cloudy", "Light Snow", "Snow"]
        
        temp = random.choice(temperatures)
        condition = random.choice(conditions)
        humidity = random.randint(30, 90)
        
        if hasattr(self, 'temp_label') and self.temp_label.winfo_exists():
            self.temp_label.configure(text=f"{temp}°C")
            self.condition_label.configure(text=condition)
            self.humidity_label.configure(text=f"Humidity: {humidity}%")
            
            self.master.after(600000, self.update_content)  # 10 minutes

class TimerWidget(BaseWidget):
    """Modern timer widget"""
    
    def get_default_config(self):
        return {
            'width': 250,
            'height': 180,
            'bg_color': '#FFF3E0',
            'text_color': '#E65100',
            'accent_color': '#FF9800',
            'font_family': 'Segoe UI',
            'font_size': 14,
            'opacity': 0.95
        }
    
    def create_widget(self, parent):
        self.frame = tk.Frame(
            parent,
            bg=self.config['bg_color'],
            relief="flat",
            bd=0,
            padx=20,
            pady=16
        )
        self.frame.configure(width=self.config['width'], height=self.config['height'])
        
        # Title
        title = tk.Label(
            self.frame,
            text="Timer",
            bg=self.config['bg_color'],
            fg=self.config['text_color'],
            font=(self.config['font_family'], self.config['font_size'] + 2, 'bold')
        )
        title.pack(pady=(0, 12))
        
        # Time display
        self.time_display = tk.Label(
            self.frame,
            text="00:00",
            bg=self.config['bg_color'],
            fg=self.config['accent_color'],
            font=(self.config['font_family'], self.config['font_size'] + 10, 'bold')
        )
        self.time_display.pack(pady=8)
        
        # Input section
        input_frame = tk.Frame(self.frame, bg=self.config['bg_color'])
        input_frame.pack(pady=8)
        
        self.minutes_var = tk.StringVar(value="5")
        minutes_entry = tk.Entry(
            input_frame,
            textvariable=self.minutes_var,
            width=5,
            font=(self.config['font_family'], self.config['font_size']),
            bg='white',
            fg=self.config['text_color'],
            relief="flat",
            bd=1,
            justify='center'
        )
        minutes_entry.pack(side='left', padx=(0, 4))
        
        tk.Label(
            input_frame,
            text="minutes",
            bg=self.config['bg_color'],
            fg=self.config['text_color'],
            font=(self.config['font_family'], self.config['font_size'])
        ).pack(side='left')
        
        # Control buttons
        control_frame = tk.Frame(self.frame, bg=self.config['bg_color'])
        control_frame.pack(pady=12)
        
        self.start_btn = ModernButton(
            control_frame,
            text="Start",
            command=self.start_timer,
            style="filled"
        )
        self.start_btn.pack(side='left', padx=(0, 8))
        
        self.stop_btn = ModernButton(
            control_frame,
            text="Stop",
            command=self.stop_timer,
            style="danger"
        )
        self.stop_btn.pack(side='left')
        
        self.remaining_time = 0
        self.timer_active = False
        self.update_content()
        return self.frame
    
    def start_timer(self):
        try:
            minutes = int(self.minutes_var.get())
            self.remaining_time = minutes * 60
            self.timer_active = True
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of minutes")
    
    def stop_timer(self):
        self.timer_active = False
        self.remaining_time = 0
        if hasattr(self, 'time_display'):
            self.time_display.configure(text="00:00")
    
    def update_content(self):
        if hasattr(self, 'time_display') and self.time_display.winfo_exists():
            if self.timer_active and self.remaining_time > 0:
                minutes = self.remaining_time // 60
                seconds = self.remaining_time % 60
                self.time_display.configure(text=f"{minutes:02d}:{seconds:02d}")
                self.remaining_time -= 1
            elif self.timer_active and self.remaining_time <= 0:
                self.time_display.configure(text="TIME!")
                self.timer_active = False
                messagebox.showinfo("Timer", "Time's up!")
            
            self.master.after(1000, self.update_content)

class WidgetManager:
    """Modern widget manager with desktop integration"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Desktop Widget Manager")
        self.root.geometry("1100x700")
        
        # Modern styling
        self.root.configure(bg='#F5F5F5')
        style = ttk.Style()
        style.theme_use('winnative')
        
        # Configure modern colors
        style.configure('Modern.TFrame', background='#FFFFFF')
        style.configure('Modern.TLabel', background='#FFFFFF', foreground='#1C1B1F')
        
        # Available widget types
        self.widget_types = {
            'Clock': ClockWidget,
            'Todo List': TodoWidget,
            'Weather': WeatherWidget,
            'Timer': TimerWidget
        }
        
        self.active_widgets = []
        self.desktop_widgets = []  # Track pinned widgets
        self.preview_window = None
        
        self.setup_modern_ui()
        self.load_config()
    
    def setup_modern_ui(self):
        """Setup modern Material Design UI"""
        # Main container
        main_container = tk.Frame(self.root, bg='#F5F5F5')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_container, bg='#F5F5F5', height=60)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="Desktop Widget Manager",
            font=("Segoe UI", 24, "normal"),
            bg='#F5F5F5',
            fg='#1C1B1F'
        )
        title_label.pack(side='left', pady=16)
        
        subtitle_label = tk.Label(
            header_frame,
            text="Create and manage modern desktop widgets",
            font=("Segoe UI", 12, "normal"),
            bg='#F5F5F5',
            fg='#49454F'
        )
        subtitle_label.pack(side='left', padx=(12, 0), pady=20)
        
        # Content area
        content_frame = tk.Frame(main_container, bg='#F5F5F5')
        content_frame.pack(fill='both', expand=True)
        
        # Left panel - Controls
        left_panel = ModernCard(content_frame, title="Widget Controls")
        left_panel.pack(side='left', fill='y', padx=(0, 20), ipadx=20, ipady=20)
        left_panel.configure(width=300)
        left_panel.pack_propagate(False)
        
        # Widget type selection
        selection_frame = tk.Frame(left_panel, bg='#FFFFFF', pady=12)
        selection_frame.pack(fill='x')
        
        tk.Label(
            selection_frame,
            text="Select Widget Type",
            font=("Segoe UI", 12, "bold"),
            bg='#FFFFFF',
            fg='#1C1B1F'
        ).pack(anchor='w', pady=(0, 8))
        
        self.widget_type_var = tk.StringVar(value='Clock')
        for widget_type in self.widget_types.keys():
            radio_frame = tk.Frame(selection_frame, bg='#FFFFFF')
            radio_frame.pack(fill='x', pady=2)
            
            radio = tk.Radiobutton(
                radio_frame,
                text=widget_type,
                variable=self.widget_type_var,
                value=widget_type,
                bg='#FFFFFF',
                fg='#1C1B1F',
                font=("Segoe UI", 10),
                selectcolor='#6750A4',
                activebackground='#FFFFFF',
                relief='flat',
                bd=0
            )
            radio.pack(anchor='w')
        
        # Action buttons
        buttons_frame = tk.Frame(left_panel, bg='#FFFFFF', pady=16)
        buttons_frame.pack(fill='x')
        
        ModernButton(
            buttons_frame,
            text="Create Widget",
            command=self.create_widget,
            style="filled"
        ).pack(fill='x', pady=4)
        
        ModernButton(
            buttons_frame,
            text="Desktop Preview",
            command=self.open_desktop_preview,
            style="tonal"
        ).pack(fill='x', pady=4)
        
        ModernButton(
            buttons_frame,
            text="Customize Selected",
            command=self.customize_widget,
            style="outlined"
        ).pack(fill='x', pady=4)
        
        # Separator
        separator = tk.Frame(left_panel, bg='#E7E0EC', height=1)
        separator.pack(fill='x', pady=16)
        
        # Management buttons
        ModernButton(
            left_panel,
            text="Pin Selected to Desktop",
            command=self.pin_selected_widget,
            style="filled"
        ).pack(fill='x', pady=4)
        
        ModernButton(
            left_panel,
            text="Unpin Selected",
            command=self.unpin_selected_widget,
            style="outlined"
        ).pack(fill='x', pady=4)
        
        ModernButton(
            left_panel,
            text="Remove Selected",
            command=self.remove_widget,
            style="danger"
        ).pack(fill='x', pady=4)
        
        # File operations
        separator2 = tk.Frame(left_panel, bg='#E7E0EC', height=1)
        separator2.pack(fill='x', pady=16)
        
        ModernButton(
            left_panel,
            text="Save Layout",
            command=self.save_config,
            style="text"
        ).pack(fill='x', pady=2)
        
        ModernButton(
            left_panel,
            text="Load Layout",
            command=self.load_config,
            style="text"
        ).pack(fill='x', pady=2)
        
        # Right panel - Widget list and preview
        right_panel = ModernCard(content_frame, title="Active Widgets")
        right_panel.pack(side='right', fill='both', expand=True, ipadx=20, ipady=20)
        
        # Widgets listbox with modern styling
        listbox_frame = tk.Frame(right_panel, bg='#FFFFFF')
        listbox_frame.pack(fill='both', expand=True, pady=16)
        
        # Custom listbox
        self.widgets_listbox = tk.Listbox(
            listbox_frame,
            bg='#F7F2FA',
            fg='#1C1B1F',
            font=("Segoe UI", 11),
            relief='flat',
            bd=0,
            selectbackground='#6750A4',
            selectforeground='#FFFFFF',
            activestyle='none'
        )
        
        scrollbar = tk.Scrollbar(
            listbox_frame,
            orient='vertical',
            bg='#F7F2FA',
            troughcolor='#F7F2FA',
            relief='flat',
            bd=0
        )
        
        self.widgets_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.widgets_listbox.yview)
        
        self.widgets_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def create_widget(self):
        """Create a new widget of the selected type"""
        widget_type = self.widget_type_var.get()
        widget_class = self.widget_types[widget_type]
        
        widget_instance = widget_class(self.root)
        widget_info = {
            'type': widget_type,
            'instance': widget_instance,
            'name': f"{widget_type} #{len(self.active_widgets) + 1}",
            'desktop_widget': None
        }
        
        self.active_widgets.append(widget_info)
        
        # Automatically pin to desktop
        self.pin_widget_to_desktop(widget_info)
        
        self.update_widgets_list()
        self.show_success_message(f"{widget_type} widget created and pinned to desktop!")
    
    def pin_widget_to_desktop(self, widget_info):
        """Pin a widget to the desktop"""
        if widget_info['desktop_widget'] and widget_info['desktop_widget'].is_pinned:
            return
        
        # Calculate position (stagger widgets)
        x = 100 + (len(self.desktop_widgets) * 30)
        y = 100 + (len(self.desktop_widgets) * 30)
        
        desktop_widget = DesktopWidget(widget_info['instance'], x, y)
        desktop_widget.pin_to_desktop()
        
        widget_info['desktop_widget'] = desktop_widget
        self.desktop_widgets.append(desktop_widget)
    
    def pin_selected_widget(self):
        """Pin selected widget to desktop"""
        selection = self.widgets_listbox.curselection()
        if selection:
            index = selection[0]
            widget_info = self.active_widgets[index]
            
            if widget_info['desktop_widget'] and widget_info['desktop_widget'].is_pinned:
                self.show_info_message("Widget is already pinned to desktop!")
                return
            
            self.pin_widget_to_desktop(widget_info)
            self.show_success_message(f"{widget_info['name']} pinned to desktop!")
        else:
            self.show_warning_message("Please select a widget to pin.")
    
    def unpin_selected_widget(self):
        """Unpin selected widget from desktop"""
        selection = self.widgets_listbox.curselection()
        if selection:
            index = selection[0]
            widget_info = self.active_widgets[index]
            
            if widget_info['desktop_widget'] and widget_info['desktop_widget'].is_pinned:
                widget_info['desktop_widget'].unpin_from_desktop()
                self.desktop_widgets.remove(widget_info['desktop_widget'])
                widget_info['desktop_widget'] = None
                self.show_success_message(f"{widget_info['name']} unpinned from desktop!")
            else:
                self.show_info_message("Widget is not currently pinned to desktop.")
        else:
            self.show_warning_message("Please select a widget to unpin.")
    
    def remove_widget(self):
        """Remove the selected widget"""
        selection = self.widgets_listbox.curselection()
        if selection:
            index = selection[0]
            widget_info = self.active_widgets[index]
            
            # Unpin from desktop if pinned
            if widget_info['desktop_widget'] and widget_info['desktop_widget'].is_pinned:
                widget_info['desktop_widget'].unpin_from_desktop()
                if widget_info['desktop_widget'] in self.desktop_widgets:
                    self.desktop_widgets.remove(widget_info['desktop_widget'])
            
            # Clean up widget resources
            if hasattr(widget_info['instance'], 'cleanup'):
                widget_info['instance'].cleanup()
            
            del self.active_widgets[index]
            self.update_widgets_list()
            self.show_success_message("Widget removed successfully!")
        else:
            self.show_warning_message("Please select a widget to remove.")
    
    def customize_widget(self):
        """Open customization dialog for selected widget"""
        selection = self.widgets_listbox.curselection()
        if selection:
            index = selection[0]
            widget_info = self.active_widgets[index]
            self.open_modern_customization_dialog(widget_info)
        else:
            self.show_warning_message("Please select a widget to customize.")
    
    def open_modern_customization_dialog(self, widget_info):
        """Open modern customization dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Customize {widget_info['name']}")
        dialog.geometry("500x600")
        dialog.configure(bg='#F5F5F5')
        dialog.grab_set()
        
        # Center the dialog
        dialog.transient(self.root)
        
        config = widget_info['instance'].config
        
        # Main container
        main_frame = tk.Frame(dialog, bg='#F5F5F5', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Header
        header = tk.Label(
            main_frame,
            text=f"Customize {widget_info['name']}",
            font=("Segoe UI", 18, "bold"),
            bg='#F5F5F5',
            fg='#1C1B1F'
        )
        header.pack(anchor='w', pady=(0, 20))
        
        # Scrollable content
        canvas = tk.Canvas(main_frame, bg='#F5F5F5', highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#F5F5F5')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Size settings card
        size_card = ModernCard(scrollable_frame, title="Size & Dimensions")
        size_card.pack(fill='x', pady=(0, 16))
        
        size_content = tk.Frame(size_card, bg='#FFFFFF', padx=20, pady=16)
        size_content.pack(fill='x')
        
        # Width
        width_frame = tk.Frame(size_content, bg='#FFFFFF')
        width_frame.pack(fill='x', pady=4)
        tk.Label(width_frame, text="Width (px):", font=("Segoe UI", 10), bg='#FFFFFF', fg='#1C1B1F').pack(side='left')
        width_var = tk.StringVar(value=str(config.get('width', 200)))
        width_entry = tk.Entry(width_frame, textvariable=width_var, font=("Segoe UI", 10), bg='#F7F2FA', relief='flat', bd=5)
        width_entry.pack(side='right', padx=(10, 0))
        
        # Height
        height_frame = tk.Frame(size_content, bg='#FFFFFF')
        height_frame.pack(fill='x', pady=4)
        tk.Label(height_frame, text="Height (px):", font=("Segoe UI", 10), bg='#FFFFFF', fg='#1C1B1F').pack(side='left')
        height_var = tk.StringVar(value=str(config.get('height', 100)))
        height_entry = tk.Entry(height_frame, textvariable=height_var, font=("Segoe UI", 10), bg='#F7F2FA', relief='flat', bd=5)
        height_entry.pack(side='right', padx=(10, 0))
        
        # Colors card
        colors_card = ModernCard(scrollable_frame, title="Colors & Theme")
        colors_card.pack(fill='x', pady=(0, 16))
        
        colors_content = tk.Frame(colors_card, bg='#FFFFFF', padx=20, pady=16)
        colors_content.pack(fill='x')
        
        bg_color_var = tk.StringVar(value=config.get('bg_color', '#FFFFFF'))
        text_color_var = tk.StringVar(value=config.get('text_color', '#000000'))
        
        # Background color
        bg_frame = tk.Frame(colors_content, bg='#FFFFFF')
        bg_frame.pack(fill='x', pady=4)
        tk.Label(bg_frame, text="Background Color:", font=("Segoe UI", 10), bg='#FFFFFF', fg='#1C1B1F').pack(side='left')
        bg_preview = tk.Frame(bg_frame, width=30, height=20, bg=bg_color_var.get(), relief='solid', bd=1)
        bg_preview.pack(side='right', padx=(5, 0))
        ModernButton(bg_frame, text="Choose", command=lambda: self.choose_color_modern(bg_color_var, bg_preview), style="outlined").pack(side='right', padx=(10, 5))
        
        # Text color
        text_frame = tk.Frame(colors_content, bg='#FFFFFF')
        text_frame.pack(fill='x', pady=4)
        tk.Label(text_frame, text="Text Color:", font=("Segoe UI", 10), bg='#FFFFFF', fg='#1C1B1F').pack(side='left')
        text_preview = tk.Frame(text_frame, width=30, height=20, bg=text_color_var.get(), relief='solid', bd=1)
        text_preview.pack(side='right', padx=(5, 0))
        ModernButton(text_frame, text="Choose", command=lambda: self.choose_color_modern(text_color_var, text_preview), style="outlined").pack(side='right', padx=(10, 5))
        
        # Font settings card
        font_card = ModernCard(scrollable_frame, title="Typography")
        font_card.pack(fill='x', pady=(0, 16))
        
        font_content = tk.Frame(font_card, bg='#FFFFFF', padx=20, pady=16)
        font_content.pack(fill='x')
        
        # Font family
        family_frame = tk.Frame(font_content, bg='#FFFFFF')
        family_frame.pack(fill='x', pady=4)
        tk.Label(family_frame, text="Font Family:", font=("Segoe UI", 10), bg='#FFFFFF', fg='#1C1B1F').pack(side='left')
        font_family_var = tk.StringVar(value=config.get('font_family', 'Segoe UI'))
        font_combo = ttk.Combobox(family_frame, textvariable=font_family_var, values=['Segoe UI', 'Arial', 'Helvetica', 'Times New Roman', 'Courier New'])
        font_combo.pack(side='right', padx=(10, 0))
        
        # Font size
        size_frame = tk.Frame(font_content, bg='#FFFFFF')
        size_frame.pack(fill='x', pady=4)
        tk.Label(size_frame, text="Font Size:", font=("Segoe UI", 10), bg='#FFFFFF', fg='#1C1B1F').pack(side='left')
        font_size_var = tk.StringVar(value=str(config.get('font_size', 12)))
        size_entry = tk.Entry(size_frame, textvariable=font_size_var, font=("Segoe UI", 10), bg='#F7F2FA', relief='flat', bd=5)
        size_entry.pack(side='right', padx=(10, 0))
        
        # Opacity card
        opacity_card = ModernCard(scrollable_frame, title="Transparency")
        opacity_card.pack(fill='x', pady=(0, 16))
        
        opacity_content = tk.Frame(opacity_card, bg='#FFFFFF', padx=20, pady=16)
        opacity_content.pack(fill='x')
        
        opacity_var = tk.DoubleVar(value=config.get('opacity', 1.0))
        tk.Label(opacity_content, text="Opacity:", font=("Segoe UI", 10), bg='#FFFFFF', fg='#1C1B1F').pack(anchor='w')
        opacity_scale = tk.Scale(
            opacity_content,
            from_=0.1,
            to=1.0,
            resolution=0.1,
            variable=opacity_var,
            orient='horizontal',
            bg='#FFFFFF',
            fg='#6750A4',
            troughcolor='#E8DEF8',
            highlightthickness=0,
            relief='flat'
        )
        opacity_scale.pack(fill='x', pady=(8, 0))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bottom buttons
        button_frame = tk.Frame(main_frame, bg='#F5F5F5')
        button_frame.pack(fill='x', pady=(20, 0))
        
        def apply_changes():
            try:
                # Update configuration
                old_config = config.copy()
                config['width'] = int(width_var.get())
                config['height'] = int(height_var.get())
                config['bg_color'] = bg_color_var.get()
                config['text_color'] = text_color_var.get()
                config['font_family'] = font_family_var.get()
                config['font_size'] = int(font_size_var.get())
                config['opacity'] = opacity_var.get()
                
                # Update desktop widget if pinned
                if widget_info['desktop_widget'] and widget_info['desktop_widget'].is_pinned:
                    # Store position
                    old_x = widget_info['desktop_widget'].x
                    old_y = widget_info['desktop_widget'].y
                    
                    # Unpin and re-pin with new configuration
                    widget_info['desktop_widget'].unpin_from_desktop()
                    widget_info['desktop_widget'] = DesktopWidget(widget_info['instance'], old_x, old_y)
                    widget_info['desktop_widget'].pin_to_desktop()
                
                # Update preview if open
                if hasattr(self, 'preview_canvas') and self.preview_canvas:
                    self.refresh_preview()
                
                self.show_success_message("Widget customization applied successfully!")
                dialog.destroy()
            except ValueError as e:
                self.show_error_message(f"Invalid input: {e}")
        
        def preview_changes():
            """Live preview of changes"""
            try:
                # Create temporary config
                temp_config = config.copy()
                temp_config.update({
                    'width': int(width_var.get()),
                    'height': int(height_var.get()),
                    'bg_color': bg_color_var.get(),
                    'text_color': text_color_var.get(),
                    'font_family': font_family_var.get(),
                    'font_size': int(font_size_var.get()),
                    'opacity': opacity_var.get()
                })
                
                # Update desktop widget temporarily for preview
                if widget_info['desktop_widget'] and widget_info['desktop_widget'].is_pinned:
                    widget_info['instance'].config = temp_config
                    # Store position
                    old_x = widget_info['desktop_widget'].x
                    old_y = widget_info['desktop_widget'].y
                    
                    # Re-create with new config
                    widget_info['desktop_widget'].unpin_from_desktop()
                    widget_info['desktop_widget'] = DesktopWidget(widget_info['instance'], old_x, old_y)
                    widget_info['desktop_widget'].pin_to_desktop()
            except ValueError:
                pass  # Ignore invalid inputs during preview
        
        # Add live preview bindings
        for var in [width_var, height_var, font_size_var]:
            var.trace('w', lambda *args: self.root.after(500, preview_changes))
        
        for var in [bg_color_var, text_color_var, font_family_var]:
            var.trace('w', lambda *args: self.root.after(100, preview_changes))
        
        opacity_var.trace('w', lambda *args: self.root.after(100, preview_changes))
        
        ModernButton(button_frame, text="Cancel", command=dialog.destroy, style="outlined").pack(side='right', padx=(8, 0))
        ModernButton(button_frame, text="Apply Changes", command=apply_changes, style="filled").pack(side='right')
    
    def choose_color_modern(self, color_var, preview_widget):
        """Modern color chooser with preview"""
        color = colorchooser.askcolor(color=color_var.get(), title="Choose Color")
        if color[1]:
            color_var.set(color[1])
            preview_widget.configure(bg=color[1])
    
    def open_desktop_preview(self):
        """Open interactive preview window with real-time positioning"""
        if self.preview_window and self.preview_window.winfo_exists():
            self.preview_window.lift()
            return
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.title("Interactive Desktop Preview")
        self.preview_window.geometry(f"{int(screen_width*0.9)}x{int(screen_height*0.9)}")
        self.preview_window.configure(bg='#1E1E1E')
        
        # Make preview window stay on top during positioning
        self.preview_window.wm_attributes("-topmost", True)
        
        # Main frame
        main_frame = tk.Frame(self.preview_window, bg='#1E1E1E')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Header with controls
        header = tk.Frame(main_frame, bg='#1E1E1E')
        header.pack(fill='x', pady=(0, 10))
        
        title = tk.Label(
            header,
            text="Interactive Desktop Preview",
            font=("Segoe UI", 16, "bold"),
            bg='#1E1E1E',
            fg='#FFFFFF'
        )
        title.pack(side='left')
        
        # Control buttons
        controls_frame = tk.Frame(header, bg='#1E1E1E')
        controls_frame.pack(side='right')
        
        ModernButton(
            controls_frame,
            text="Apply Positions",
            command=self.apply_preview_positions,
            style="filled"
        ).pack(side='right', padx=(8, 0))
        
        ModernButton(
            controls_frame,
            text="Reset Positions",
            command=self.reset_preview_positions,
            style="outlined"
        ).pack(side='right', padx=(8, 0))
        
        info_label = tk.Label(
            header,
            text="Drag widgets to position them. Changes apply in real-time to desktop.",
            font=("Segoe UI", 9),
            bg='#1E1E1E',
            fg='#B3B3B3'
        )
        info_label.pack(side='left', padx=(20, 0))
        
        # Desktop simulation canvas with real proportions
        canvas_frame = tk.Frame(main_frame, bg='#1E1E1E', relief='solid', bd=1)
        canvas_frame.pack(fill='both', expand=True)
        
        self.preview_canvas = tk.Canvas(
            canvas_frame,
            bg='#2D2D2D',
            highlightthickness=0,
            relief='flat'
        )
        self.preview_canvas.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Store canvas dimensions and scaling
        self.preview_canvas.update()
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        # Calculate scaling factor
        self.scale_x = canvas_width / screen_width
        self.scale_y = canvas_height / screen_height
        
        # Draw desktop elements
        self.draw_desktop_simulation()
        
        # Add interactive widgets
        self.preview_widget_items = {}
        self.add_interactive_widgets()
        
        # Bind canvas events for widget interaction
        self.preview_canvas.bind("<Button-1>", self.on_preview_click)
        self.preview_canvas.bind("<B1-Motion>", self.on_preview_drag)
        self.preview_canvas.bind("<ButtonRelease-1>", self.on_preview_release)
        
        self.dragging_widget = None
        self.drag_start_x = 0
        self.drag_start_y = 0
    
    def draw_desktop_simulation(self):
        """Draw realistic desktop simulation"""
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        # Clear canvas
        self.preview_canvas.delete("desktop_element")
        
        # Draw subtle grid
        for i in range(0, canvas_width, int(50 * self.scale_x)):
            self.preview_canvas.create_line(
                i, 0, i, canvas_height, 
                fill='#3A3A3A', width=1, dash=(1, 4), tags="desktop_element"
            )
        for i in range(0, canvas_height, int(50 * self.scale_y)):
            self.preview_canvas.create_line(
                0, i, canvas_width, i, 
                fill='#3A3A3A', width=1, dash=(1, 4), tags="desktop_element"
            )
        
        # Simulate desktop icons (scaled)
        icon_size = int(50 * min(self.scale_x, self.scale_y))
        margin = int(20 * min(self.scale_x, self.scale_y))
        
        # My Computer
        self.preview_canvas.create_rectangle(
            margin, margin, 
            margin + icon_size, margin + icon_size,
            fill='#404040', outline='#666666', tags="desktop_element"
        )
        self.preview_canvas.create_text(
            margin + icon_size//2, margin + icon_size + 10,
            text="My Computer", fill='#FFFFFF', 
            font=("Segoe UI", int(8 * min(self.scale_x, self.scale_y))), tags="desktop_element"
        )
        
        # Recycle Bin
        self.preview_canvas.create_rectangle(
            margin, margin + icon_size + 30,
            margin + icon_size, margin + 2*icon_size + 30,
            fill='#404040', outline='#666666', tags="desktop_element"
        )
        self.preview_canvas.create_text(
            margin + icon_size//2, margin + 2*icon_size + 40,
            text="Recycle Bin", fill='#FFFFFF',
            font=("Segoe UI", int(8 * min(self.scale_x, self.scale_y))), tags="desktop_element"
        )
        
        # Taskbar
        taskbar_height = int(40 * self.scale_y)
        self.preview_canvas.create_rectangle(
            0, canvas_height - taskbar_height,
            canvas_width, canvas_height,
            fill='#1F1F1F', outline='#333333', tags="desktop_element"
        )
        
        # Start button
        self.preview_canvas.create_text(
            int(50 * self.scale_x), canvas_height - taskbar_height//2,
            text="⊞ Start", fill='#FFFFFF',
            font=("Segoe UI", int(10 * min(self.scale_x, self.scale_y))), tags="desktop_element"
        )
        
        # System tray area
        self.preview_canvas.create_text(
            canvas_width - int(100 * self.scale_x), canvas_height - taskbar_height//2,
            text="🔊 📶 🔋 12:34 PM", fill='#FFFFFF',
            font=("Segoe UI", int(8 * min(self.scale_x, self.scale_y))), tags="desktop_element"
        )
    
    def add_interactive_widgets(self):
        """Add interactive widget representations"""
        for i, widget_info in enumerate(self.active_widgets):
            # Get current position or default
            if widget_info['desktop_widget'] and widget_info['desktop_widget'].is_pinned:
                real_x = widget_info['desktop_widget'].x
                real_y = widget_info['desktop_widget'].y
            else:
                real_x = 200 + i * 50
                real_y = 150 + i * 50
            
            # Convert to canvas coordinates
            canvas_x = int(real_x * self.scale_x)
            canvas_y = int(real_y * self.scale_y)
            
            # Get widget dimensions (scaled)
            widget_width = int(widget_info['instance'].config.get('width', 200) * self.scale_x)
            widget_height = int(widget_info['instance'].config.get('height', 100) * self.scale_y)
            
            # Create widget representation
            widget_bg = widget_info['instance'].config.get('bg_color', '#FFFFFF')
            
            # Widget background
            rect_id = self.preview_canvas.create_rectangle(
                canvas_x, canvas_y,
                canvas_x + widget_width, canvas_y + widget_height,
                fill=widget_bg,
                outline='#6750A4',
                width=2,
                tags=f"widget_{i}"
            )
            
            # Widget title
            text_id = self.preview_canvas.create_text(
                canvas_x + widget_width//2, canvas_y + 15,
                text=widget_info['name'],
                fill=widget_info['instance'].config.get('text_color', '#000000'),
                font=("Segoe UI", int(9 * min(self.scale_x, self.scale_y)), "bold"),
                tags=f"widget_{i}"
            )
            
            # Widget type indicator
            type_id = self.preview_canvas.create_text(
                canvas_x + widget_width//2, canvas_y + widget_height//2,
                text=widget_info['type'],
                fill=widget_info['instance'].config.get('text_color', '#000000'),
                font=("Segoe UI", int(8 * min(self.scale_x, self.scale_y))),
                tags=f"widget_{i}"
            )
            
            # Store widget info
            self.preview_widget_items[i] = {
                'rect': rect_id,
                'text': text_id,
                'type': type_id,
                'real_x': real_x,
                'real_y': real_y,
                'widget_info': widget_info
            }
    
    def on_preview_click(self, event):
        """Handle click on preview canvas"""
        # Find clicked widget
        clicked_item = self.preview_canvas.find_closest(event.x, event.y)[0]
        
        for i, item_data in self.preview_widget_items.items():
            if clicked_item in [item_data['rect'], item_data['text'], item_data['type']]:
                self.dragging_widget = i
                self.drag_start_x = event.x
                self.drag_start_y = event.y
                
                # Highlight selected widget
                self.preview_canvas.itemconfig(item_data['rect'], outline='#FF5722', width=3)
                break
    
    def on_preview_drag(self, event):
        """Handle dragging in preview"""
        if self.dragging_widget is not None:
            # Calculate movement
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            # Move widget items
            item_data = self.preview_widget_items[self.dragging_widget]
            self.preview_canvas.move(item_data['rect'], dx, dy)
            self.preview_canvas.move(item_data['text'], dx, dy)
            self.preview_canvas.move(item_data['type'], dx, dy)
            
            # Update real coordinates
            item_data['real_x'] += dx / self.scale_x
            item_data['real_y'] += dy / self.scale_y
            
            # Update actual desktop widget position in real-time
            widget_info = item_data['widget_info']
            if widget_info['desktop_widget'] and widget_info['desktop_widget'].is_pinned:
                new_x = int(item_data['real_x'])
                new_y = int(item_data['real_y'])
                widget_info['desktop_widget'].desktop_window.geometry(f"+{new_x}+{new_y}")
                widget_info['desktop_widget'].x = new_x
                widget_info['desktop_widget'].y = new_y
            
            # Update drag start position
            self.drag_start_x = event.x
            self.drag_start_y = event.y
    
    def on_preview_release(self, event):
        """Handle release after dragging"""
        if self.dragging_widget is not None:
            # Reset highlight
            item_data = self.preview_widget_items[self.dragging_widget]
            self.preview_canvas.itemconfig(item_data['rect'], outline='#6750A4', width=2)
            
            self.dragging_widget = None
    
    def apply_preview_positions(self):
        """Apply current preview positions to desktop widgets"""
        applied_count = 0
        for item_data in self.preview_widget_items.values():
            widget_info = item_data['widget_info']
            if widget_info['desktop_widget'] and widget_info['desktop_widget'].is_pinned:
                new_x = int(item_data['real_x'])
                new_y = int(item_data['real_y'])
                widget_info['desktop_widget'].x = new_x
                widget_info['desktop_widget'].y = new_y
                widget_info['desktop_widget'].desktop_window.geometry(f"+{new_x}+{new_y}")
                applied_count += 1
        
        self.show_success_message(f"Applied positions to {applied_count} desktop widgets!")
    
    def reset_preview_positions(self):
        """Reset widget positions to default"""
        for i, item_data in self.preview_widget_items.items():
            # Default positions
            default_x = 200 + i * 50
            default_y = 150 + i * 50
            
            # Update preview
            canvas_x = int(default_x * self.scale_x)
            canvas_y = int(default_y * self.scale_y)
            
            # Get current position
            current_coords = self.preview_canvas.coords(item_data['rect'])
            dx = canvas_x - current_coords[0]
            dy = canvas_y - current_coords[1]
            
            # Move items
            self.preview_canvas.move(item_data['rect'], dx, dy)
            self.preview_canvas.move(item_data['text'], dx, dy)
            self.preview_canvas.move(item_data['type'], dx, dy)
            
            # Update real coordinates
            item_data['real_x'] = default_x
            item_data['real_y'] = default_y
            
            # Update desktop widget
            widget_info = item_data['widget_info']
            if widget_info['desktop_widget'] and widget_info['desktop_widget'].is_pinned:
                widget_info['desktop_widget'].desktop_window.geometry(f"+{default_x}+{default_y}")
                widget_info['desktop_widget'].x = default_x
                widget_info['desktop_widget'].y = default_y
        
        self.show_success_message("Widget positions reset to default!")
    
    def refresh_preview(self):
        """Refresh preview window with updated widgets"""
        if hasattr(self, 'preview_canvas') and self.preview_canvas:
            # Clear existing widgets
            for i in range(len(self.active_widgets)):
                self.preview_canvas.delete(f"widget_{i}")
            
            # Re-add widgets
            self.add_interactive_widgets()
    
    def update_widgets_list(self):
        """Update the modern widgets listbox"""
        self.widgets_listbox.delete(0, 'end')
        for i, widget_info in enumerate(self.active_widgets):
            status = " 📌" if widget_info['desktop_widget'] and widget_info['desktop_widget'].is_pinned else ""
            display_text = f"{widget_info['name']}{status}"
            self.widgets_listbox.insert('end', display_text)
    
    def save_config(self):
        """Save current configuration to file"""
        config_data = {
            'widgets': [],
            'desktop_positions': {}
        }
        
        for i, widget_info in enumerate(self.active_widgets):
            widget_config = {
                'type': widget_info['type'],
                'name': widget_info['name'],
                'config': widget_info['instance'].config
            }
            
            # Save desktop position if pinned
            if widget_info['desktop_widget'] and widget_info['desktop_widget'].is_pinned:
                widget_config['desktop_x'] = widget_info['desktop_widget'].x
                widget_config['desktop_y'] = widget_info['desktop_widget'].y
                widget_config['pinned'] = True
            
            config_data['widgets'].append(widget_config)
        
        try:
            with open('modern_widget_config.json', 'w') as f:
                json.dump(config_data, f, indent=2)
            self.show_success_message("Layout saved successfully!")
        except Exception as e:
            self.show_error_message(f"Failed to save layout: {e}")
    
    def load_config(self):
        """Load configuration from file"""
        if not os.path.exists('modern_widget_config.json'):
            return
        
        try:
            with open('modern_widget_config.json', 'r') as f:
                config_data = json.load(f)
            
            # Clear existing widgets
            for widget_info in self.active_widgets:
                if widget_info['desktop_widget'] and widget_info['desktop_widget'].is_pinned:
                    widget_info['desktop_widget'].unpin_from_desktop()
            
            self.active_widgets = []
            self.desktop_widgets = []
            
            # Load widgets
            for widget_data in config_data.get('widgets', []):
                widget_type = widget_data['type']
                if widget_type in self.widget_types:
                    widget_class = self.widget_types[widget_type]
                    widget_instance = widget_class(self.root, widget_data['config'])
                    
                    widget_info = {
                        'type': widget_type,
                        'instance': widget_instance,
                        'name': widget_data['name'],
                        'desktop_widget': None
                    }
                    
                    self.active_widgets.append(widget_info)
                    
                    # Restore desktop pinning if it was pinned
                    if widget_data.get('pinned', False):
                        x = widget_data.get('desktop_x', 100)
                        y = widget_data.get('desktop_y', 100)
                        desktop_widget = DesktopWidget(widget_instance, x, y)
                        desktop_widget.pin_to_desktop()
                        widget_info['desktop_widget'] = desktop_widget
                        self.desktop_widgets.append(desktop_widget)
            
            self.update_widgets_list()
            self.show_success_message("Layout loaded successfully!")
        except Exception as e:
            self.show_error_message(f"Failed to load layout: {e}")
    
    def show_success_message(self, message):
        """Show modern success message"""
        self._show_toast(message, "success")
    
    def show_error_message(self, message):
        """Show modern error message"""
        self._show_toast(message, "error")
    
    def show_warning_message(self, message):
        """Show modern warning message"""
        self._show_toast(message, "warning")
    
    def show_info_message(self, message):
        """Show modern info message"""
        self._show_toast(message, "info")
    
    def _show_toast(self, message, toast_type):
        """Show modern toast notification"""
        colors = {
            "success": {"bg": "#4CAF50", "fg": "#FFFFFF"},
            "error": {"bg": "#F44336", "fg": "#FFFFFF"},
            "warning": {"bg": "#FF9800", "fg": "#FFFFFF"},
            "info": {"bg": "#2196F3", "fg": "#FFFFFF"}
        }
        
        color_scheme = colors.get(toast_type, colors["info"])
        
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.configure(bg=color_scheme["bg"])
        
        # Position at top-right of main window
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        toast.geometry(f"300x60+{main_x + 400}+{main_y + 50}")
        
        # Toast content
        toast_frame = tk.Frame(toast, bg=color_scheme["bg"], padx=16, pady=12)
        toast_frame.pack(fill='both', expand=True)
        
        message_label = tk.Label(
            toast_frame,
            text=message,
            bg=color_scheme["bg"],
            fg=color_scheme["fg"],
            font=("Segoe UI", 10),
            wraplength=250
        )
        message_label.pack()
        
        # Auto-close after 3 seconds
        toast.after(3000, toast.destroy)
        
        # Make it fade-in effect
        toast.attributes('-alpha', 0.0)
        for i in range(1, 11):
            toast.attributes('-alpha', i/10.0)
            toast.update()
            time.sleep(0.02)
    
    def run(self):
        """Start the modern application"""
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = WidgetManager()
        app.run()
    except ImportError as e:
        print(f"Missing required module: {e}")
        print("Please install required modules: pip install pillow pywin32")
        messagebox.showerror("Missing Dependencies", 
                           "Required modules missing.\nPlease install: pip install pillow pywin32")