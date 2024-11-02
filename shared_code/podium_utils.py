# shared_code/podium_utils.py

import logging

class PodiumUtils:
    def __init__(self, player_container):
        self.player_container = player_container

    def get_podium(self):
        """
        Retrieves the top 3 positions (gold, silver, bronze) based on points per game ratio (ppgr).
        Applies tiebreakers as specified.

        Returns:
            dict: A dictionary with keys 'gold', 'silver', 'bronze', each containing a list of player dictionaries.
        """
        try:
            # Fetch all players from the database
            players = list(self.player_container.read_all_items())
            logging.info(f"Retrieved {len(players)} players from the database.")

            # Compute ppgr for each player
            player_stats = []
            for player in players:
                games_played = player.get('games_played', 0)
                total_score = player.get('total_score', 0)
                username = player.get('username')

                # Handle division by zero
                if games_played == 0:
                    ppgr = 0  # Option A: Consider ppgr as 0 for players with zero games played
                else:
                    ppgr = total_score / games_played

                player_stats.append({
                    'username': username,
                    'games_played': games_played,
                    'total_score': total_score,
                    'ppgr': ppgr
                })

            # Sort players by ppgr in descending order
            # Apply tiebreakers: increasing games_played, then increasing alphabetical order
            player_stats.sort(
                key=lambda x: (-x['ppgr'], x['games_played'], x['username'])
            )

            # Prepare the podium
            podium = {'gold': [], 'silver': [], 'bronze': []}
            positions = ['gold', 'silver', 'bronze']
            current_position = 0
            last_ppgr = None

            for player in player_stats:
                ppgr = player['ppgr']

                if ppgr == 0:
                    # Skip players with ppgr == 0 if you choose Option B
                    # break  # Uncomment this line if you choose Option B
                    pass  # For Option A, continue including players with ppgr == 0

                if last_ppgr is None:
                    # First player
                    podium[positions[current_position]].append(player)
                    last_ppgr = ppgr
                elif ppgr == last_ppgr:
                    # Same ppgr, add to the current position
                    podium[positions[current_position]].append(player)
                else:
                    # Different ppgr, move to the next position
                    current_position += 1
                    if current_position >= len(positions):
                        # Podium is full
                        break
                    podium[positions[current_position]].append(player)
                    last_ppgr = ppgr

            # Remove positions that are empty
            podium = {k: v for k, v in podium.items() if v}

            # Remove ppgr from the output
            for position in podium.values():
                for player in position:
                    del player['ppgr']

            return podium

        except Exception as e:
            logging.error(f"Error computing podium: {e}")
            print("TEST:------------------------SOMETHING WENT WRONG------------------------")
            raise e
