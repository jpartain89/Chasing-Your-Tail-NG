#!/usr/bin/env python3
"""
CYT Setup Wizard - First-run configuration and setup
Handles all configuration questions and initial setup
"""
import json
import os
import sys
import getpass
import glob
from typing import Optional, Dict, Any

# Check if running in GUI mode
try:
    import tkinter as tk
    from tkinter import messagebox, filedialog
    HAS_TK = True
except ImportError:
    HAS_TK = False


class SetupConfig:
    """Configuration container for setup wizard"""
    
    DEFAULT_CONFIG = {
        "paths": {
            "base_dir": ".",
            "log_dir": "logs",
            "kismet_logs": "/home/*/kismet_logs/*.kismet",
            "ignore_lists": {
                "mac": "mac_list.json",
                "ssid": "ssid_list.json"
            }
        },
        "timing": {
            "check_interval": 60,
            "list_update_interval": 5,
            "time_windows": {
                "recent": 5,
                "medium": 10,
                "old": 15,
                "oldest": 20
            }
        },
        "search": {
            "lat_min": 31.3,
            "lat_max": 37.0,
            "lon_min": -114.8,
            "lon_max": -109.0
        },
        "setup_complete": False
    }
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load existing config or create default"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                return self._merge_configs(self.DEFAULT_CONFIG.copy(), config)
            except (json.JSONDecodeError, IOError):
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """Recursively merge configs, preserving existing values"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def save_config(self) -> bool:
        """Save current configuration"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False
    
    def is_setup_complete(self) -> bool:
        """Check if setup has been completed"""
        return self.config.get('setup_complete', False)
    
    def mark_setup_complete(self):
        """Mark setup as complete"""
        self.config['setup_complete'] = True
        self.save_config()


