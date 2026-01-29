import requests
import re

base_url = "https://pokeapi.co/api/v2/"

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


def get_pokemon_info(name):
    # Validate input first
    is_valid, sanitized_name, error_message = InputValidator.validate_pokemon_name(name)
    
    if not is_valid:
        print(f"Validation Error: {error_message}")
        return None
    
    url = f"{base_url}pokemon/{sanitized_name}/"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            pokemon_data = response.json()
            print("Data retrieved successfully")
            return pokemon_data
        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

# --- Main Execution ---
pokemon_name = "pikachu"
pokemon_info = get_pokemon_info(pokemon_name)

if pokemon_info:
    
    print("-----------------------------")
    print(f"Name: {pokemon_info['name'].capitalize()}")
    print(f"ID: {pokemon_info['id']}")
    print(f"Height: {pokemon_info['height']}")
    print(f"Weight: {pokemon_info['weight']}")
    print("Abilities:")
    for ability in pokemon_info['abilities']:
        print(f"- {ability['ability']['name'].replace('-', ' ').title()}")
    print("-----------------------------")
else:
    print("No data found to display.")