"""
Never do like this, but API doesnt have a good documentation.
Sorry to everyone watching this
"""

import os, requests
import time
import json


URL = "https://api.football-data.org/v4/teams/{i}/matches"
HEADERS = {"X-Auth-Token": os.getenv("FOOTBALL_API_KEY")} 


def clear_console():
    # Clears the console on Windows or Unix systems
    os.system('cls' if os.name == 'nt' else 'clear')


def get_team_ids():
    try:
        with open('team_ids.json', 'r') as json_file:
            team_data_list = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        team_data_list = [] 

    processed_ids = {list(d.keys())[0] for d in team_data_list}

    for i in range(10000):
        # Skip team IDs that are already processed
        if str(i) in processed_ids:
            clear_console()
            print(f"Team {i} already processed, skipping.")
            continue

        response = requests.get(URL.format(i=i), headers=HEADERS)
        
        if response.status_code == 200:
            fixtures = response.json().get("matches", [])
            games = []
            for index in range(len(fixtures)):
                home_team = fixtures[index]["homeTeam"]["name"]
                away_team = fixtures[index]["awayTeam"]["name"]
                games.append(away_team)
                games.append(home_team)

                if index >= 10:
                    break
            
            games = sorted(games, key=lambda x: games.count(x),reverse=True)
            if games:  
                team_name = games[0]
                team_count = games.count(team_name)
                team_data = {str(i): games[0]}
                team_data_list.append(team_data)
                processed_ids.add(str(i))
                clear_console()
                print(f"Team ID {i}: {team_count} - {team_name}")
            else:
                clear_console()
                print(f"Team {i} has no games.")
        
            time.sleep(7)
        else:
            clear_console()
            print(f"Team {i}: No data available")
            continue
        
        with open('team_ids.json', 'w') as json_file:
            json.dump(team_data_list, json_file, indent=4)
            

get_team_ids()
