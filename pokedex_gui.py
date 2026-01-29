import customtkinter as ctk
import requests
from PIL import Image, ImageTk
import io
import threading
import re

# --- API Configuration ---
BASE_URL = "https://pokeapi.co/api/v2/pokemon/"

# --- Input Validation ---
class InputValidator:
    """
    Validates and sanitizes user input to prevent injection attacks.
    This includes SQL injection, command injection, and path traversal.
    """
    
    # Maximum allowed input length
    MAX_INPUT_LENGTH = 50
    
    # Regex pattern for valid Pokemon names (alphanumeric, hyphens, spaces only)
    VALID_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\-\s]+$')
    
    # Dangerous patterns to block (SQL injection, command injection, etc.)
    DANGEROUS_PATTERNS = [
        r'[;\'\"\`]',           # SQL/command terminators and quotes
        r'--',                   # SQL comment
        r'/\*',                  # SQL block comment start
        r'\*/',                  # SQL block comment end
        r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|EXEC|UNION|OR|AND)\b',  # SQL keywords
        r'[<>]',                 # XSS brackets
        r'\.\.',                 # Path traversal
        r'[/\\]',                # Path separators
        r'[\x00-\x1f]',          # Control characters
    ]
    
    @classmethod
    def validate_pokemon_name(cls, name: str) -> tuple[bool, str, str]:
        """
        Validates and sanitizes a Pokemon name input.
        
        Args:
            name: The raw user input
            
        Returns:
            Tuple of (is_valid, sanitized_name, error_message)
        """
        # Check if input is empty
        if not name or not name.strip():
            return False, "", "Please enter a Pokémon name"
        
        # Strip whitespace and convert to lowercase
        sanitized = name.strip().lower()
        
        # Check length
        if len(sanitized) > cls.MAX_INPUT_LENGTH:
            return False, "", f"Input too long (max {cls.MAX_INPUT_LENGTH} characters)"
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return False, "", "Invalid characters detected in input"
        
        # Check if name matches valid pattern
        if not cls.VALID_NAME_PATTERN.match(sanitized):
            return False, "", "Pokémon name can only contain letters, numbers, and hyphens"
        
        return True, sanitized, ""
    
    @classmethod
    def is_safe_input(cls, user_input: str) -> bool:
        """
        Quick check if input is safe (no dangerous patterns).
        
        Args:
            user_input: The raw user input
            
        Returns:
            True if input appears safe, False otherwise
        """
        if not user_input:
            return False
            
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False
        
        return True

class PokedexApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Pokédex - Modern Collector")
        self.geometry("800x600")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Variables
        self.current_pokemon_data = None

        # --- Layout ---
        
        # Sidebar (for search and list history maybe?)
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Pokédex", font=ctk.CTkFont(size=24, weight="bold", family="Inter"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.search_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Enter Pokémon Name...")
        self.search_entry.grid(row=1, column=0, padx=20, pady=10)
        self.search_entry.bind("<Return>", lambda e: self.search_pokemon())

        self.search_button = ctk.CTkButton(self.sidebar_frame, text="Search", command=self.search_pokemon, fg_color="#DD2D44", hover_color="#B91C1C")
        self.search_button.grid(row=2, column=0, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="", text_color="gray")
        self.status_label.grid(row=3, column=0, padx=20, pady=5)

        # Main Content Area
        self.main_content = ctk.CTkFrame(self, corner_radius=15, fg_color="#1A1A1A")
        self.main_content.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_columnconfigure(1, weight=1)

        # Pokemon Image Display
        self.image_container = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.image_container.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.pokemon_img_label = ctk.CTkLabel(self.image_container, text="No Pokémon Selected", text_color="#555555")
        self.pokemon_img_label.pack(expand=True, fill="both")

        # Pokemon Info Display
        self.info_container = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.info_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.name_label = ctk.CTkLabel(self.info_container, text="---", font=ctk.CTkFont(size=32, weight="bold"))
        self.name_label.pack(anchor="w", pady=(0, 5))

        self.id_label = ctk.CTkLabel(self.info_container, text="#000", font=ctk.CTkFont(size=18), text_color="gray")
        self.id_label.pack(anchor="w", pady=(0, 20))

        # Stats Section
        self.stats_frame = ctk.CTkFrame(self.info_container, fg_color="transparent")
        self.stats_frame.pack(fill="x", expand=True)
        
        self.stat_widgets = {}
        for stat_name in ["hp", "attack", "defense", "speed"]:
            row = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            lbl = ctk.CTkLabel(row, text=stat_name.upper(), width=80, anchor="w", font=ctk.CTkFont(size=11, weight="bold"))
            lbl.pack(side="left")
            
            progress = ctk.CTkProgressBar(row, height=10, progress_color="#DD2D44")
            progress.set(0)
            progress.pack(side="left", fill="x", expand=True, padx=10)
            
            val_lbl = ctk.CTkLabel(row, text="0", width=30)
            val_lbl.pack(side="right")
            
            self.stat_widgets[stat_name] = (progress, val_lbl)

        # Abilities & Types
        self.details_frame = ctk.CTkFrame(self.info_container, fg_color="transparent")
        self.details_frame.pack(fill="x", pady=20)
        
        self.type_label = ctk.CTkLabel(self.details_frame, text="Type: ---", anchor="w")
        self.type_label.pack(fill="x")
        
        self.ability_label = ctk.CTkLabel(self.details_frame, text="Abilities: ---", anchor="w", wraplength=300)
        self.ability_label.pack(fill="x")

    def search_pokemon(self):
        raw_name = self.search_entry.get()
        
        # Validate input to prevent injection attacks and malformed requests
        is_valid, sanitized_name, error_message = InputValidator.validate_pokemon_name(raw_name)
        
        if not is_valid:
            self.status_label.configure(text=error_message, text_color="#EF4444")
            return

        self.status_label.configure(text="Searching...", text_color="gray")
        self.search_button.configure(state="disabled")
        
        # Run in thread to keep GUI responsive
        thread = threading.Thread(target=self.fetch_pokemon_data, args=(sanitized_name,))
        thread.start()

    def fetch_pokemon_data(self, name):
        try:
            response = requests.get(f"{BASE_URL}{name}")
            if response.status_code == 200:
                data = response.json()
                self.after(0, lambda: self.update_ui(data))
            else:
                self.after(0, lambda: self.show_error(f"Pokemon '{name}' not found"))
        except Exception as e:
            self.after(0, lambda: self.show_error("Network Error"))
        finally:
            self.after(0, lambda: self.search_button.configure(state="normal"))

    def update_ui(self, data):
        self.status_label.configure(text="Pokémon Loaded!", text_color="#10B981")
        
        # Name and ID
        self.name_label.configure(text=data['name'].capitalize())
        self.id_label.configure(text=f"No. {data['id']:03d}")

        # Basic Stats
        stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
        for name, (progress, lbl) in self.stat_widgets.items():
            if name in stats:
                val = stats[name]
                progress.set(val / 255.0) # Stats usually max around 255
                lbl.configure(text=str(val))

        # Types
        types = [t['type']['name'].capitalize() for t in data['types']]
        self.type_label.configure(text=f"Type: {' / '.join(types)}")

        # Abilities
        abilities = [a['ability']['name'].replace('-', ' ').title() for a in data['abilities']]
        self.ability_label.configure(text=f"Abilities: {', '.join(abilities)}")

        # Load Image
        image_url = data['sprites']['other']['official-artwork']['front_default']
        if not image_url:
            image_url = data['sprites']['front_default']
            
        if image_url:
            thread = threading.Thread(target=self.load_pokemon_image, args=(image_url,))
            thread.start()

    def load_pokemon_image(self, url):
        try:
            response = requests.get(url)
            img_data = response.content
            img = Image.open(io.BytesIO(img_data))
            
            # Resize image
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(300, 300))
            
            self.after(0, lambda: self.pokemon_img_label.configure(image=ctk_img, text=""))
        except Exception:
            self.after(0, lambda: self.pokemon_img_label.configure(text="Image Loading Failed"))

    def show_error(self, message):
        self.status_label.configure(text=message, text_color="#EF4444")
        self.name_label.configure(text="---")
        self.id_label.configure(text="#000")
        self.pokemon_img_label.configure(image=None, text="Pokémon Not Found")
        for progress, lbl in self.stat_widgets.values():
            progress.set(0)
            lbl.configure(text="0")

if __name__ == "__main__":
    app = PokedexApp()
    app.mainloop()
