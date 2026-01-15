import requests

base_url = "https://pokeapi.co/api/v2/"

def get_pokemon_info(name):
    # Convert name to lowercase to ensure API finds it
    url = f"{base_url}pokemon/{name.lower()}/"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            pokemon_data = response.json()
            print("Data retrieved successfully")
            return pokemon_data  # <--- CRITICAL FIX: Return the data!
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