# tests/test_db_utils.py

import unittest
import os
import json
import logging
from unittest import mock
from unittest.mock import patch, MagicMock

from shared_code.db_utils import CosmosDB
from azure.cosmos import CosmosClient, exceptions

class TestCosmosDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Set up the CosmosDB instance for testing.
        """
        # Load settings from local.settings.json
        settings_file = os.path.join(os.path.dirname(__file__), '..', 'local.settings.json')
        with open(settings_file) as f:
            settings = json.load(f).get('Values', {})

        # Mock environment variables
        cls.patcher = patch.dict(os.environ, settings, clear=True)
        cls.patcher.start()

        # Initialize CosmosDB instance
        try:
            cls.cosmos_db = CosmosDB()
        except ValueError as e:
            raise unittest.SkipTest(f"Skipping tests due to initialization failure: {e}")

    @classmethod
    def tearDownClass(cls):
        """
        Clean up after tests.
        """
        cls.patcher.stop()

    def test_connection_string_present(self):
        """
        Test that the CosmosDB client is initialized with the connection string.
        """
        self.assertIsNotNone(self.cosmos_db.client, "CosmosClient should be initialized.")
        logging.info("CosmosClient initialized successfully.")

    def test_database_found(self):
        """
        Test that the specified database is found.
        """
        self.assertIsNotNone(self.cosmos_db.database, "Database client should be initialized.")
        self.assertEqual(self.cosmos_db.database.database_name, os.environ.get('DATABASE_NAME'),
                         "Database name should match the environment variable.")
        logging.info(f"Database '{self.cosmos_db.database.database_name}' found successfully.")

    def test_player_container_found(self):
        """
        Test that the player container is found.
        """
        self.assertIsNotNone(self.cosmos_db.player_container, "Player container client should be initialized.")
        self.assertEqual(self.cosmos_db.player_container.container_id, os.environ.get('PLAYER_CONTAINER_NAME'),
                         "Player container name should match the environment variable.")
        logging.info(f"Player container '{self.cosmos_db.player_container.container_id}' found successfully.")

    def test_prompt_container_found(self):
        """
        Test that the prompt container is found.
        """
        self.assertIsNotNone(self.cosmos_db.prompt_container, "Prompt container client should be initialized.")
        self.assertEqual(self.cosmos_db.prompt_container.container_id, os.environ.get('PROMPT_CONTAINER_NAME'),
                         "Prompt container name should match the environment variable.")
        logging.info(f"Prompt container '{self.cosmos_db.prompt_container.container_id}' found successfully.")

    @patch('shared_code.db_utils.CosmosClient')
    def test_initialization_failure_missing_connection_string(self, mock_cosmos_client):
        """
        Test that initialization fails when the connection string is missing.
        """
        with patch.dict(os.environ, {"COSMOS_DB_CONNECTION_STRING": ""}, clear=True):
            with self.assertRaises(ValueError) as context:
                CosmosDB()
            self.assertIn("COSMOS_DB_CONNECTION_STRING not set", str(context.exception))
            logging.info("Initialization failed as expected due to missing connection string.")

    @patch('shared_code.db_utils.CosmosClient')
    def test_initialization_failure_missing_database_name(self, mock_cosmos_client):
        """
        Test that initialization fails when the database name is missing.
        """
        with patch.dict(os.environ, {"DATABASE_NAME": ""}, clear=True):
            with self.assertRaises(ValueError) as context:
                CosmosDB()
            self.assertIn("DATABASE_NAME not set", str(context.exception))
            logging.info("Initialization failed as expected due to missing database name.")

    @patch('shared_code.db_utils.CosmosClient')
    def test_initialization_failure_missing_player_container(self, mock_cosmos_client):
        """
        Test that initialization fails when the player container name is missing.
        """
        with patch.dict(os.environ, {"PLAYER_CONTAINER_NAME": ""}, clear=True):
            with self.assertRaises(ValueError) as context:
                CosmosDB()
            self.assertIn("PLAYER_CONTAINER_NAME not set", str(context.exception))
            logging.info("Initialization failed as expected due to missing player container name.")

    @patch('shared_code.db_utils.CosmosClient')
    def test_initialization_failure_missing_prompt_container(self, mock_cosmos_client):
        """
        Test that initialization fails when the prompt container name is missing.
        """
        with patch.dict(os.environ, {"PROMPT_CONTAINER_NAME": ""}, clear=True):
            with self.assertRaises(ValueError) as context:
                CosmosDB()
            self.assertIn("PROMPT_CONTAINER_NAME not set", str(context.exception))
            logging.info("Initialization failed as expected due to missing prompt container name.")

if __name__ == '__main__':
    unittest.main()
