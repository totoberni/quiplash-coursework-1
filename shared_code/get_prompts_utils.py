# shared_code/get_prompts_utils.py

import logging

class GetPrompts:
    def __init__(self, prompt_container):
        """
        Initializes the GetPrompts utility with the given prompt container.
        
        Parameters:
            prompt_container: The Cosmos DB container for prompts.
        """
        self.prompt_container = prompt_container

    def retrieve_prompts(self, players, language):
        """
        Retrieves all prompts' texts in the specified language created by the given players.

        Parameters:
            players (list): List of usernames.
            language (str): Language code to filter prompts.

        Returns:
            list: List of dictionaries with keys 'id', 'text', and 'username'.
        """
        result = []
        try:
            for player in players:
                # Query prompts by username
                query = "SELECT * FROM c WHERE c.username = @username"
                parameters = [{"name": "@username", "value": player}]
                prompts = list(self.prompt_container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))

                for prompt in prompts:
                    # Find the text in the specified language
                    for text_entry in prompt.get('texts', []):
                        if text_entry.get('language') == language:
                            result.append({
                                "id": prompt.get('id'),
                                "text": text_entry.get('text'),
                                "username": prompt.get('username')
                            })
                            break  # Assuming one text per language per prompt

            return result

        except Exception as e:
            logging.error(f"Error retrieving prompts: {e}")
            raise e
