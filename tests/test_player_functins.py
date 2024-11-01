import unittest
import os
import json
import logging
from azure.functions import HttpRequest
from azure.cosmos import exceptions
from shared_code.db_utils import CosmosDB

# Set environment variables before importing function_app
settings_file = os.path.join(os.path.dirname(__file__), '..', 'local.settings.json')
with open(settings_file) as f:
    settings = json.load(f).get('Values', {})
# Set environment variables
for key, value in settings.items():
    os.environ.update(settings)

from function_app import player_register  # Import the specific function

class TestPlayerFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize CosmosDB instance
        cls.cosmos_db = CosmosDB()
        cls.player_container = cls.cosmos_db.get_player_container()
        # Clear the player container before running tests
        cls._clean_up_database()

    @classmethod
    def tearDownClass(cls):
        # Clean up after tests
        cls._clean_up_database()

    @classmethod
    def _clean_up_database(cls):
        items = list(cls.player_container.read_all_items())
        for item in items:
            cls.player_container.delete_item(item=item['id'], partition_key=item['id'])

    def test_register_player_when_db_empty(self):
        """
        Test registering a player when the database is empty.
        """
        # Prepare the request
        req = HttpRequest(
            method='POST',
            url='/api/player/register',
            body=json.dumps({"username": "testuser", "password": "testpass123"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function directly
        resp = player_register(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertTrue(result['result'])
        self.assertEqual(result['msg'], 'OK')

        # Verify that the player is in the database
        try:
            query = "SELECT * FROM c WHERE c.username = @username"
            parameters = [{"name": "@username", "value": "testuser"}]
            items = list(self.player_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            self.assertEqual(len(items), 1)
            player = items[0]
            self.assertEqual(player['username'], 'testuser')
            self.assertEqual(player['password'], 'testpass123')
            self.assertEqual(player['games_played'], 0)
            self.assertEqual(player['total_score'], 0)
        except exceptions.CosmosResourceNotFoundError:
            self.fail("Player not found in database after registration.")
