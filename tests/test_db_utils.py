# tests/test_db_utils.py

import unittest
import os
import json
import logging

from shared_code.db_utils import CosmosDB
from azure.cosmos import exceptions

class TestCosmosDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Set up the CosmosDB instance for testing by loading environment variables
        from local.settings.json and initializing the CosmosDB class.
        """
        # Load settings from local.settings.json
        settings_file = os.path.join(os.path.dirname(__file__), '..', 'local.settings.json')
        try:
            with open(settings_file) as f:
                settings = json.load(f).get('Values', {})
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find {settings_file}. Ensure it exists and is correctly formatted.")

        # Set environment variables
        for key, value in settings.items():
            os.environ[key] = value

        # Initialize CosmosDB instance
        try:
            cls.cosmos_db = CosmosDB()
            logging.info("CosmosDB instance initialized successfully.")
        except ValueError as e:
            cls.cosmos_db = None
            logging.error(f"Initialization failed: {e}")

    def test_connection_string_exists(self):
        """Test that the COSMOS_DB_CONNECTION_STRING environment variable exists."""
        connection_string = os.environ.get('AzureCosmosDBConnectionString')
        self.assertIsNotNone(connection_string, "AzureCosmosDBConnectionString is not set.")
        logging.info("AzureCosmosDBConnectionString exists.")

    def test_connection_string_leads_to_connection(self):
        """Test that the connection string can be used to connect to Cosmos DB."""
        if self.cosmos_db is None:
            self.fail("CosmosDB instance was not initialized due to missing or invalid connection string.")

        try:
            # Attempt to list databases to verify connection
            databases = list(self.cosmos_db.client.list_databases())
            self.assertIsInstance(databases, list, "Databases should be returned as a list.")
            logging.info("Successfully connected to Cosmos DB and retrieved databases.")
        except exceptions.CosmosHttpResponseError as e:
            self.fail(f"Failed to connect to Cosmos DB: {e.message}")
        except Exception as e:
            self.fail(f"An unexpected error occurred while connecting to Cosmos DB: {str(e)}")

    def test_containers_fetched(self):
        """Test that the database and container names are set in the environment variables."""
        try: 
            player_container_name = CosmosDB.get_prompt_container
            prompt_container_name = CosmosDB.get_player_container
            self.assertIsNotNone(player_container_name, "PlayerContainerName is not set.")
            self.assertIsNotNone(prompt_container_name, "PromptContainerName is not set.")
            logging.info("Database and container names are set in the environment variables.")
        except Exception as e:
            self.fail(f"An unexpected error occurred while checking environment variables: {str(e)}")

if __name__ == '__main__':
    # Configure logging to display INFO level messages
    logging.basicConfig(level=logging.INFO)
    unittest.main()