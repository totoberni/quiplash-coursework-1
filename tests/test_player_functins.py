import unittest
import os
import json
import uuid
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

from function_app import player_register, player_login, player_update  # Import the specific function

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
        
        self._clean_up_database()

    def test_register_player_when_db_not_empty(self):
        """
        Test registering a player when the database is not empty.
        """
        # Add an existing player to the database
        existing_player = {
            "id": str(uuid.uuid4()),
            "username": "existinguser",
            "password": "existingpass123",
            "games_played": 0,
            "total_score": 0
        }
        self.player_container.create_item(existing_player)

        # Prepare the request for a new user
        req = HttpRequest(
            method='POST',
            url='/api/player/register',
            body=json.dumps({"username": "testuser2", "password": "testpass456"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_register(req)
        print('------------------------TEST-------------------- ',resp.get_body())

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertTrue(result['result'])
        self.assertEqual(result['msg'], 'OK')

        # Verify that the new player is in the database
        query = "SELECT * FROM c WHERE c.username = @username"
        parameters = [{"name": "@username", "value": "testuser2"}]
        items = list(self.player_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        self.assertEqual(len(items), 1)
        player = items[0]
        self.assertEqual(player['username'], 'testuser2')
        self.assertEqual(player['password'], 'testpass456')
        self.assertEqual(player['games_played'], 0)
        self.assertEqual(player['total_score'], 0)
        self._clean_up_database()

    def test_register_existing_username(self):
        """
        Test attempting to register a username that already exists.
        """
        # Add an existing player to the database
        existing_player = {
            "id": str(uuid.uuid4()),
            "username": "duplicateuser",
            "password": "password123",
            "games_played": 0,
            "total_score": 0
        }
        self.player_container.create_item(existing_player)

        # Prepare the request with the same username
        req = HttpRequest(
            method='POST',
            url='/api/player/register',
            body=json.dumps({"username": "duplicateuser", "password": "newpassword456"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_register(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Username already exists')
        self._clean_up_database()

    def test_register_username_too_short(self):
        """
        Test registering a player with a username that is too short.
        """
        # Prepare the request
        req = HttpRequest(
            method='POST',
            url='/api/player/register',
            body=json.dumps({"username": "usr", "password": "validpass123"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_register(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Username less than 5 characters or more than 15 characters')
        self._clean_up_database()

    def test_register_username_too_long(self):
        """
        Test registering a player with a username that is too long.
        """
        long_username = 'u' * 16  # 16 characters
        # Prepare the request
        req = HttpRequest(
            method='POST',
            url='/api/player/register',
            body=json.dumps({"username": long_username, "password": "validpass123"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_register(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Username less than 5 characters or more than 15 characters')
        self._clean_up_database()

    def test_register_password_too_short(self):
        """
        Test registering a player with a password that is too short.
        """
        # Prepare the request
        req = HttpRequest(
            method='POST',
            url='/api/player/register',
            body=json.dumps({"username": "validuser", "password": "short"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_register(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Password less than 8 characters or more than 15 characters')
        self._clean_up_database()

    def test_register_password_too_long(self):
        """
        Test registering a player with a password that is too long.
        """
        long_password = 'p' * 16  # 16 characters
        # Prepare the request
        req = HttpRequest(
            method='POST',
            url='/api/player/register',
            body=json.dumps({"username": "validuser", "password": long_password}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_register(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Password less than 8 characters or more than 15 characters')
        self._clean_up_database()

    def test_register_boundary_username_length(self):
        """
        Test registering users with username lengths at the boundary values.
        """
        # Username length 5 (minimum valid length)
        username_min = 'user1'
        req_min = HttpRequest(
            method='POST',
            url='/api/player/register',
            body=json.dumps({"username": username_min, "password": "validpass"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )
        resp_min = player_register(req_min)
        result_min = json.loads(resp_min.get_body())
        self.assertTrue(result_min['result'])
        self.assertEqual(result_min['msg'], 'OK')

        # Username length 15 (maximum valid length)
        username_max = 'u' * 15
        req_max = HttpRequest(
            method='POST',
            url='/api/player/register',
            body=json.dumps({"username": username_max, "password": "validpass"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )
        resp_max = player_register(req_max)
        result_max = json.loads(resp_max.get_body())
        self.assertTrue(result_max['result'])
        self.assertEqual(result_max['msg'], 'OK')
        self._clean_up_database()

    def test_register_boundary_password_length(self):
        """
        Test registering users with password lengths at the boundary values.
        """
        # Password length 8 (minimum valid length)
        password_min = 'pass1234'
        req_min = HttpRequest(
            method='POST',
            url='/api/player/register',
            body=json.dumps({"username": "userboundary1", "password": password_min}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )
        resp_min = player_register(req_min)
        result_min = json.loads(resp_min.get_body())
        self.assertTrue(result_min['result'])
        self.assertEqual(result_min['msg'], 'OK')

        # Password length 15 (maximum valid length)
        password_max = 'p' * 15
        req_max = HttpRequest(
            method='POST',
            url='/api/player/register',
            body=json.dumps({"username": "userboundary2", "password": password_max}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )
        resp_max = player_register(req_max)
        result_max = json.loads(resp_max.get_body())
        self.assertTrue(result_max['result'])
        self.assertEqual(result_max['msg'], 'OK')
        self._clean_up_database()

    def test_register_missing_username(self):
        """
        Test registering a player with a missing username field.
        """
        # Prepare the request without username
        req = HttpRequest(
            method='POST',
            url='/api/player/register',
            body=json.dumps({"password": "validpass123"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_register(req)

        # Verify the response (although the spec says assume input is well-formed, it's good practice to test)
        self.assertEqual(resp.status_code, 400)  # Bad Request
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        # The message can be 'Username or password missing' as per your implementation
        self.assertEqual(result['msg'], 'Username or password missing')
        self._clean_up_database()

    def test_register_missing_password(self):
        """
        Test registering a player with a missing password field.
        """
        # Prepare the request without password
        req = HttpRequest(
            method='POST',
            url='/api/player/register',
            body=json.dumps({"username": "validuser"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_register(req)

        # Verify the response
        self.assertEqual(resp.status_code, 400)  # Bad Request
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Username or password missing')
        self._clean_up_database()

    def test_register_invalid_json(self):
        """
        Test registering a player with invalid JSON input.
        """
        # Prepare the request with invalid JSON
        req = HttpRequest(
            method='POST',
            url='/api/player/register',
            body=b'{"username": "user", "password": "pass123"',  # Missing closing brace
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_register(req)

        # Verify the response
        self.assertEqual(resp.status_code, 400)  # Bad Request
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Invalid JSON input')
        self._clean_up_database()


    def test_login_existing_user_correct_password(self):
        """
        Test logging in with an existing user and correct password.
        """
        # First, register the user
        self.player_container.create_item({
            "id": str(uuid.uuid4()),
            "username": "testuser1",
            "password": "correctpassword",
            "games_played": 0,
            "total_score": 0
        })

        # Prepare the request
        req = HttpRequest(
            method='GET',
            url='/api/player/login',
            body=json.dumps({"username": "testuser1", "password": "correctpassword"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_login(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertTrue(result['result'])
        self.assertEqual(result['msg'], 'OK')
        self._clean_up_database()

    def test_login_existing_user_wrong_password(self):
        """
        Test logging in with an existing user and wrong password.
        """
        # First, register the user
        self.player_container.create_item({
            "id": str(uuid.uuid4()),
            "username": "testuser2",
            "password": "correctpassword",
            "games_played": 0,
            "total_score": 0
        })

        # Prepare the request
        req = HttpRequest(
            method='GET',
            url='/api/player/login',
            body=json.dumps({"username": "testuser2", "password": "wrongpassword"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_login(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Username or password incorrect')
        self._clean_up_database()

    def test_login_nonexistent_user(self):
        """
        Test logging in with a non-existent user.
        """
        # Prepare the request
        req = HttpRequest(
            method='GET',
            url='/api/player/login',
            body=json.dumps({"username": "nonexistentuser", "password": "any_password"}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_login(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Username or password incorrect')
        self._clean_up_database()
    
    def test_update_existing_player_positive_increments(self):
        """
        Test updating an existing player with positive increments.
        """
        # First, register the user
        self.player_container.create_item({
            "id": str(uuid.uuid4()),
            "username": "testuser_update",
            "password": "testpass123",
            "games_played": 10,
            "total_score": 100
        })

        # Prepare the request
        req = HttpRequest(
            method='PUT',
            url='/api/player/update',
            body=json.dumps({"username": "testuser_update", "add_to_games_played": 5, "add_to_score": 50}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_update(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertTrue(result['result'])
        self.assertEqual(result['msg'], 'OK')

        # Verify that the player's games_played and total_score are updated correctly
        query = "SELECT * FROM c WHERE c.username = @username"
        parameters = [{"name": "@username", "value": "testuser_update"}]
        items = list(self.player_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        self.assertEqual(len(items), 1)
        player = items[0]
        self.assertEqual(player['games_played'], 15)  # 10 + 5
        self.assertEqual(player['total_score'], 150)  # 100 + 50
        self._clean_up_database()

    def test_update_existing_player_zero_increments(self):
        """
        Test updating an existing player with zero increments.
        """
        # First, register the user
        self.player_container.create_item({
            "id": str(uuid.uuid4()),
            "username": "testuser_update_zero",
            "password": "testpass123",
            "games_played": 10,
            "total_score": 100
        })

        # Prepare the request
        req = HttpRequest(
            method='PUT',
            url='/api/player/update',
            body=json.dumps({"username": "testuser_update_zero", "add_to_games_played": 0, "add_to_score": 0}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_update(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertTrue(result['result'])
        self.assertEqual(result['msg'], 'OK')

        # Verify that the player's games_played and total_score remain the same
        query = "SELECT * FROM c WHERE c.username = @username"
        parameters = [{"name": "@username", "value": "testuser_update_zero"}]
        items = list(self.player_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        self.assertEqual(len(items), 1)
        player = items[0]
        self.assertEqual(player['games_played'], 10)  # 10 + 0
        self.assertEqual(player['total_score'], 100)  # 100 + 0
        self._clean_up_database()

    def test_update_existing_player_negative_increments(self):
        """
        Test updating an existing player with negative increments.
        """
        # First, register the user
        self.player_container.create_item({
            "id": str(uuid.uuid4()),
            "username": "testuser_update_negative",
            "password": "testpass123",
            "games_played": 10,
            "total_score": 100
        })

        # Prepare the request
        req = HttpRequest(
            method='PUT',
            url='/api/player/update',
            body=json.dumps({"username": "testuser_update_negative", "add_to_games_played": -5, "add_to_score": -50}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_update(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertTrue(result['result'])
        self.assertEqual(result['msg'], 'OK')

        # Verify that the player's games_played and total_score are updated correctly
        query = "SELECT * FROM c WHERE c.username = @username"
        parameters = [{"name": "@username", "value": "testuser_update_negative"}]
        items = list(self.player_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        self.assertEqual(len(items), 1)
        player = items[0]
        self.assertEqual(player['games_played'], 5)  # 10 + (-5)
        self.assertEqual(player['total_score'], 50)  # 100 + (-50)
        self._clean_up_database()

    def test_update_existing_player_to_negative_values(self):
        """
        Test updating an existing player with negative increments that would result in negative totals.
        """
        # First, register the user
        self.player_container.create_item({
            "id": str(uuid.uuid4()),
            "username": "testuser_negative_total",
            "password": "testpass123",
            "games_played": 5,
            "total_score": 40
        })

        # Prepare the request
        req = HttpRequest(
            method='PUT',
            url='/api/player/update',
            body=json.dumps({"username": "testuser_negative_total", "add_to_games_played": -10, "add_to_score": -50}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_update(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertTrue(result['result'])
        self.assertEqual(result['msg'], 'OK')

        # Verify that the player's games_played and total_score are not negative
        query = "SELECT * FROM c WHERE c.username = @username"
        parameters = [{"name": "@username", "value": "testuser_negative_total"}]
        items = list(self.player_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        self.assertEqual(len(items), 1)
        player = items[0]
        self.assertEqual(player['games_played'], 0)  # Should not be negative
        self.assertEqual(player['total_score'], 0)  # Should not be negative
        self._clean_up_database()

    def test_update_nonexistent_player(self):
        """
        Test updating a non-existent player.
        """
        # Ensure the database does not have the player
        self._clean_up_database()

        # Prepare the request
        req = HttpRequest(
            method='PUT',
            url='/api/player/update',
            body=json.dumps({"username": "nonexistentuser", "add_to_games_played": 5, "add_to_score": 50}).encode('utf8'),
            headers={'Content-Type': 'application/json'}
        )

        # Call the function
        resp = player_update(req)

        # Verify the response
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.get_body())
        self.assertFalse(result['result'])
        self.assertEqual(result['msg'], 'Player does not exist')
        self._clean_up_database()