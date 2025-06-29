#!/usr/bin/env python3
"""
ModSlayer - Lightweight Mod Manager for PC Games
A simple mod manager that allows users to load, delete, and manage mod load order.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
import configparser
import subprocess
import time


class ModManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ModSlayer - Lightweight Mod Manager")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Configuration
        self.config_file = "modslayer_config.ini"
        self.mods_file = "mods_data.json"
        self.game_path = ""
        self.mods_folder = ""
        self.mods_data = []
        
        # File navigation improvements
        self.recent_paths = {'game': [], 'mods': [], 'files': []}
        self.favorites = {'game': [], 'mods': []}
        self.max_recent_items = 10
        
        self.load_config()
        self.setup_ui()
        self.load_mods_data()
        self.refresh_mod_list()
        
    def load_config(self):
        """Load configuration from INI file"""
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            self.game_path = config.get('Settings', 'game_path', fallback='')
            self.mods_folder = config.get('Settings', 'mods_folder', fallback='')
            
            # Load recent paths and favorites
            if config.has_section('RecentPaths'):
                for key in ['game', 'mods', 'files']:
                    paths_str = config.get('RecentPaths', f'{key}_paths', fallback='')
                    if paths_str:
                        self.recent_paths[key] = [p.strip() for p in paths_str.split('|') if p.strip()]
            
            if config.has_section('Favorites'):
                for key in ['game', 'mods']:
                    favorites_str = config.get('Favorites', f'{key}_favorites', fallback='')
                    if favorites_str:
                        self.favorites[key] = [p.strip() for p in favorites_str.split('|') if p.strip()]
    
    def save_config(self):
        """Save configuration to INI file"""
        config = configparser.ConfigParser()
        config['Settings'] = {
            'game_path': self.game_path,
            'mods_folder': self.mods_folder
        }
        
        # Save recent paths
        config['RecentPaths'] = {}
        for key, paths in self.recent_paths.items():
            config['RecentPaths'][f'{key}_paths'] = '|'.join(paths[:self.max_recent_items])
        
        # Save favorites
        config['Favorites'] = {}
        for key, favorites in self.favorites.items():
            config['Favorites'][f'{key}_favorites'] = '|'.join(favorites)
        
        with open(self.config_file, 'w') as f:
            config.write(f)
    
    def load_mods_data(self):
        """Load mods data from JSON file"""
        if os.path.exists(self.mods_file):
            try:
                with open(self.mods_file, 'r') as f:
                    self.mods_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.mods_data = []
        else:
            self.mods_data = []
    
    def save_mods_data(self):
        """Save mods data to JSON file"""
        with open(self.mods_file, 'w') as f:
            json.dump(self.mods_data, f, indent=2)
    
    def add_to_recent_paths(self, path_type: str, path: str):
        """Add a path to recent paths list"""
        if path and os.path.exists(path):
            # Remove if already exists to avoid duplicates
            if path in self.recent_paths[path_type]:
                self.recent_paths[path_type].remove(path)
            # Add to beginning of list
            self.recent_paths[path_type].insert(0, path)
            # Keep only max_recent_items
            self.recent_paths[path_type] = self.recent_paths[path_type][:self.max_recent_items]
            self.save_config()
    
    def create_enhanced_file_dialog(self, dialog_type: str, title: str, path_type: str, 
                                   file_types=None, initial_dir=None):
        """Create an enhanced file dialog with recent paths and favorites"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("700x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Result variable
        result = {'path': None}
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Quick access frame
        quick_frame = ttk.LabelFrame(main_frame, text="Quick Access", padding="5")
        quick_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        quick_frame.columnconfigure(1, weight=1)
        
        # Recent paths
        if self.recent_paths.get(path_type):
            ttk.Label(quick_frame, text="Recent:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
            recent_combo = ttk.Combobox(quick_frame, values=self.recent_paths[path_type], state="readonly")
            recent_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
            ttk.Button(quick_frame, text="Go", 
                      command=lambda: self.navigate_to_path(recent_combo.get(), path_var, tree)).grid(row=0, column=2)
        
        # Favorites
        fav_frame = ttk.Frame(quick_frame)
        fav_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        fav_frame.columnconfigure(1, weight=1)
        
        ttk.Label(fav_frame, text="Favorites:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        favorites_list = self.favorites.get(path_type, [])
        if favorites_list:
            fav_combo = ttk.Combobox(fav_frame, values=favorites_list, state="readonly")
            fav_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
            ttk.Button(fav_frame, text="Go", 
                      command=lambda: self.navigate_to_path(fav_combo.get(), path_var, tree)).grid(row=0, column=2, padx=(0, 5))
        
        # Current path frame
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        path_frame.columnconfigure(1, weight=1)
        
        ttk.Label(path_frame, text="Current Path:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        path_var = tk.StringVar(value=initial_dir or os.path.expanduser("~"))
        path_entry = ttk.Entry(path_frame, textvariable=path_var)
        path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        path_entry.bind('<Return>', lambda e: self.navigate_to_path(path_var.get(), path_var, tree))
        
        ttk.Button(path_frame, text="Up", 
                  command=lambda: self.navigate_up(path_var, tree)).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(path_frame, text="Home", 
                  command=lambda: self.navigate_to_path(os.path.expanduser("~"), path_var, tree)).grid(row=0, column=3, padx=(0, 5))
        ttk.Button(path_frame, text="Refresh", 
                  command=lambda: self.navigate_to_path(path_var.get(), path_var, tree)).grid(row=0, column=4)
        
        # File browser tree
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        tree = ttk.Treeview(tree_frame, columns=('size', 'modified'), show='tree headings')
        tree.heading('#0', text='Name')
        tree.heading('size', text='Size')
        tree.heading('modified', text='Modified')
        tree.column('#0', width=300)
        tree.column('size', width=100)
        tree.column('modified', width=150)
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)
        
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind double-click
        if dialog_type == 'folder':
            tree.bind('<Double-1>', lambda e: self.on_tree_double_click(tree, path_var, tree, dialog_type))
        else:
            tree.bind('<Double-1>', lambda e: self.on_tree_double_click(tree, path_var, tree, dialog_type, result, dialog))
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Add to favorites button
        if path_type in ['game', 'mods']:
            ttk.Button(btn_frame, text="Add to Favorites", 
                      command=lambda: self.add_to_favorites(path_type, path_var.get())).pack(side=tk.LEFT, padx=(0, 5))
        
        # Select/Cancel buttons
        ttk.Button(btn_frame, text="Cancel", 
                  command=dialog.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        
        select_text = "Select Folder" if dialog_type == 'folder' else "Select File"
        ttk.Button(btn_frame, text=select_text, 
                  command=lambda: self.confirm_selection(tree, path_var, result, dialog, dialog_type)).pack(side=tk.RIGHT)
        
        # Initialize tree
        self.navigate_to_path(path_var.get(), path_var, tree)
        
        # Center dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Wait for dialog to close
        self.root.wait_window(dialog)
        return result['path']
    
    def navigate_to_path(self, path: str, path_var: tk.StringVar, tree: ttk.Treeview):
        """Navigate to a specific path in the tree"""
        if not path or not os.path.exists(path):
            return
        
        try:
            # Clear tree
            for item in tree.get_children():
                tree.delete(item)
            
            path_var.set(path)
            
            # Add parent directory if not at root
            if path != os.path.dirname(path):
                tree.insert('', 'end', text='..', values=('', ''), tags=('folder',))
            
            # List directory contents
            items = []
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    try:
                        stat = os.stat(item_path)
                        size = self.format_size(stat.st_size) if os.path.isfile(item_path) else ''
                        modified = time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime))
                        is_dir = os.path.isdir(item_path)
                        items.append((item, size, modified, is_dir))
                    except (OSError, PermissionError):
                        # Skip items we can't access
                        continue
            except PermissionError:
                messagebox.showerror("Permission Error", f"Cannot access directory: {path}")
                return
            
            # Sort: directories first, then files
            items.sort(key=lambda x: (not x[3], x[0].lower()))
            
            # Add items to tree
            for item, size, modified, is_dir in items:
                tag = 'folder' if is_dir else 'file'
                tree.insert('', 'end', text=item, values=(size, modified), tags=(tag,))
            
            # Configure tags for visual distinction
            tree.tag_configure('folder', foreground='blue')
            tree.tag_configure('file', foreground='black')
            
        except Exception as e:
            messagebox.showerror("Error", f"Error navigating to path: {str(e)}")
    
    def navigate_up(self, path_var: tk.StringVar, tree: ttk.Treeview):
        """Navigate to parent directory"""
        current_path = path_var.get()
        parent_path = os.path.dirname(current_path)
        if parent_path != current_path:  # Not at root
            self.navigate_to_path(parent_path, path_var, tree)
    
    def on_tree_double_click(self, tree: ttk.Treeview, path_var: tk.StringVar, tree_widget: ttk.Treeview, 
                           dialog_type: str, result=None, dialog=None):
        """Handle double-click on tree item"""
        selection = tree.selection()
        if not selection:
            return
        
        item = selection[0]
        item_text = tree.item(item)['text']
        current_path = path_var.get()
        
        if item_text == '..':
            # Go to parent directory
            self.navigate_up(path_var, tree_widget)
        else:
            item_path = os.path.join(current_path, item_text)
            if os.path.isdir(item_path):
                # Navigate to directory
                self.navigate_to_path(item_path, path_var, tree_widget)
            elif dialog_type == 'file' and result and dialog:
                # Select file and close dialog
                result['path'] = item_path
                dialog.destroy()
    
    def confirm_selection(self, tree: ttk.Treeview, path_var: tk.StringVar, result: dict, 
                         dialog: tk.Toplevel, dialog_type: str):
        """Confirm the current selection"""
        if dialog_type == 'folder':
            result['path'] = path_var.get()
        else:
            # For file selection, check if a file is selected
            selection = tree.selection()
            if selection:
                item = selection[0]
                item_text = tree.item(item)['text']
                if item_text != '..':
                    item_path = os.path.join(path_var.get(), item_text)
                    if os.path.isfile(item_path):
                        result['path'] = item_path
                    else:
                        messagebox.showwarning("Warning", "Please select a file!")
                        return
            else:
                messagebox.showwarning("Warning", "Please select a file!")
                return
        
        dialog.destroy()
    
    def add_to_favorites(self, path_type: str, path: str):
        """Add path to favorites"""
        if path and os.path.exists(path) and path not in self.favorites[path_type]:
            self.favorites[path_type].append(path)
            self.save_config()
            messagebox.showinfo("Success", f"Added to {path_type} favorites!")
    
    def format_size(self, size: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def manage_paths(self):
        """Open path management dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Manage Paths - Recent & Favorites")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        ttk.Label(main_frame, text="Path Management", 
                 font=('Arial', 14, 'bold')).grid(row=0, column=0, pady=(0, 10))
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Recent paths tab
        recent_frame = ttk.Frame(notebook, padding="10")
        notebook.add(recent_frame, text="Recent Paths")
        
        ttk.Label(recent_frame, text="Recent Paths", 
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Recent paths lists
        for i, (path_type, paths) in enumerate(self.recent_paths.items()):
            if paths:
                ttk.Label(recent_frame, text=f"{path_type.title()}:").grid(
                    row=i+1, column=0, sticky=tk.W, pady=(5, 0))
                
                listbox = tk.Listbox(recent_frame, height=4)
                listbox.grid(row=i+1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(5, 0))
                recent_frame.columnconfigure(1, weight=1)
                
                for path in paths:
                    listbox.insert(tk.END, path)
                
                # Clear button
                ttk.Button(recent_frame, text=f"Clear {path_type.title()}", 
                          command=lambda pt=path_type: self.clear_recent_paths(pt, dialog)).grid(
                    row=i+1, column=2, padx=(5, 0), pady=(5, 0))
        
        # Favorites tab
        fav_frame = ttk.Frame(notebook, padding="10")
        notebook.add(fav_frame, text="Favorites")
        
        ttk.Label(fav_frame, text="Favorite Paths", 
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Favorites lists
        self.fav_listboxes = {}
        for i, (path_type, favorites) in enumerate(self.favorites.items()):
            ttk.Label(fav_frame, text=f"{path_type.title()}:").grid(
                row=i+1, column=0, sticky=tk.W, pady=(5, 0))
            
            listbox = tk.Listbox(fav_frame, height=4)
            listbox.grid(row=i+1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(5, 0))
            fav_frame.columnconfigure(1, weight=1)
            self.fav_listboxes[path_type] = listbox
            
            for favorite in favorites:
                listbox.insert(tk.END, favorite)
            
            # Remove button
            ttk.Button(fav_frame, text="Remove", 
                      command=lambda pt=path_type: self.remove_favorite(pt, dialog)).grid(
                row=i+1, column=2, padx=(5, 0), pady=(5, 0))
        
        # Close button
        ttk.Button(main_frame, text="Close", command=dialog.destroy).grid(
            row=2, column=0, pady=(10, 0))
        
        # Center dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def clear_recent_paths(self, path_type: str, dialog: tk.Toplevel):
        """Clear recent paths for a specific type"""
        if messagebox.askyesno("Confirm", f"Clear all recent {path_type} paths?"):
            self.recent_paths[path_type] = []
            self.save_config()
            dialog.destroy()
            self.manage_paths()  # Refresh the dialog
    
    def remove_favorite(self, path_type: str, dialog: tk.Toplevel):
        """Remove selected favorite"""
        listbox = self.fav_listboxes[path_type]
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            self.favorites[path_type].pop(index)
            self.save_config()
            listbox.delete(index)
        else:
            messagebox.showwarning("Warning", f"Please select a {path_type} favorite to remove!")
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="ModSlayer - Lightweight Mod Manager", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Game path selection
        path_frame = ttk.LabelFrame(main_frame, text="Game Configuration", padding="10")
        path_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        path_frame.columnconfigure(1, weight=1)
        
        ttk.Label(path_frame, text="Game Path:").grid(row=0, column=0, sticky=tk.W)
        self.game_path_var = tk.StringVar(value=self.game_path)
        ttk.Entry(path_frame, textvariable=self.game_path_var, state="readonly").grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        ttk.Button(path_frame, text="Browse", command=self.select_game_path).grid(
            row=0, column=2, padx=(5, 0))
        
        ttk.Label(path_frame, text="Mods Folder:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.mods_folder_var = tk.StringVar(value=self.mods_folder)
        ttk.Entry(path_frame, textvariable=self.mods_folder_var, state="readonly").grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=(5, 0))
        ttk.Button(path_frame, text="Browse", command=self.select_mods_folder).grid(
            row=1, column=2, padx=(5, 0), pady=(5, 0))
        
        # Mod list frame
        list_frame = ttk.LabelFrame(main_frame, text="Installed Mods", padding="10")
        list_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview for mod list
        columns = ('name', 'status', 'priority')
        self.mod_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=15)
        
        # Define headings
        self.mod_tree.heading('#0', text='Mod Name')
        self.mod_tree.heading('name', text='File/Folder')
        self.mod_tree.heading('status', text='Status')
        self.mod_tree.heading('priority', text='Load Order')
        
        # Define column widths
        self.mod_tree.column('#0', width=200)
        self.mod_tree.column('name', width=200)
        self.mod_tree.column('status', width=100)
        self.mod_tree.column('priority', width=100)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.mod_tree.yview)
        self.mod_tree.configure(yscrollcommand=scrollbar.set)
        
        self.mod_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=2, sticky=(tk.N, tk.S), padx=(10, 0))
        
        # Buttons
        ttk.Button(buttons_frame, text="Add Mod", command=self.add_mod).grid(
            row=0, column=0, pady=(0, 5), sticky=(tk.W, tk.E))
        ttk.Button(buttons_frame, text="Remove Mod", command=self.remove_mod).grid(
            row=1, column=0, pady=(0, 5), sticky=(tk.W, tk.E))
        ttk.Button(buttons_frame, text="Enable/Disable", command=self.toggle_mod).grid(
            row=2, column=0, pady=(0, 5), sticky=(tk.W, tk.E))
        
        ttk.Separator(buttons_frame, orient='horizontal').grid(
            row=3, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(buttons_frame, text="Move Up", command=self.move_mod_up).grid(
            row=4, column=0, pady=(0, 5), sticky=(tk.W, tk.E))
        ttk.Button(buttons_frame, text="Move Down", command=self.move_mod_down).grid(
            row=5, column=0, pady=(0, 5), sticky=(tk.W, tk.E))
        
        ttk.Separator(buttons_frame, orient='horizontal').grid(
            row=6, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(buttons_frame, text="Refresh", command=self.refresh_mod_list).grid(
            row=7, column=0, pady=(0, 5), sticky=(tk.W, tk.E))
        
        ttk.Button(buttons_frame, text="Manage Paths", command=self.manage_paths).grid(
            row=8, column=0, pady=(0, 5), sticky=(tk.W, tk.E))
        
        # Launch Game button
        self.launch_btn = ttk.Button(buttons_frame, text="Launch Game", command=self.launch_game)
        self.launch_btn.grid(row=9, column=0, pady=(10, 0), sticky=(tk.W, tk.E))
        self.update_launch_button_state()
        # ...existing code...

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def update_launch_button_state(self):
        if self.game_path and os.path.exists(self.game_path):
            self.launch_btn.state(["!disabled"])
        else:
            self.launch_btn.state(["disabled"])

    def select_game_path(self):
        """Select game installation path"""
        initial_dir = self.game_path if self.game_path and os.path.exists(self.game_path) else None
        path = self.create_enhanced_file_dialog(
            'folder', 
            "Select Game Installation Folder", 
            'game',
            initial_dir=initial_dir
        )
        
        if path:
            # Use os.access to check read permissions
            if not os.access(path, os.R_OK | os.X_OK):
                messagebox.showerror("Permission Error", "Cannot access the selected directory. Please check read/execute permissions.")
                return
            self.game_path = path
            self.game_path_var.set(path)
            self.add_to_recent_paths('game', path)
            self.save_config()
            self.status_var.set(f"Game path set to: {path}")
            self.update_launch_button_state()

    def select_mods_folder(self):
        """Select mods folder"""
        initial_dir = self.mods_folder if self.mods_folder and os.path.exists(self.mods_folder) else None
        path = self.create_enhanced_file_dialog(
            'folder', 
            "Select Mods Folder", 
            'mods',
            initial_dir=initial_dir
        )
        
        if path:
            # Use os.access to check read and write permissions
            if not os.access(path, os.R_OK | os.W_OK | os.X_OK):
                messagebox.showerror("Permission Error", "Cannot write to the selected directory. Please check read/write/execute permissions.")
                return
            self.mods_folder = path
            self.mods_folder_var.set(path)
            self.add_to_recent_paths('mods', path)
            self.save_config()
            self.status_var.set(f"Mods folder set to: {path}")
    
    def add_mod(self):
        """Add a new mod"""
        if not self.mods_folder:
            messagebox.showerror("Error", "Please select a mods folder first!")
            return
        
        # Create selection dialog
        selection_dialog = tk.Toplevel(self.root)
        selection_dialog.title("Add Mod - Select Type")
        selection_dialog.geometry("400x200")
        selection_dialog.transient(self.root)
        selection_dialog.grab_set()
        
        # Center the dialog
        selection_dialog.update_idletasks()
        width = selection_dialog.winfo_width()
        height = selection_dialog.winfo_height()
        x = (selection_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (selection_dialog.winfo_screenheight() // 2) - (height // 2)
        selection_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(selection_dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        selection_dialog.columnconfigure(0, weight=1)
        selection_dialog.rowconfigure(0, weight=1)
        
        # Title
        ttk.Label(main_frame, text="What type of mod would you like to add?", 
                 font=('Arial', 12)).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Buttons
        ttk.Button(main_frame, text="📁 Mod Folder", 
                  command=lambda: self.add_mod_folder_enhanced(selection_dialog),
                  width=20).grid(row=1, column=0, padx=(0, 10), pady=(0, 10))
        
        ttk.Button(main_frame, text="📄 Mod File", 
                  command=lambda: self.add_mod_file_enhanced(selection_dialog),
                  width=20).grid(row=1, column=1, padx=(10, 0), pady=(0, 10))
        
        # Description
        desc_text = ("• Mod Folder: Select a folder containing mod files\n"
                    "• Mod File: Select individual mod files (.zip, .rar, .esp, etc.)")
        ttk.Label(main_frame, text=desc_text, font=('Arial', 9), 
                 foreground='gray').grid(row=2, column=0, columnspan=2, pady=(10, 10))
        
        # Cancel button
        ttk.Button(main_frame, text="Cancel", 
                  command=selection_dialog.destroy).grid(row=3, column=0, columnspan=2, pady=(10, 0))
    
    def add_mod_file_enhanced(self, parent_dialog=None):
        """Add a mod file using enhanced dialog"""
        if parent_dialog:
            parent_dialog.destroy()
        
        # Get recent file directory or use mods folder
        initial_dir = None
        if self.recent_paths['files']:
            initial_dir = os.path.dirname(self.recent_paths['files'][0])
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = self.mods_folder
        
        file_path = self.create_enhanced_file_dialog(
            'file',
            "Select Mod File",
            'files',
            file_types=[
                ("All Mod Files", "*.zip *.rar *.7z *.pak *.ba2 *.esp *.esm"),
                ("Archive Files", "*.zip *.rar *.7z"),
                ("Game Files", "*.pak *.ba2 *.esp *.esm"),
                ("All Files", "*.*")
            ],
            initial_dir=initial_dir
        )
        
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    f.read(1)  # Test file access
                self.add_to_recent_paths('files', file_path)
                self.install_mod_file(file_path)
            except PermissionError:
                messagebox.showerror("Permission Error", "Cannot access the selected file. Please check permissions.")
            except Exception as e:
                messagebox.showerror("Error", f"Error accessing file: {str(e)}")
    
    def add_mod_folder_enhanced(self, parent_dialog=None):
        """Add a mod folder using enhanced dialog"""
        if parent_dialog:
            parent_dialog.destroy()
        
        # Get recent folder directory or use current directory
        initial_dir = None
        if self.recent_paths['files']:
            initial_dir = os.path.dirname(self.recent_paths['files'][0])
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser("~")
        
        folder_path = self.create_enhanced_file_dialog(
            'folder',
            "Select Mod Folder",
            'files',
            initial_dir=initial_dir
        )
        
        if folder_path:
            try:
                os.listdir(folder_path)
                self.add_to_recent_paths('files', folder_path)
                self.install_mod_folder(folder_path)
            except PermissionError:
                messagebox.showerror("Permission Error", "Cannot access the selected folder. Please check permissions.")
            except Exception as e:
                messagebox.showerror("Error", f"Error accessing folder: {str(e)}")
    
    def install_mod_file(self, file_path: str):
        """Install a mod from file"""
        try:
            filename = os.path.basename(file_path)
            mod_name = os.path.splitext(filename)[0]
            
            # Create mod entry
            mod_data = {
                'id': len(self.mods_data),
                'name': mod_name,
                'file_path': filename,
                'original_path': file_path,
                'enabled': True,
                'priority': len(self.mods_data),
                'type': 'file'
            }
            
            # Copy file to mods folder
            dest_path = os.path.join(self.mods_folder, filename)
            shutil.copy2(file_path, dest_path)
            
            self.mods_data.append(mod_data)
            self.save_mods_data()
            self.refresh_mod_list()
            
            self.status_var.set(f"Mod '{mod_name}' added successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install mod: {str(e)}")
    
    def install_mod_folder(self, folder_path: str):
        """Install a mod from folder"""
        try:
            folder_name = os.path.basename(folder_path)
            
            # Create mod entry
            mod_data = {
                'id': len(self.mods_data),
                'name': folder_name,
                'file_path': folder_name,
                'original_path': folder_path,
                'enabled': True,
                'priority': len(self.mods_data),
                'type': 'folder'
            }
            
            # Copy folder to mods folder
            dest_path = os.path.join(self.mods_folder, folder_name)
            shutil.copytree(folder_path, dest_path)
            
            self.mods_data.append(mod_data)
            self.save_mods_data()
            self.refresh_mod_list()
            
            self.status_var.set(f"Mod '{folder_name}' added successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install mod: {str(e)}")
    
    def remove_mod(self):
        """Remove selected mod"""
        selection = self.mod_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a mod to remove!")
            return
        
        item = selection[0]
        mod_name = self.mod_tree.item(item)['text']
        
        # Confirm deletion
        if messagebox.askyesno("Confirm", f"Are you sure you want to remove '{mod_name}'?"):
            try:
                # Find mod in data
                mod_index = None
                for i, mod in enumerate(self.mods_data):
                    if mod['name'] == mod_name:
                        mod_index = i
                        break
                
                if mod_index is not None:
                    mod = self.mods_data[mod_index]
                    
                    # Remove file/folder from mods directory
                    mod_path = os.path.join(self.mods_folder, mod['file_path'])
                    if os.path.exists(mod_path):
                        if mod['type'] == 'folder':
                            shutil.rmtree(mod_path)
                        else:
                            os.remove(mod_path)
                    
                    # Remove from data
                    self.mods_data.pop(mod_index)
                    
                    # Update priorities
                    for i, remaining_mod in enumerate(self.mods_data):
                        remaining_mod['priority'] = i
                    
                    self.save_mods_data()
                    self.refresh_mod_list()
                    
                    self.status_var.set(f"Mod '{mod_name}' removed successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove mod: {str(e)}")
    
    def toggle_mod(self):
        """Enable/disable selected mod"""
        selection = self.mod_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a mod to enable/disable!")
            return
        
        item = selection[0]
        mod_name = self.mod_tree.item(item)['text']
        
        # Find and toggle mod
        for mod in self.mods_data:
            if mod['name'] == mod_name:
                mod['enabled'] = not mod['enabled']
                break
        
        self.save_mods_data()
        self.refresh_mod_list()
        
        status = "enabled" if mod['enabled'] else "disabled"
        self.status_var.set(f"Mod '{mod_name}' {status}!")
    
    def move_mod_up(self):
        """Move selected mod up in load order"""
        self.move_mod(-1)
    
    def move_mod_down(self):
        """Move selected mod down in load order"""
        self.move_mod(1)
    
    def move_mod(self, direction: int):
        """Move mod in load order (direction: -1 for up, 1 for down)"""
        selection = self.mod_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a mod to move!")
            return
        
        item = selection[0]
        mod_name = self.mod_tree.item(item)['text']
        
        # Find mod index
        mod_index = None
        for i, mod in enumerate(self.mods_data):
            if mod['name'] == mod_name:
                mod_index = i
                break
        
        if mod_index is not None:
            new_index = mod_index + direction
            
            # Check bounds
            if 0 <= new_index < len(self.mods_data):
                # Swap mods
                self.mods_data[mod_index], self.mods_data[new_index] = \
                    self.mods_data[new_index], self.mods_data[mod_index]
                
                # Update priorities
                for i, mod in enumerate(self.mods_data):
                    mod['priority'] = i
                
                self.save_mods_data()
                self.refresh_mod_list()
                
                # Reselect the moved mod
                for child in self.mod_tree.get_children():
                    if self.mod_tree.item(child)['text'] == mod_name:
                        self.mod_tree.selection_set(child)
                        break
                
                direction_text = "up" if direction == -1 else "down"
                self.status_var.set(f"Moved '{mod_name}' {direction_text}!")
    
    def refresh_mod_list(self):
        """Refresh the mod list display"""
        # Clear existing items
        for item in self.mod_tree.get_children():
            self.mod_tree.delete(item)
        
        # Sort mods by priority
        sorted_mods = sorted(self.mods_data, key=lambda x: x['priority'])
        
        # Add mods to tree
        for mod in sorted_mods:
            status = "Enabled" if mod['enabled'] else "Disabled"
            self.mod_tree.insert('', 'end', text=mod['name'], 
                               values=(mod['file_path'], status, mod['priority']))
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

    def launch_game(self):
        """Launch the game or emulator from the selected path"""
        if not self.game_path or not os.path.exists(self.game_path):
            messagebox.showerror("Error", "Game path is not set or does not exist!")
            return
        try:
            # Check if this might be a Steam game (look for a Steam ID in path)
            is_steam_game = False
            steam_id = None
            
            # Check for Steam Proton paths
            if "steamapps/compatdata/" in self.game_path:
                is_steam_game = True
                # Try to extract the Steam ID from path
                path_parts = self.game_path.split("steamapps/compatdata/")
                if len(path_parts) > 1:
                    steam_id_path = path_parts[1].split("/")[0]
                    if steam_id_path.isdigit():
                        steam_id = steam_id_path
            
            if is_steam_game and steam_id:
                # Ask if user wants to launch through Steam
                launch_method = messagebox.askyesno(
                    "Launch Method", 
                    "This appears to be a Steam game. Would you like to launch through Steam?\n\n"
                    "Yes: Launch through Steam (recommended for Proton games)\n"
                    "No: Launch executable directly"
                )
                
                if launch_method:
                    # Launch through Steam
                    steam_url = f"steam://rungameid/{steam_id}"
                    subprocess.Popen(["xdg-open", steam_url])
                    self.status_var.set(f"Launched Steam game with ID: {steam_id}")
                    return
            
            # Normal launch (direct executable)
            if os.path.isdir(self.game_path):
                # Try to find an executable in the folder
                exes = [f for f in os.listdir(self.game_path) if f.lower().endswith(('.exe', '.AppImage', '.sh'))]
                if not exes:
                    messagebox.showerror("Error", "No executable found in the selected folder!")
                    return
                
                # If multiple executables, let user choose
                exe_file = exes[0]
                if len(exes) > 1:
                    exe_file = self.choose_executable(exes)
                    if not exe_file:
                        return  # User cancelled
                
                exe_path = os.path.join(self.game_path, exe_file)
            else:
                exe_path = self.game_path
            
            # Make sure the file is executable (especially on Linux)
            if os.name == 'posix':
                try:
                    current_mode = os.stat(exe_path).st_mode
                    os.chmod(exe_path, current_mode | 0o111)  # Add executable permission
                except Exception:
                    pass  # If this fails, we'll try anyway
            
            # Launch the executable
            subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
            self.status_var.set(f"Launched: {exe_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch game: {str(e)}")
    
    def choose_executable(self, exes):
        """Let the user choose from multiple executables"""
        # Create a simple dialog for selection
        select_window = tk.Toplevel(self.root)
        select_window.title("Select Executable")
        select_window.geometry("400x300")
        select_window.transient(self.root)
        select_window.grab_set()
        
        # Label
        tk.Label(select_window, text="Multiple executables found. Please select one:").pack(pady=10)
        
        # Create a listbox with all executables
        listbox = tk.Listbox(select_window, width=50, height=10)
        listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Add executables to the list
        for exe in exes:
            listbox.insert(tk.END, exe)
        
        # Select the first item
        listbox.select_set(0)
        
        # Variable to store the result
        result = [None]
        
        def on_ok():
            # Get selected executable
            selection = listbox.curselection()
            if selection:
                result[0] = exes[selection[0]]
            select_window.destroy()
        
        def on_cancel():
            select_window.destroy()
        
        # Buttons
        btn_frame = tk.Frame(select_window)
        btn_frame.pack(pady=10, fill=tk.X)
        
        tk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=10)
        tk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT)
        
        # Center the window
        select_window.update_idletasks()
        width = select_window.winfo_width()
        height = select_window.winfo_height()
        x = (select_window.winfo_screenwidth() // 2) - (width // 2)
        y = (select_window.winfo_screenheight() // 2) - (height // 2)
        select_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Wait for the window to be closed
        self.root.wait_window(select_window)
        
        return result[0]


if __name__ == "__main__":
    app = ModManager()
    app.run()