class CLISetupWizard:
    """Command-line setup wizard"""
    
    def __init__(self, config: SetupConfig):
        self.config = config
    
    def print_header(self, text: str):
        """Print a section header"""
        print("\n" + "=" * 60)
        print(f"  {text}")
        print("=" * 60 + "\n")
    
    def print_step(self, step: int, total: int, text: str):
        """Print step indicator"""
        print(f"\n[Step {step}/{total}] {text}")
        print("-" * 40)
    
    def get_input(self, prompt: str, default: str = "", required: bool = False) -> str:
        """Get user input with optional default"""
        if default:
            prompt = f"{prompt} [{default}]: "
        else:
            prompt = f"{prompt}: "
        
        while True:
            value = input(prompt).strip()
            if not value and default:
                return default
            if not value and required:
                print("This field is required. Please enter a value.")
                continue
            return value if value else default
    
    def get_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Get yes/no input"""
        default_str = "Y/n" if default else "y/N"
        while True:
            value = input(f"{prompt} [{default_str}]: ").strip().lower()
            if not value:
                return default
            if value in ('y', 'yes'):
                return True
            if value in ('n', 'no'):
                return False
            print("Please enter 'y' or 'n'")
    
    def run(self) -> bool:
        """Run the setup wizard"""
        self.print_header("🔧 CYT Setup Wizard")
        
        print("Welcome to Chasing Your Tail (CYT) setup!")
        print("This wizard will help you configure CYT for your system.\n")
        
        if self.config.is_setup_complete():
            if not self.get_yes_no("Setup has already been completed. Run setup again?", False):
                print("Setup cancelled.")
                return False
        
        total_steps = 5
        
        # Step 1: Kismet Configuration
        self.print_step(1, total_steps, "Kismet Database Configuration")
        self._setup_kismet()
        
        # Step 2: Directory Setup
        self.print_step(2, total_steps, "Directory Configuration")
        self._setup_directories()
        
        # Step 3: WiGLE API (Optional)
        self.print_step(3, total_steps, "WiGLE API Configuration (Optional)")
        self._setup_wigle()
        
        # Step 4: Geographic Boundaries
        self.print_step(4, total_steps, "Geographic Search Area")
        self._setup_geographic()
        
        # Step 5: Timing Settings
        self.print_step(5, total_steps, "Monitoring Settings")
        self._setup_timing()
        
        # Save and complete
        self.print_header("✅ Setup Complete")
        
        if self.config.save_config():
            self.config.mark_setup_complete()
            print("Configuration saved successfully!")
            print("\nYou can now run CYT:")
            print("  - GUI Mode:     python3 cyt_gui.py")
            print("  - CLI Mode:     python3 chasing_your_tail.py")
            print("  - Analysis:     python3 surveillance_analyzer.py")
            return True
        else:
            print("Error saving configuration!")
            return False
    
    def _setup_kismet(self):
        """Configure Kismet database path"""
        print("CYT reads Wi-Fi data from Kismet database files.")
        print("These are typically stored in a kismet_logs directory.\n")
        
        current_path = self.config.config['paths']['kismet_logs']
        
        # Try to find existing Kismet databases
        common_paths = [
            os.path.expanduser("~/kismet_logs/*.kismet"),
            "/home/*/kismet_logs/*.kismet",
            "/var/log/kismet/*.kismet",
            "/tmp/kismet*.kismet"
        ]
        
        found_paths = []
        for pattern in common_paths:
            matches = glob.glob(os.path.expanduser(pattern))
            if matches:
                # Get the directory pattern
                dir_pattern = os.path.dirname(pattern)
                found_paths.append(f"{dir_pattern}/*.kismet")
        
        if found_paths:
            print("Found potential Kismet database locations:")
            for i, path in enumerate(found_paths, 1):
                print(f"  {i}. {path}")
            print(f"  {len(found_paths)+1}. Enter custom path")
            
            choice = self.get_input(f"Select option (1-{len(found_paths)+1})", "1")
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(found_paths):
                    self.config.config['paths']['kismet_logs'] = found_paths[idx]
                else:
                    custom_path = self.get_input("Enter Kismet database path pattern", current_path)
                    self.config.config['paths']['kismet_logs'] = custom_path
            except ValueError:
                print("  ⚠️ Invalid input. Using previous or default Kismet database path.")
        else:
            print("No Kismet databases found automatically.")
            path = self.get_input("Enter Kismet database path pattern", current_path)
            self.config.config['paths']['kismet_logs'] = path
        
        print(f"\n✅ Kismet path set to: {self.config.config['paths']['kismet_logs']}")
    
    def _setup_directories(self):
        """Setup required directories"""
        print("CYT needs several directories for logs and output files.\n")
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        directories = ['logs', 'reports', 'ignore_lists', 'kml_files', 
                       'surveillance_reports', 'analysis_logs', 'secure_credentials']
        
        for dir_name in directories:
            dir_path = os.path.join(base_dir, dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                print(f"  ✅ Created: {dir_name}/")
            else:
                print(f"  ✓ Exists:  {dir_name}/")
        
        # Set secure permissions on credentials directory
        creds_dir = os.path.join(base_dir, 'secure_credentials')
        try:
            os.chmod(creds_dir, 0o700)
        except (OSError, PermissionError) as e:
            print(f"  ⚠️ Could not set permissions on credentials directory: {e}")
        
        print("\n✅ All directories configured")
    
    def _setup_wigle(self):
        """Configure WiGLE API credentials (optional)"""
        print("WiGLE API allows CYT to look up SSID locations.")
        print("This is optional - CYT works without it.\n")
        
        if not self.get_yes_no("Would you like to configure WiGLE API?", False):
            print("Skipping WiGLE configuration.")
            return
        
        print("\nTo get a WiGLE API key:")
        print("  1. Create an account at https://wigle.net")
        print("  2. Go to Account > API Token")
        print("  3. Generate a new API token\n")
        
        api_name = self.get_input("Enter WiGLE API name (or press Enter to skip)")
        if not api_name:
            return
        
        # Validate API name length and characters
        if len(api_name) > 100 or any(c in api_name for c in ['<', '>', '"', "'", '&', ';']):
            print("\n⚠️ Invalid API name. Contains invalid characters or is too long.")
            return
        
        api_token = getpass.getpass("Enter WiGLE API token: ")
        if not api_token:
            return
        
        # Validate API token length
        if len(api_token) > 200:
            print("\n⚠️ Invalid API token. Token is too long.")
            return
        
        # Create base64 encoded token
        import base64
        encoded_token = base64.b64encode(f"{api_name}:{api_token}".encode()).decode()
        
        # Store using secure credentials manager
        # Note: We set CYT_TEST_MODE to allow non-interactive credential storage during setup
        old_test_mode = os.environ.get('CYT_TEST_MODE')
        try:
            from secure_credentials import SecureCredentialManager
            os.environ['CYT_TEST_MODE'] = 'true'  # Use test mode for setup
            cred_manager = SecureCredentialManager()
            cred_manager.store_credential('wigle', 'encoded_token', encoded_token)
            print("\n✅ WiGLE API credentials stored securely")
        except Exception as e:
            print(f"\n⚠️ Could not store credentials securely: {e}")
            print("You may need to run migrate_credentials.py later.")
        finally:
            # Restore original test mode setting
            if old_test_mode is None:
                os.environ.pop('CYT_TEST_MODE', None)
            else:
                os.environ['CYT_TEST_MODE'] = old_test_mode
    
    def _setup_geographic(self):
        """Configure geographic search boundaries"""
        print("Geographic boundaries limit WiGLE searches to a specific area.")
        print("This helps reduce API usage and focus on your location.\n")
        
        current = self.config.config.get('search', {})
        
        if self.get_yes_no("Use default boundaries (Arizona/Southwest US)?", True):
            # Keep defaults
            pass
        else:
            print("\nEnter coordinates for your search area:")
            print("(Use negative values for West longitude and South latitude)\n")
            
            try:
                lat_min = float(self.get_input("Minimum Latitude", str(current.get('lat_min', 31.3))))
                lat_max = float(self.get_input("Maximum Latitude", str(current.get('lat_max', 37.0))))
                lon_min = float(self.get_input("Minimum Longitude", str(current.get('lon_min', -114.8))))
                lon_max = float(self.get_input("Maximum Longitude", str(current.get('lon_max', -109.0))))
                
                # Validate coordinate ranges
                if not (-90 <= lat_min <= 90 and -90 <= lat_max <= 90):
                    print("⚠️ Latitude values must be between -90 and 90. Using defaults.")
                elif not (-180 <= lon_min <= 180 and -180 <= lon_max <= 180):
                    print("⚠️ Longitude values must be between -180 and 180. Using defaults.")
                else:
                    self.config.config['search'] = {
                        'lat_min': lat_min,
                        'lat_max': lat_max,
                        'lon_min': lon_min,
                        'lon_max': lon_max
                    }
            except ValueError:
                print("⚠️ Invalid coordinates. Using defaults.")
        
        print(f"\n✅ Search area configured")
    
    def _setup_timing(self):
        """Configure monitoring timing settings"""
        print("Timing settings control how often CYT checks for new devices.\n")
        
        current_interval = self.config.config.get('timing', {}).get('check_interval', 60)
        
        if self.get_yes_no(f"Use default check interval ({current_interval} seconds)?", True):
            pass
        else:
            try:
                interval = int(self.get_input("Check interval (seconds)", str(current_interval)))
                if interval >= 10:
                    self.config.config['timing']['check_interval'] = interval
                else:
                    print("Interval must be at least 10 seconds. Using default.")
            except ValueError:
                print("Invalid interval. Using default.")
        
        print(f"\n✅ Timing configured: {self.config.config['timing']['check_interval']}s interval")


# Only define GUI class if tkinter is available
if HAS_TK:
    class GUISetupWizard:
        """Graphical setup wizard for touch-friendly interface"""
        
        def __init__(self, config: SetupConfig, parent: Optional[tk.Tk] = None):
            self.config = config
            self.parent = parent
            self.result = False
            
        def run(self) -> bool:
            """Run the GUI setup wizard"""
            if self.parent:
                # Run as dialog
                self._create_wizard_dialog()
            else:
                # Run as standalone window
                self.root = tk.Tk()
                self._setup_window()
                self.root.mainloop()
            
            return self.result
        
        def _create_wizard_dialog(self):
            """Create wizard as a dialog"""
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title("🔧 CYT Setup Wizard")
            self.dialog.geometry("700x550")
            self.dialog.configure(bg='#1a1a1a')
            self.dialog.transient(self.parent)
            self.dialog.grab_set()
            
            self._create_wizard_content(self.dialog)
            
            self.parent.wait_window(self.dialog)
        
        def _setup_window(self):
            """Setup standalone window"""
            self.root.title("🔧 CYT Setup Wizard")
            self.root.geometry("700x550")
            self.root.configure(bg='#1a1a1a')
            
            self._create_wizard_content(self.root)
        
        def _create_wizard_content(self, parent):
            """Create the wizard content"""
            self.current_step = 0
            self.steps = [
                ("Welcome", self._create_welcome_step),
                ("Kismet Database", self._create_kismet_step),
                ("WiGLE API", self._create_wigle_step),
                ("Search Area", self._create_search_step),
                ("Complete", self._create_complete_step)
            ]
            
            # Main container
            self.main_frame = tk.Frame(parent, bg='#1a1a1a', padx=30, pady=20)
            self.main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Step indicator
            self.step_label = tk.Label(
                self.main_frame,
                text="",
                font=('Arial', 12),
                fg='#888888',
                bg='#1a1a1a'
            )
            self.step_label.pack(pady=(0, 10))
            
            # Title
            self.title_label = tk.Label(
                self.main_frame,
                text="",
                font=('Arial', 20, 'bold'),
                fg='#00ff41',
                bg='#1a1a1a'
            )
            self.title_label.pack(pady=(0, 20))
            
            # Content frame
            self.content_frame = tk.Frame(self.main_frame, bg='#1a1a1a')
            self.content_frame.pack(fill=tk.BOTH, expand=True)
            
            # Navigation buttons
            nav_frame = tk.Frame(self.main_frame, bg='#1a1a1a')
            nav_frame.pack(fill=tk.X, pady=(20, 0))
            
            self.back_btn = tk.Button(
                nav_frame,
                text="◀ Back",
                font=('Arial', 12, 'bold'),
                width=12,
                height=2,
                fg='#ffffff',
                bg='#666666',
                activebackground='#555555',
                command=self._go_back
            )
            self.back_btn.pack(side=tk.LEFT)
            
            self.next_btn = tk.Button(
                nav_frame,
                text="Next ▶",
                font=('Arial', 12, 'bold'),
                width=12,
                height=2,
                fg='#ffffff',
                bg='#007acc',
                activebackground='#005999',
                command=self._go_next
            )
            self.next_btn.pack(side=tk.RIGHT)
            
            # Show first step
            self._show_step(0)
        
        def _show_step(self, step_index: int):
            """Show a specific step"""
            self.current_step = step_index
            
            # Clear content frame
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            
            # Update step indicator
            step_name, step_func = self.steps[step_index]
            self.step_label.config(text=f"Step {step_index + 1} of {len(self.steps)}")
            self.title_label.config(text=step_name)
            
            # Update navigation buttons
            self.back_btn.config(state=tk.NORMAL if step_index > 0 else tk.DISABLED)
            
            if step_index == len(self.steps) - 1:
                self.next_btn.config(text="Finish ✓", bg='#28a745')
            else:
                self.next_btn.config(text="Next ▶", bg='#007acc')
            
            # Create step content
            step_func()
        
        def _go_back(self):
            """Go to previous step"""
            if self.current_step > 0:
                self._show_step(self.current_step - 1)
        
        def _go_next(self):
            """Go to next step or finish"""
            if self.current_step < len(self.steps) - 1:
                self._show_step(self.current_step + 1)
            else:
                self._finish_setup()
        
        def _finish_setup(self):
            """Complete the setup"""
            self.config.save_config()
            self.config.mark_setup_complete()
            self.result = True
            
            if hasattr(self, 'dialog'):
                self.dialog.destroy()
            else:
                self.root.quit()
        
        def _create_label(self, parent, text: str, font_size: int = 12, color: str = '#cccccc'):
            """Helper to create styled labels"""
            return tk.Label(
                parent,
                text=text,
                font=('Arial', font_size),
                fg=color,
                bg='#1a1a1a',
                wraplength=600,
                justify=tk.LEFT
            )
        
        def _create_entry(self, parent, default: str = ""):
            """Helper to create styled entry"""
            entry = tk.Entry(
                parent,
                font=('Courier', 12),
                fg='#00ff41',
                bg='#2a2a2a',
                insertbackground='#00ff41',
                width=50
            )
            if default:
                entry.insert(0, default)
            return entry
        
        def _create_welcome_step(self):
            """Create welcome step content"""
            label = self._create_label(
                self.content_frame,
                "Welcome to Chasing Your Tail (CYT)!\n\n"
                "This setup wizard will help you configure CYT for your system.\n\n"
                "CYT is a Wi-Fi probe request analyzer that monitors wireless devices "
                "and can detect potential surveillance or stalking by identifying "
                "devices that appear persistently or follow you across locations.\n\n"
                "The setup will configure:\n"
                "• Kismet database location\n"
                "• WiGLE API credentials (optional)\n"
                "• Geographic search boundaries\n\n"
                "Click 'Next' to begin.",
                font_size=13
            )
            label.pack(pady=20)
        
        def _create_kismet_step(self):
            """Create Kismet configuration step"""
            label = self._create_label(
                self.content_frame,
                "CYT reads Wi-Fi data from Kismet database files.\n"
                "Enter the path pattern to your Kismet logs below.\n"
                "Use wildcards (*) to match multiple files.",
                font_size=12
            )
            label.pack(pady=(0, 20))
            
            # Path entry
            entry_frame = tk.Frame(self.content_frame, bg='#1a1a1a')
            entry_frame.pack(fill=tk.X, pady=10)
            
            tk.Label(
                entry_frame,
                text="Kismet Database Path:",
                font=('Arial', 11, 'bold'),
                fg='#ffffff',
                bg='#1a1a1a'
            ).pack(anchor=tk.W)
            
            self.kismet_entry = self._create_entry(
                entry_frame,
                self.config.config['paths']['kismet_logs']
            )
            self.kismet_entry.pack(fill=tk.X, pady=5)
            
            # Browse button
            browse_btn = tk.Button(
                entry_frame,
                text="Browse...",
                font=('Arial', 10),
                fg='#ffffff',
                bg='#444444',
                command=self._browse_kismet
            )
            browse_btn.pack(anchor=tk.W, pady=5)
            
            # Example
            example_label = self._create_label(
                self.content_frame,
                "Examples:\n"
                "• /home/user/kismet_logs/*.kismet\n"
                "• /var/log/kismet/*.kismet",
                font_size=10,
                color='#888888'
            )
            example_label.pack(pady=10)
        
        def _browse_kismet(self):
            """Browse for Kismet directory"""
            directory = filedialog.askdirectory(title="Select Kismet Logs Directory")
            if directory:
                self.kismet_entry.delete(0, tk.END)
                self.kismet_entry.insert(0, f"{directory}/*.kismet")
                self.config.config['paths']['kismet_logs'] = f"{directory}/*.kismet"
        
        def _create_wigle_step(self):
            """Create WiGLE API configuration step"""
            label = self._create_label(
                self.content_frame,
                "WiGLE API allows CYT to look up SSID locations.\n"
                "This is optional - CYT works without it.\n\n"
                "To get a WiGLE API key:\n"
                "1. Create an account at wigle.net\n"
                "2. Go to Account > API Token\n"
                "3. Generate a new API token",
                font_size=12
            )
            label.pack(pady=(0, 20))
            
            # API Name
            name_frame = tk.Frame(self.content_frame, bg='#1a1a1a')
            name_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(
                name_frame,
                text="WiGLE API Name (optional):",
                font=('Arial', 11, 'bold'),
                fg='#ffffff',
                bg='#1a1a1a'
            ).pack(anchor=tk.W)
            
            self.wigle_name_entry = self._create_entry(name_frame)
            self.wigle_name_entry.pack(fill=tk.X, pady=5)
            
            # API Token
            token_frame = tk.Frame(self.content_frame, bg='#1a1a1a')
            token_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(
                token_frame,
                text="WiGLE API Token (optional):",
                font=('Arial', 11, 'bold'),
                fg='#ffffff',
                bg='#1a1a1a'
            ).pack(anchor=tk.W)
            
            self.wigle_token_entry = self._create_entry(token_frame)
            self.wigle_token_entry.config(show='•')
            self.wigle_token_entry.pack(fill=tk.X, pady=5)
        
        def _create_search_step(self):
            """Create geographic search boundaries step"""
            label = self._create_label(
                self.content_frame,
                "Geographic boundaries limit WiGLE searches to your area.\n"
                "This helps reduce API usage and focus on your location.",
                font_size=12
            )
            label.pack(pady=(0, 20))
            
            current_search = self.config.config.get('search', {})
            
            # Coordinates frame
            coords_frame = tk.Frame(self.content_frame, bg='#2a2a2a', padx=20, pady=15)
            coords_frame.pack(fill=tk.X, pady=10)
            
            entries = [
                ("Minimum Latitude:", 'lat_min', current_search.get('lat_min', 31.3)),
                ("Maximum Latitude:", 'lat_max', current_search.get('lat_max', 37.0)),
                ("Minimum Longitude:", 'lon_min', current_search.get('lon_min', -114.8)),
                ("Maximum Longitude:", 'lon_max', current_search.get('lon_max', -109.0))
            ]
            
            self.search_entries = {}
            
            for label_text, key, default in entries:
                row = tk.Frame(coords_frame, bg='#2a2a2a')
                row.pack(fill=tk.X, pady=3)
                
                tk.Label(
                    row,
                    text=label_text,
                    font=('Arial', 11),
                    fg='#ffffff',
                    bg='#2a2a2a',
                    width=20,
                    anchor=tk.W
                ).pack(side=tk.LEFT)
                
                entry = tk.Entry(
                    row,
                    font=('Courier', 12),
                    fg='#00ff41',
                    bg='#1a1a1a',
                    insertbackground='#00ff41',
                    width=15
                )
                entry.insert(0, str(default))
                entry.pack(side=tk.LEFT, padx=10)
                self.search_entries[key] = entry
        
        def _create_complete_step(self):
            """Create completion step"""
            # Save any entered values first
            self._save_current_values()
            
            label = self._create_label(
                self.content_frame,
                "✅ Setup is complete!\n\n"
                "Your CYT configuration has been saved.\n\n"
                "You can now:\n"
                "• Start monitoring with the GUI\n"
                "• Run surveillance analysis\n"
                "• Analyze probe request logs\n\n"
                "Click 'Finish' to close the setup wizard.",
                font_size=13
            )
            label.pack(pady=20)
        
        def _save_current_values(self):
            """Save values from current step"""
            # Save Kismet path
            if hasattr(self, 'kismet_entry'):
                self.config.config['paths']['kismet_logs'] = self.kismet_entry.get()
            
            # Save WiGLE credentials if provided
            if hasattr(self, 'wigle_name_entry') and hasattr(self, 'wigle_token_entry'):
                api_name = self.wigle_name_entry.get().strip()
                api_token = self.wigle_token_entry.get().strip()
                
                if api_name and api_token:
                    # Validate API credentials
                    if len(api_name) > 100 or any(c in api_name for c in ['<', '>', '"', "'", '&', ';']):
                        messagebox.showwarning(
                            "Invalid API Name",
                            "WiGLE API name contains invalid characters or is too long.\n"
                            "Please use a shorter name without special characters."
                        )
                    elif len(api_token) > 200:
                        messagebox.showwarning(
                            "Invalid API Token",
                            "WiGLE API token is too long.\n"
                            "Please check your token and try again."
                        )
                    else:
                        # Store credentials with proper environment variable handling
                        old_test_mode = os.environ.get('CYT_TEST_MODE')
                        try:
                            import base64
                            from secure_credentials import SecureCredentialManager
                            os.environ['CYT_TEST_MODE'] = 'true'  # Use test mode for setup
                            encoded_token = base64.b64encode(f"{api_name}:{api_token}".encode()).decode()
                            cred_manager = SecureCredentialManager()
                            cred_manager.store_credential('wigle', 'encoded_token', encoded_token)
                        except Exception as e:
                            messagebox.showwarning(
                                "WiGLE Credential Storage Failed",
                                f"Could not store WiGLE credentials securely:\n{e}\n\n"
                                "You may need to re-enter them later."
                            )
                        finally:
                            # Restore original test mode setting
                            if old_test_mode is None:
                                os.environ.pop('CYT_TEST_MODE', None)
                            else:
                                os.environ['CYT_TEST_MODE'] = old_test_mode
            # Save search boundaries
            if hasattr(self, 'search_entries'):
                try:
                    lat_min = float(self.search_entries['lat_min'].get())
                    lat_max = float(self.search_entries['lat_max'].get())
                    lon_min = float(self.search_entries['lon_min'].get())
                    lon_max = float(self.search_entries['lon_max'].get())
                    
                    # Validate coordinate ranges
                    if not (-90 <= lat_min <= 90 and -90 <= lat_max <= 90):
                        messagebox.showwarning(
                            "Invalid Coordinates",
                            "Latitude values must be between -90 and 90.\n"
                            "Keeping previous values."
                        )
                    elif not (-180 <= lon_min <= 180 and -180 <= lon_max <= 180):
                        messagebox.showwarning(
                            "Invalid Coordinates",
                            "Longitude values must be between -180 and 180.\n"
                            "Keeping previous values."
                        )
                    else:
                        self.config.config['search'] = {
                            'lat_min': lat_min,
                            'lat_max': lat_max,
                            'lon_min': lon_min,
                            'lon_max': lon_max
                        }
                except ValueError as e:
                    messagebox.showwarning(
                        "Invalid Input",
                        f"Invalid search coordinates entered.\n"
                        f"Error: {e}\n\n"
                        "Keeping previous values."
                    )
else:
    # Placeholder for when tkinter is not available
    GUISetupWizard = None


def run_setup_wizard(gui: bool = None, parent=None) -> bool:
    """
    Run the setup wizard
    
    Args:
        gui: Force GUI (True) or CLI (False) mode. Auto-detect if None.
        parent: Parent Tk window for GUI mode (optional)
    
    Returns:
        True if setup completed successfully
    """
    config = SetupConfig()
    
    # Auto-detect mode if not specified
    if gui is None:
        # Use GUI if available and we have a display
        gui = HAS_TK and (os.environ.get('DISPLAY') or sys.platform == 'darwin')
    
    if gui and HAS_TK and GUISetupWizard:
        wizard = GUISetupWizard(config, parent)
        return wizard.run()
    else:
        wizard = CLISetupWizard(config)
        return wizard.run()


def needs_setup(config_path: str = "config.json") -> bool:
    """
    Check if setup is needed
    
    Args:
        config_path: Path to config file (defaults to config.json)
    
    Returns:
        True if setup is needed, False otherwise
    """
    config = SetupConfig(config_path)
    return not config.is_setup_complete()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='CYT Setup Wizard')
    parser.add_argument('--cli', action='store_true', help='Force CLI mode')
    parser.add_argument('--gui', action='store_true', help='Force GUI mode')
    args = parser.parse_args()
    
    if args.cli:
        run_setup_wizard(gui=False)
    elif args.gui:
        run_setup_wizard(gui=True)
    else:
        run_setup_wizard()
