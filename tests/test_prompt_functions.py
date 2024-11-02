# tests/test_prompt_functions.py

import unittest
import os
import json
import uuid
import logging
from unittest.mock import patch
from azure.functions import HttpRequest
from shared_code.db_utils import CosmosDB
from shared_code.translator_utils import Translator

# Set environment variables before importing function_app
settings_file = os.path.join(os.path.dirname(__file__), '..', 'local.settings.json')
with open(settings_file) as f:
    settings = json.load(f).get('Values', {})
# Set environment variables
for key, value in settings.items():
    os.environ[key] = value

from function_app import prompt_create, prompt_suggest, prompt_delete  # Import the specific function


class TestPromptFunctions(unittest.TestCase):
    def setUp(self):
        # Initialize CosmosDB instance
        self.cosmos_db = CosmosDB()
        self.player_container = self.cosmos_db.get_player_container()
        self.prompt_container = self.cosmos_db.get_prompt_container()
        # Initialize Translator
        self.translator = Translator()
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

    def test_prompt_create_supported_language(self):
        """
        Test creating a prompt in a supported language.
        """
        # Register a user
        username = "testuser_prompt"
        self.player_container.create_item({
            "id": str(uuid.uuid4()),
            "username": username,
            "password": "testpass123",
            "games_played": 0,
            "total_score": 0
        })

        # Prepare the request with a prompt in English
        text = "This is a test prompt that is sufficiently long."
        req = HttpRequest(
            method='POST',
            url='/api/prompt/create',
            body=json.dumps({"text": text, "username": username}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = prompt_create(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        # The response should be the prompt document
        self.assertIn('id', result)
        self.assertEqual(result['username'], username)
        self.assertIn('texts', result)
        # Verify that the texts include translations in supported languages
        texts = result['texts']
        languages_in_texts = [t['language'] for t in texts]
        # The supported languages
        expected_languages = ["en", "ga", "es", "hi", "zh-Hans", "pl"]
        # Ensure that all supported languages are included
        for lang in expected_languages:
            self.assertIn(lang, languages_in_texts)
        # Verify that the original text is included
        self.assertTrue(any(t['language'] == 'en' and t['text'] == text for t in texts))

        # Verify that the prompt is stored in the database
        query = "SELECT * FROM c WHERE c.id = @id"
        parameters = [{"name": "@id", "value": result['id']}]
        items = list(self.prompt_container.query_items(
            query=query,
            parameters=parameters,
            partition_key=username
        ))
        self.assertEqual(len(items), 1)
        prompt = items[0]
        self.assertEqual(prompt['username'], username)
        self.assertEqual(prompt['texts'], result['texts'])

    def test_prompt_create_unsupported_language(self):
        """
        Test creating a prompt in an unsupported language.
        """
        # Register a user
        username = "testuser_prompt"
        self.player_container.create_item({
            "id": str(uuid.uuid4()),
            "username": username,
            "password": "testpass123",
            "games_played": 0,
            "total_score": 0
        })

        # Prepare the request with a prompt in an unsupported language (e.g., Japanese)
        text = "これはテスト用のプロンプトです。十分な長さがあります。"
        req = HttpRequest(
            method='POST',
            url='/api/prompt/create',
            body=json.dumps({"text": text, "username": username}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = prompt_create(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Unsupported language')

    def test_prompt_create_prompt_too_short(self):
        """
        Test creating a prompt that is too short.
        """
        # Register a user
        username = "testuser_prompt"
        self.player_container.create_item({
            "id": str(uuid.uuid4()),
            "username": username,
            "password": "testpass123",
            "games_played": 0,
            "total_score": 0
        })

        # Prepare the request with a prompt that is less than 20 characters
        text = "Too short prompt"
        req = HttpRequest(
            method='POST',
            url='/api/prompt/create',
            body=json.dumps({"text": text, "username": username}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = prompt_create(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Prompt less than 20 characters or more than 100 characters')

    def test_prompt_create_prompt_too_long(self):
        """
        Test creating a prompt that is too long.
        """
        # Register a user
        username = "testuser_prompt"
        self.player_container.create_item({
            "id": str(uuid.uuid4()),
            "username": username,
            "password": "testpass123",
            "games_played": 0,
            "total_score": 0
        })

        # Prepare the request with a prompt that is more than 100 characters
        text = "This is a very long prompt that exceeds the maximum allowed length. " \
               "It is supposed to be more than one hundred characters in length, " \
               "which should cause validation to fail."
        req = HttpRequest(
            method='POST',
            url='/api/prompt/create',
            body=json.dumps({"text": text, "username": username}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = prompt_create(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Prompt less than 20 characters or more than 100 characters')

    def test_prompt_create_player_does_not_exist(self):
        """
        Test creating a prompt when the player does not exist.
        """
        # Do not register the user

        # Prepare the request
        username = "nonexistent_user"
        text = "This is a test prompt that is sufficiently long."
        req = HttpRequest(
            method='POST',
            url='/api/prompt/create',
            body=json.dumps({"text": text, "username": username}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = prompt_create(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Player does not exist')
    
    def test_prompt_suggest_valid_keyword(self):
        """
        Test prompt suggestion with a valid keyword.
        """
        # Prepare the request with a valid keyword
        keyword = "advantage"
        req = HttpRequest(
            method='POST',
            url='/api/prompt/suggest',
            body=json.dumps({"keyword": keyword}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = prompt_suggest(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        suggestion = result.get('suggestion', '')
        self.assertIn(keyword.lower(), suggestion.lower())
        self.assertGreaterEqual(len(suggestion), 20)
        self.assertLessEqual(len(suggestion), 100)

    def test_prompt_suggest_invalid_keyword(self):
        """
        Test prompt suggestion with an invalid keyword (e.g., empty string).
        """
        # Prepare the request with an invalid keyword
        keyword = ""
        req = HttpRequest(
            method='POST',
            url='/api/prompt/suggest',
            body=json.dumps({"keyword": keyword}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = prompt_suggest(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertEqual(result.get('suggestion'), 'Cannot generate suggestion')

    def test_prompt_suggest_cannot_generate_suggestion(self):
        """
        Test prompt suggestion when the LLM cannot generate a valid prompt after maximum attempts.
        """
        # Mock the PromptAdvisor's generate_prompt method to return 'Cannot generate suggestion'
        with patch('shared_code.prompt_advisor.PromptAdvisor.generate_prompt') as mock_generate_prompt:
            mock_generate_prompt.return_value = {"suggestion": "Cannot generate suggestion"}

            # Prepare the request with a valid keyword
            keyword = "difficultkeyword"
            req = HttpRequest(
                method='POST',
                url='/api/prompt/suggest',
                body=json.dumps({"keyword": keyword}).encode('utf8'),
                headers={'Content-Type': 'application/json'}
            )

            # Call the function
            resp = prompt_suggest(req)

            # Verify the response
            self.assertEqual(resp.status_code, 200)
            result = json.loads(resp.get_body())
            self.assertEqual(result.get('suggestion'), 'Cannot generate suggestion')

    def test_prompt_suggest_keyword_not_in_prompt(self):
        """
        Test prompt suggestion when the generated prompt does not include the keyword.
        """
        # Mock the PromptAdvisor's is_valid_prompt method to return False
        with patch('shared_code.prompt_advisor.PromptAdvisor.is_valid_prompt') as mock_is_valid_prompt:
            mock_is_valid_prompt.return_value = False

            # Prepare the request with a valid keyword
            keyword = "testkeyword"
            req = HttpRequest(
                method='POST',
                url='/api/prompt/suggest',
                body=json.dumps({"keyword": keyword}).encode('utf8'),
                headers={'Content-Type': 'application/json'}
            )

            # Call the function
            resp = prompt_suggest(req)

            # Since the is_valid_prompt method is mocked to return False, after MAX_ATTEMPTS,
            # the function should return 'Cannot generate suggestion'

            # Verify the response
            result = json.loads(resp.get_body())
            self.assertEqual(result.get('suggestion'), 'Cannot generate suggestion')
    # This test fails :((
    def test_prompt_delete_existing_player_with_prompts(self):
        """
        Test deleting prompts for an existing player who has prompts.
        """
        # Set up initial data
        # Players
        players = [
            {"id": str(uuid.uuid4()), "username": "py_luis", "password": "pass123", "games_played": 0, "total_score": 0},
            {"id": str(uuid.uuid4()), "username": "js_packer", "password": "pass123", "games_played": 0, "total_score": 0},
            {"id": str(uuid.uuid4()), "username": "les_cobol", "password": "pass123", "games_played": 0, "total_score": 0}
        ]
        for player in players:
            self.player_container.create_item(player)

        # Prompts
        prompts = [
            {
                "id": str(uuid.uuid4()),
                "username": "py_luis",
                "texts": [
                    {"text": "The most useless Python one-line program", "language": "en"},
                    {"text": "El programa de una línea en Python más inútil", "language": "es"}
                ]
            },
            {
                "id": str(uuid.uuid4()),
                "username": "py_luis",
                "texts": [
                    {"text": "Why the millenial crossed the avenue?", "language": "en"},
                    {"text": "¿Por qué el millenial cruzó la avenida?", "language": "es"}
                ]
            },
            {
                "id": str(uuid.uuid4()),
                "username": "js_packer",
                "texts": [
                    {"text": "Why the ka-boomer crossed the road?", "language": "en"},
                    {"text": "¿Por qué el ka-boomer cruzó la calle?", "language": "es"}
                ]
            },
            {
                "id": str(uuid.uuid4()),
                "username": "les_cobol",
                "texts": [
                    {"text": "Why the boomer crossed the road?", "language": "en"},
                    {"text": "¿Por qué el boomer cruzó la calle?", "language": "es"}
                ]
            }
        ]
        for prompt in prompts:
            re = self.prompt_container.create_item(prompt)
            response = re  # 're' is already a dict
            print('-------------------------------------TEST-------------------------------------')
            print(json.dumps(response, indent=2))  # Pretty-print the JSON response


        # Prepare the request
        req = HttpRequest(
            method='POST',
            url='/api/prompt/delete',
            body=json.dumps({"player": "py_luis"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = prompt_delete(req)
        print('-------------------------------------TEST-------------------------------------')
        print(resp.get_body())

        # Verify the response
        #Test fails here
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertTrue(result['result'])
        self.assertEqual(result['msg'], '2 prompts deleted')

        # Verify that prompts by 'py_luis' are deleted
        remaining_prompts = list(self.prompt_container.read_all_items())
        remaining_usernames = set(p['username'] for p in remaining_prompts)
        self.assertNotIn('py_luis', remaining_usernames)
        self.assertEqual(len(remaining_prompts), 2)
        self.assertEqual(remaining_usernames, {'js_packer', 'les_cobol'})

    def test_prompt_delete_existing_player_no_prompts(self):
        """
        Test deleting prompts for an existing player who has no prompts.
        """
        # Set up initial data
        # Players
        player = {"id": str(uuid.uuid4()), "username": "no_prompts_player", "password": "pass123", "games_played": 0, "total_score": 0}
        self.player_container.create_item(player)

        # No prompts for this player

        # Prepare the request
        req = HttpRequest(
            method='POST',
            url='/api/prompt/delete',
            body=json.dumps({"player": "no_prompts_player"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = prompt_delete(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertTrue(result['result'])
        self.assertEqual(result['msg'], '0 prompts deleted')

    def test_prompt_delete_nonexistent_player(self):
        """
        Test deleting prompts for a player who does not exist in the database.
        """
        # No players in the database

        # Prepare the request
        req = HttpRequest(
            method='POST',
            url='/api/prompt/delete',
            body=json.dumps({"player": "ghost_player"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = prompt_delete(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        # According to the specification, we assume "player" exists, no need to check existence
        # So we proceed to delete prompts for 'ghost_player', which results in 0 prompts deleted
        self.assertTrue(result['result'])
        self.assertEqual(result['msg'], '0 prompts deleted')

    def test_prompt_delete_missing_player_field(self):
        """
        Test deleting prompts when the 'player' field is missing in the request.
        """
        # Prepare the request with missing 'player' field
        req = HttpRequest(
            method='POST',
            url='/api/prompt/delete',
            body=json.dumps({}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = prompt_delete(req)

        # Verify the response
        self.assertEqual(resp.status_code, 400)
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Player username missing')

    def test_prompt_delete_invalid_json(self):
        """
        Test deleting prompts with invalid JSON input.
        """
        # Prepare the request with invalid JSON
        req = HttpRequest(
            method='POST',
            url='/api/prompt/delete',
            body=b'{"player": "username"',  # Missing closing brace
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = prompt_delete(req)

        # Verify the response
        self.assertEqual(resp.status_code, 400)
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Invalid JSON input')