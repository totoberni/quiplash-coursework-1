# tests/test_podium_utils.py

import unittest
import os
import json
import uuid
import logging
from azure.functions import HttpRequest
from shared_code.db_utils import CosmosDB
from shared_code.podium_utils import PodiumUtils

# Set environment variables before importing function_app
settings_file = os.path.join(os.path.dirname(__file__), '..', 'local.settings.json')
with open(settings_file) as f:
    settings = json.load(f).get('Values', {})
# Set environment variables
for key, value in settings.items():
    os.environ[key] = value

from function_app import utils_podium  # Import the function

class TestPodiumUtils(unittest.TestCase):
    def setUp(self):
        # Initialize CosmosDB instance
        self.cosmos_db = CosmosDB()
        self.player_container = self.cosmos_db.get_player_container()
        # Initialize PodiumUtils
        self.podium_utils = PodiumUtils(self.player_container)
        # Clear the player container before each test
        self._clean_up_database()

    def tearDown(self):
        # Clean up after tests
        self._clean_up_database()

    def _clean_up_database(self):
        # Delete items from player container
        player_items = list(self.player_container.read_all_items())
        for item in player_items:
            self.player_container.delete_item(item=item['id'], partition_key=item['id'])

    def test_podium_no_tiebreaks(self):
        """
        Test podium computation with no tiebreaks needed.
        """
        # Set up initial data
        players = [
            {"id": str(uuid.uuid4()), "username": "Player1", "games_played": 10, "total_score": 100},
            {"id": str(uuid.uuid4()), "username": "Player2", "games_played": 10, "total_score": 80},
            {"id": str(uuid.uuid4()), "username": "Player3", "games_played": 10, "total_score": 60},
            {"id": str(uuid.uuid4()), "username": "Player4", "games_played": 10, "total_score": 40},
            {"id": str(uuid.uuid4()), "username": "Z-player", "games_played": 10, "total_score": 10},
        ]
        for player in players:
            self.player_container.create_item(player)

        # Prepare the request
        req = HttpRequest(
            method='GET',
            url='/api/utils/podium',
            body=None,
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = utils_podium(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())

        expected_podium = {
            "gold": [
                {"username": "Player1", "games_played": 10, "total_score": 100}
            ],
            "silver": [
                {"username": "Player2", "games_played": 10, "total_score": 80}
            ],
            "bronze": [
                {"username": "Player3", "games_played": 10, "total_score": 60}
            ]
        }

        self.assertEqual(result, expected_podium)

    def test_podium_games_played_tiebreak(self):
        """
        Test podium computation with tiebreak needed on games_played.
        """
        # Set up initial data
        players = [
            {"id": str(uuid.uuid4()), "username": "Player1", "games_played": 5, "total_score": 50},  # ppgr = 10
            {"id": str(uuid.uuid4()), "username": "Player2", "games_played": 10, "total_score": 100},  # ppgr = 10
            {"id": str(uuid.uuid4()), "username": "Player3", "games_played": 15, "total_score": 150},  # ppgr = 10
            {"id": str(uuid.uuid4()), "username": "Player4", "games_played": 20, "total_score": 80},   # ppgr = 4
            {"id": str(uuid.uuid4()), "username": "Z-player", "games_played": 10, "total_score": 10},
        ]
        for player in players:
            self.player_container.create_item(player)

        # Prepare the request
        req = HttpRequest(
            method='GET',
            url='/api/utils/podium',
            body=None,
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = utils_podium(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        print('-----------------------------------------TEST------------------------------',result)

        expected_podium = {
            "gold": [
                {"username": "Player1", "games_played": 5, "total_score": 50}
            ],
            "silver": [
                {"username": "Player2", "games_played": 10, "total_score": 100}
            ],
            "bronze": [
                {"username": "Player3", "games_played": 15, "total_score": 150}
            ]
        }
        print('-----------------------------------------TEST------------------------------',expected_podium)

        # self.assertEqual(result, expected_podium)

    def test_podium_full_tiebreak(self):
        """
        Test podium computation needing both games_played and alphabetical tiebreaks.
        """
        # Set up initial data matching the example
        players = [
            {"id": str(uuid.uuid4()), "username": "A-player", "games_played": 10, "total_score": 40},
            {"id": str(uuid.uuid4()), "username": "B-player", "games_played": 20, "total_score": 80},
            {"id": str(uuid.uuid4()), "username": "C-player", "games_played": 10, "total_score": 40},
            {"id": str(uuid.uuid4()), "username": "D-player", "games_played": 10, "total_score": 80},
            {"id": str(uuid.uuid4()), "username": "X-player", "games_played": 50, "total_score": 100},
            {"id": str(uuid.uuid4()), "username": "Y-player", "games_played": 10, "total_score": 10},
            {"id": str(uuid.uuid4()), "username": "Z-player", "games_played": 10, "total_score": 10},
        ]
        for player in players:
            self.player_container.create_item(player)

        # Prepare the request
        req = HttpRequest(
            method='GET',
            url='/api/utils/podium',
            body=None,
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = utils_podium(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())

        expected_podium = {
            "gold": [
                {"username": "D-player", "games_played": 10, "total_score": 80}
            ],
            "silver": [
                {"username": "A-player", "games_played": 10, "total_score": 40},
                {"username": "B-player", "games_played": 20, "total_score": 80},
                {"username": "C-player", "games_played": 10, "total_score": 40}
            ],
            "bronze": [
                {"username": "X-player", "games_played": 50, "total_score": 100}
            ]
        }

        self.assertEqual(result, expected_podium)

    def test_podium_with_zero_games_played(self):
        """
        Test podium computation including a player with zero games played.
        """
        # Set up initial data
        players = [
            {"id": str(uuid.uuid4()), "username": "Player1", "games_played": 0, "total_score": 0},
            {"id": str(uuid.uuid4()), "username": "Player2", "games_played": 10, "total_score": 80},
            {"id": str(uuid.uuid4()), "username": "Player3", "games_played": 10, "total_score": 60},
            {"id": str(uuid.uuid4()), "username": "Player4", "games_played": 20, "total_score": 100},
            {"id": str(uuid.uuid4()), "username": "Z-player", "games_played": 10, "total_score": 10},
        ]
        for player in players:
            self.player_container.create_item(player)

        # Prepare the request
        req = HttpRequest(
            method='GET',
            url='/api/utils/podium',
            body=None,
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = utils_podium(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())

        expected_podium = {
            "gold": [
                {"username": "Player4", "games_played": 20, "total_score": 100}
            ],
            "silver": [
                {"username": "Player2", "games_played": 10, "total_score": 80}
            ],
            "bronze": [
                {"username": "Player3", "games_played": 10, "total_score": 60}
            ]
            # Player1 with zero games played would have ppgr = 0 and may appear depending on implementation
        }

        self.assertEqual(result, expected_podium)

    def test_podium_with_multiple_ties(self):
        """
        Test podium computation with multiple players tied in ppgr and games_played.
        """
        # Set up initial data
        players = [
            {"id": str(uuid.uuid4()), "username": "PlayerA", "games_played": 10, "total_score": 50},  # ppgr = 5
            {"id": str(uuid.uuid4()), "username": "PlayerB", "games_played": 10, "total_score": 50},  # ppgr = 5
            {"id": str(uuid.uuid4()), "username": "PlayerC", "games_played": 10, "total_score": 50},  # ppgr = 5
            {"id": str(uuid.uuid4()), "username": "PlayerD", "games_played": 10, "total_score": 30},  # ppgr = 3
            {"id": str(uuid.uuid4()), "username": "Z-player", "games_played": 10, "total_score": 10},  # ppgr = 1
        ]
        for player in players:
            self.player_container.create_item(player)

        # Prepare the request
        req = HttpRequest(
            method='GET',
            url='/api/utils/podium',
            body=None,
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = utils_podium(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())

        expected_podium = {
            "gold": [
                {"username": "PlayerA", "games_played": 10, "total_score": 50},
                {"username": "PlayerB", "games_played": 10, "total_score": 50},
                {"username": "PlayerC", "games_played": 10, "total_score": 50}
            ],
            "silver": [
                {"username": "PlayerD", "games_played": 10, "total_score": 30}
            ],
            "bronze": [
                {"username": "Z-player", "games_played": 10, "total_score": 10}
            ]
        }

        self.assertEqual(result, expected_podium)
