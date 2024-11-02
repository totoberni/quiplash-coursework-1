# tests/test_podium_utils.py

import unittest
import os
import json
import uuid
import logging
from azure.functions import HttpRequest
from shared_code.db_utils import CosmosDB
from shared_code.get_prompts_utils import GetPrompts

# Set environment variables before importing function_app
settings_file = os.path.join(os.path.dirname(__file__), '..', 'local.settings.json')
with open(settings_file) as f:
    settings = json.load(f).get('Values', {})
# Set environment variables
for key, value in settings.items():
    os.environ[key] = value

from function_app import utils_podium, utils_get  # Import the functions

class TestGetPrompts(unittest.TestCase):
    def setUp(self):
        # Initialize CosmosDB instance
        self.cosmos_db = CosmosDB()
        self.player_container = self.cosmos_db.get_player_container()
        self.prompt_container = self.cosmos_db.get_prompt_container()
        # Initialize GetPrompts
        self.get_prompts_utils = GetPrompts(self.prompt_container)
        # Clear the player and prompt containers before each test
        self._clean_up_database()

    def tearDown(self):
        # Clean up after tests
        self._clean_up_database()

    def _clean_up_database(self):
        # Delete items from player container
        player_items = list(self.player_container.read_all_items())
        for item in player_items:
            self.player_container.delete_item(item=item['id'], partition_key=item['id'])
        # Delete items from prompt container
        prompt_items = list(self.prompt_container.read_all_items())
        for item in prompt_items:
            self.prompt_container.delete_item(item=item['id'], partition_key=item['username'])

    def test_get_prompts_single_player_single_language(self):
        """
        Test retrieving prompts with only 1 player and 1 language type.
        """
        # Set up initial data
        player = {"id": str(uuid.uuid4()), "username": "player1", "games_played": 10, "total_score": 50}
        self.player_container.create_item(player)

        prompts = [
            {
                "id": "auto-gen-1",
                "username": "player1",
                "texts": [
                    {"text": "First English prompt", "language": "en"},
                    {"text": "Primer prompt en español", "language": "es"}
                ]
            },
            {
                "id": "auto-gen-2",
                "username": "player1",
                "texts": [
                    {"text": "Second English prompt", "language": "en"},
                    {"text": "Segundo prompt en español", "language": "es"}
                ]
            }
        ]
        for prompt in prompts:
            self.prompt_container.create_item(prompt)

        # Prepare the request
        req_body = {"players": ["player1"], "language": "en"}
        req = HttpRequest(
            method='GET',
            url='/api/utils/get',
            body=json.dumps(req_body).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = utils_get(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())

        expected_output = [
            {"id": "auto-gen-1", "text": "First English prompt", "username": "player1"},
            {"id": "auto-gen-2", "text": "Second English prompt", "username": "player1"}
        ]

        self.assertCountEqual(result, expected_output)

    def test_get_prompts_single_player_two_languages(self):
        """
        Test retrieving prompts with 1 player, 2 language types, and request to see both languages.
        """
        # Set up initial data
        player = {"id": str(uuid.uuid4()), "username": "player2", "games_played": 15, "total_score": 75}
        self.player_container.create_item(player)

        prompts = [
            {
                "id": "auto-gen-3",
                "username": "player2",
                "texts": [
                    {"text": "English prompt one", "language": "en"},
                    {"text": "Prompt en español uno", "language": "es"}
                ]
            },
            {
                "id": "auto-gen-4",
                "username": "player2",
                "texts": [
                    {"text": "English prompt two", "language": "en"},
                    {"text": "Prompt en español dos", "language": "es"}
                ]
            }
        ]
        for prompt in prompts:
            self.prompt_container.create_item(prompt)

        # Prepare the request
        req_body = {"players": ["player2"], "language": "es"}
        req = HttpRequest(
            method='GET',
            url='/api/utils/get',
            body=json.dumps(req_body).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = utils_get(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())

        expected_output = [
            {"id": "auto-gen-3", "text": "Prompt en español uno", "username": "player2"},
            {"id": "auto-gen-4", "text": "Prompt en español dos", "username": "player2"}
        ]

        self.assertCountEqual(result, expected_output)

    def test_get_prompts_single_player_two_languages_single_request_language(self):
        """
        Test retrieving prompts with 1 player, 2 languages, and request to see only one language.
        """
        # Set up initial data
        player = {"id": str(uuid.uuid4()), "username": "player3", "games_played": 20, "total_score": 100}
        self.player_container.create_item(player)

        prompts = [
            {
                "id": "auto-gen-5",
                "username": "player3",
                "texts": [
                    {"text": "English prompt three", "language": "en"},
                    {"text": "Prompt en español tres", "language": "es"}
                ]
            },
            {
                "id": "auto-gen-6",
                "username": "player3",
                "texts": [
                    {"text": "English prompt four", "language": "en"},
                    {"text": "Prompt en español cuatro", "language": "es"}
                ]
            }
        ]
        for prompt in prompts:
            self.prompt_container.create_item(prompt)

        # Prepare the request to fetch only 'en' language
        req_body = {"players": ["player3"], "language": "en"}
        req = HttpRequest(
            method='GET',
            url='/api/utils/get',
            body=json.dumps(req_body).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = utils_get(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())

        expected_output = [
            {"id": "auto-gen-5", "text": "English prompt three", "username": "player3"},
            {"id": "auto-gen-6", "text": "English prompt four", "username": "player3"}
        ]

        self.assertCountEqual(result, expected_output)

    def test_get_prompts_multiple_players_multiple_languages_subset(self):
        """
        Test retrieving prompts with 4 players, 3 languages and request to see prompts for 2 players and 2 languages 
        """
        # Set up initial data
        players = [
            {"id": str(uuid.uuid4()), "username": "player4", "games_played": 10, "total_score": 40},
            {"id": str(uuid.uuid4()), "username": "player5", "games_played": 20, "total_score": 80},
            {"id": str(uuid.uuid4()), "username": "player6", "games_played": 10, "total_score": 40},
            {"id": str(uuid.uuid4()), "username": "player7", "games_played": 10, "total_score": 80}
        ]
        for player in players:
            self.player_container.create_item(player)

        prompts = [
            {
                "id": "auto-gen-7",
                "username": "player4",
                "texts": [
                    {"text": "English prompt five", "language": "en"},
                    {"text": "Prompt en español cinco", "language": "es"},
                    {"text": "Prompt in Italian five", "language": "it"}
                ]
            },
            {
                "id": "auto-gen-8",
                "username": "player5",
                "texts": [
                    {"text": "English prompt six", "language": "en"},
                    {"text": "Prompt en español seis", "language": "es"},
                    {"text": "Prompt in Italian six", "language": "it"}
                ]
            },
            {
                "id": "auto-gen-9",
                "username": "player6",
                "texts": [
                    {"text": "English prompt seven", "language": "en"},
                    {"text": "Prompt en español siete", "language": "es"},
                    {"text": "Prompt in Italian seven", "language": "it"}
                ]
            },
            {
                "id": "auto-gen-10",
                "username": "player7",
                "texts": [
                    {"text": "English prompt eight", "language": "en"},
                    {"text": "Prompt en español ocho", "language": "es"},
                    {"text": "Prompt in Italian eight", "language": "it"}
                ]
            }
        ]
        for prompt in prompts:
            self.prompt_container.create_item(prompt)

        # Prepare the request to fetch prompts for 'player4' and 'player5' in 'es'
        req_body = {"players": ["player4", "player5"], "language": "es"}
        req = HttpRequest(
            method='GET',
            url='/api/utils/get',
            body=json.dumps(req_body).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = utils_get(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())

        expected_output = [
            {"id": "auto-gen-7", "text": "Prompt en español cinco", "username": "player4"},
            {"id": "auto-gen-8", "text": "Prompt en español seis", "username": "player5"}
        ]

        self.assertCountEqual(result, expected_output)

    def test_get_prompts_multiple_players_multiple_languages_all(self):
        """
        Test retrieving prompts with 4 players, 3 languages and request to see all 3 languages and all 4 players
        """
        # Set up initial data
        players = [
            {"id": str(uuid.uuid4()), "username": "player8", "games_played": 10, "total_score": 40},
            {"id": str(uuid.uuid4()), "username": "player9", "games_played": 20, "total_score": 80},
            {"id": str(uuid.uuid4()), "username": "player10", "games_played": 10, "total_score": 40},
            {"id": str(uuid.uuid4()), "username": "player11", "games_played": 10, "total_score": 80}
        ]
        for player in players:
            self.player_container.create_item(player)

        prompts = [
            {
                "id": "auto-gen-11",
                "username": "player8",
                "texts": [
                    {"text": "English prompt nine", "language": "en"},
                    {"text": "Prompt en español nueve", "language": "es"},
                    {"text": "Prompt in Italian nine", "language": "it"}
                ]
            },
            {
                "id": "auto-gen-12",
                "username": "player9",
                "texts": [
                    {"text": "English prompt ten", "language": "en"},
                    {"text": "Prompt en español diez", "language": "es"},
                    {"text": "Prompt in Italian ten", "language": "it"}
                ]
            },
            {
                "id": "auto-gen-13",
                "username": "player10",
                "texts": [
                    {"text": "English prompt eleven", "language": "en"},
                    {"text": "Prompt en español once", "language": "es"},
                    {"text": "Prompt in Italian eleven", "language": "it"}
                ]
            },
            {
                "id": "auto-gen-14",
                "username": "player11",
                "texts": [
                    {"text": "English prompt twelve", "language": "en"},
                    {"text": "Prompt en español doce", "language": "es"},
                    {"text": "Prompt in Italian twelve", "language": "it"}
                ]
            }
        ]
        for prompt in prompts:
            self.prompt_container.create_item(prompt)

        # Prepare the request to fetch all prompts in 'it' language for all players
        req_body = {"players": ["player8", "player9", "player10", "player11"], "language": "it"}
        req = HttpRequest(
            method='GET',
            url='/api/utils/get',
            body=json.dumps(req_body).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = utils_get(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())

        expected_output = [
            {"id": "auto-gen-11", "text": "Prompt in Italian nine", "username": "player8"},
            {"id": "auto-gen-12", "text": "Prompt in Italian ten", "username": "player9"},
            {"id": "auto-gen-13", "text": "Prompt in Italian eleven", "username": "player10"},
            {"id": "auto-gen-14", "text": "Prompt in Italian twelve", "username": "player11"}
        ]

        self.assertCountEqual(result, expected_output)

    def test_get_prompts_no_valid_usernames(self):
        """
        Test that when no usernames are valid or present, an empty list is returned.
        """
        # No players are added to the database

        # Prepare the request with usernames that do not exist
        req_body = {"players": ["nonexistent1", "nonexistent2"], "language": "en"}
        req = HttpRequest(
            method='GET',
            url='/api/utils/get',
            body=json.dumps(req_body).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = utils_get(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertEqual(result, [])

    def test_get_prompts_mixed_valid_invalid_usernames(self):
        """
        Test invalid usernames with valid (present in the DB) usernames and check that only valid ones are returned.
        """
        # Set up initial data
        valid_player = {"id": str(uuid.uuid4()), "username": "valid_player", "games_played": 10, "total_score": 50}
        self.player_container.create_item(valid_player)

        prompts = [
            {
                "id": "auto-gen-15",
                "username": "valid_player",
                "texts": [
                    {"text": "Valid player's English prompt", "language": "en"},
                    {"text": "Prompt en español válido", "language": "es"}
                ]
            },
            {
                "id": "auto-gen-16",
                "username": "valid_player",
                "texts": [
                    {"text": "Another valid English prompt", "language": "en"},
                    {"text": "Otro prompt en español válido", "language": "es"}
                ]
            }
        ]
        for prompt in prompts:
            self.prompt_container.create_item(prompt)

        # Prepare the request with a mix of valid and invalid usernames
        req_body = {"players": ["valid_player", "invalid_player1", "invalid_player2"], "language": "en"}
        req = HttpRequest(
            method='GET',
            url='/api/utils/get',
            body=json.dumps(req_body).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = utils_get(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())

        expected_output = [
            {"id": "auto-gen-15", "text": "Valid player's English prompt", "username": "valid_player"},
            {"id": "auto-gen-16", "text": "Another valid English prompt", "username": "valid_player"}
        ]

        self.assertCountEqual(result, expected_output)