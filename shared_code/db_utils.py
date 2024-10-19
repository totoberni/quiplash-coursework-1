import os
import logging
from azure.cosmos import CosmosClient

class CosmosDB:
    def __init__(self):
        # Initialize Cosmos DB client
        cosmos_connection_string = os.environ.get('COSMOS_DB_CONNECTION_STRING')
        if not cosmos_connection_string:
            logging.error("COSMOS_DB_CONNECTION_STRING not set in environment variables")
            raise ValueError("COSMOS_DB_CONNECTION_STRING not set in environment variables")

        self.client = CosmosClient.from_connection_string(cosmos_connection_string)
        self.database_name = os.environ.get('DATABASE_NAME')
        self.player_container_name = os.environ.get('PLAYER_CONTAINER_NAME')
        self.prompt_container_name = os.environ.get('PROMPT_CONTAINER_NAME')

        if not self.database_name:
            logging.error("DATABASE_NAME not set in environment variables")
            raise ValueError("DATABASE_NAME not set in environment variables")

        if not self.player_container_name:
            logging.error("PLAYER_CONTAINER_NAME not set in environment variables")
            raise ValueError("PLAYER_CONTAINER_NAME not set in environment variables")

        if not self.prompt_container_name:
            logging.error("PROMPT_CONTAINER_NAME not set in environment variables")
            raise ValueError("PROMPT_CONTAINER_NAME not set in environment variables")

        self.database = self.client.get_database_client(self.database_name)
        self.player_container = self.database.get_container_client(self.player_container_name)
        self.prompt_container = self.database.get_container_client(self.prompt_container_name)
    
    def get_player_container(self):
        return self.player_container
    
    def get_prompt_container(self):
        return self.prompt_container