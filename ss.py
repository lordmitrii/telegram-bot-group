"""
Never do like this, but API doesnt have a good documentation.
Sorry to everyone watching this
"""
import os, requests
import time
import json


with open("team_ids.json", "r", encoding="utf-8") as file:
    TEAMS = json.load(file)

TEAMS_DICT = {team["team_id"]: {"team_name": team["team_name"], "team_league": team["team_league"]} for team in TEAMS}

URL = "https://api.football-data.org/v4/matches?TODAY"
HEADERS = {"X-Auth-Token": os.getenv("FOOTBALL_API_KEY")} 

def get_team_ids():
    
    response = requests.get(URL, headers=HEADERS)
    big_games = []
    if response.status_code == 200:
        fixtures = response.json().get("matches", [])
        for match in fixtures:
            league_id = match["competition"]["id"]
            league_name_api = match["competition"]["name"]
            home_team_api = match["homeTeam"]
            away_team_api = match["awayTeam"]
            match_time_api = match["utcDate"]

            if league_id == 2001 or league_name_api == "UEFA Champions League":
                home_team = home_team_api["name"]
                away_team = away_team_api["name"]

                if home_team_api["id"] in TEAMS_DICT.keys():
                    home_team = TEAMS_DICT[home_team_api["id"]]["team_name"]
                if away_team_api["id"] in TEAMS_DICT.keys():
                    away_team = TEAMS_DICT[away_team_api["id"]]["team_name"]

                big_games.append((league_name_api, home_team, away_team, match_time_api))

            elif home_team_api["id"] in TEAMS_DICT.keys() and away_team_api["id"] in TEAMS_DICT.keys():
                home_team = TEAMS_DICT[home_team_api["id"]]["team_name"]
                away_team = TEAMS_DICT[away_team_api["id"]]["team_name"]
                if TEAMS_DICT[home_team_api["id"]]["team_league"] == TEAMS_DICT[away_team_api["id"]]["team_league"]:
                    league_name = TEAMS_DICT[home_team_api["id"]]["team_league"]
                    big_games.append((league_name, home_team, away_team, match_time_api))
                else:
                    big_games.append((league_name_api, home_team, away_team, match_time_api))

        print(big_games)
   
    else:
        print(f"No data available")
            
        
       
            

get_team_ids()
