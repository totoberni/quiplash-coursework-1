import os
import logging
from azure.cosmos import CosmosClient

class CosmosDB:
    def __init__(self):
        # Initialize Cosmos DB client
        cosmos_connection_string = os.environ.get('AzureCosmosDBConnectionString')
        if not cosmos_connection_string:
            logging.error("AzureCosmosDBConnectionString not set in environment variables")
            raise ValueError("AzureCosmosDBConnectionString not set in environment variables")

        self.client = CosmosClient.from_connection_string(cosmos_connection_string)
        self.database_name = os.environ.get('DatabaseName')
        self.player_container_name = os.environ.get('PlayerContainerName')
        self.prompt_container_name = os.environ.get('PromptContainerName')

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