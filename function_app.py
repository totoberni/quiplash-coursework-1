# function_app.py

import azure.functions as func
import logging
import os
import json
import uuid

from shared_code.db_utils import CosmosDB
from shared_code.prompt_advisor import PromptAdvisor
from shared_code.translator_utils import Translator
from shared_code.podium_utils import PodiumUtils
from shared_code.get_prompts_utils import GetPrompts 

# Initialize CosmosDB instance
cosmos_db = CosmosDB()
player_container = cosmos_db.get_player_container()
prompt_container = cosmos_db.get_prompt_container()

# Initialize shared classes with helper code
advisor = PromptAdvisor()
translator = Translator()
podium_utils = PodiumUtils(player_container)
prompts_utils = GetPrompts(prompt_container)
app = func.FunctionApp()

# Player_Register
@app.route(route="player/register", methods=['POST'], auth_level=func.AuthLevel.FUNCTION)
def player_register(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing /player/register request')
    
    try:
        req_body = req.get_json()
    except ValueError:
        logging.error("Invalid JSON input")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "Invalid JSON input"}),
            mimetype="application/json",
            status_code=400
        )
    
    username = req_body.get('username')
    password = req_body.get('password')

    # Validate presence of username and password
    if username is None or password is None:
        logging.warning("Username or password missing in the request")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "Username or password missing"}),
            mimetype="application/json",
            status_code=400
        )
    
    # Validate username length
    if not (5 <= len(username) <= 15):
        logging.warning(f"Invalid username length: {len(username)} characters")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "Username less than 5 characters or more than 15 characters"}),
            mimetype="application/json",
            status_code=200
        )
    
    # Validate password length
    if not (8 <= len(password) <= 15):
        logging.warning(f"Invalid password length: {len(password)} characters")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "Password less than 8 characters or more than 15 characters"}),
            mimetype="application/json",
            status_code=200
        )
    
    # Check if username already exists by querying the container
    try:
        query = "SELECT * FROM c WHERE c.username = @username"
        parameters = [{"name": "@username", "value": username}]
        items = list(player_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if len(items) > 0:
            logging.info(f"Username '{username}' already exists")
            return func.HttpResponse(
                json.dumps({"result": False, "msg": "Username already exists"}),
                mimetype="application/json",
                status_code=200
            )
    except Exception as e:
        logging.error(f"Error querying for existing username: {e}")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "An error occurred while checking username existence"}),
            mimetype="application/json",
            status_code=500
        )
    
    # Create the player document
    player_doc = {
        "id": str(uuid.uuid4()),  # Generating a unique UUID for the 'id' field
        "username": username,
        "password": password,
        "games_played": 0,
        "total_score": 0
    }
    
    # Insert the new player into the database
    try:
        player_container.create_item(body=player_doc)
        logging.info(f"Player '{username}' registered successfully with ID '{player_doc['id']}'")
        return func.HttpResponse(
            json.dumps({"result": True, "msg": "OK"}),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error inserting new player: {e}")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "An error occurred while registering the player"}),
            mimetype="application/json",
            status_code=500
        )
    except Exception as e:
        logging.error(f"Unexpected error in /player/register: {e}")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "An unexpected error occurred"}),
            mimetype="application/json",
            status_code=500
        )
    
# Player_Login
@app.route(route="player/login", methods=['GET', 'POST'], auth_level=func.AuthLevel.FUNCTION)
def player_login(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing /player/login request')

    try:
        req_body = req.get_json()
    except ValueError:
        logging.error("Invalid JSON input")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "Invalid JSON input"}),
            mimetype="application/json",
            status_code=400
        )

    username = req_body.get('username')
    password = req_body.get('password')

    # Validate presence of username and password
    if username is None or password is None:
        logging.warning("Username or password missing in the request")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "Username or password incorrect"}),
            mimetype="application/json",
            status_code=200
        )

    # Query the player container for the username
    try:
        query = "SELECT * FROM c WHERE c.username = @username"
        parameters = [{"name": "@username", "value": username}]
        items = list(player_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

        if not items:
            logging.info(f"Username '{username}' not found")
            return func.HttpResponse(
                json.dumps({"result": False, "msg": "Username or password incorrect"}),
                mimetype="application/json",
                status_code=200
            )
        else:
            player = items[0]
            if player.get('password') == password:
                logging.info(f"User '{username}' logged in successfully")
                return func.HttpResponse(
                    json.dumps({"result": True, "msg": "OK"}),
                    mimetype="application/json",
                    status_code=200
                )
            else:
                logging.info(f"Password mismatch for user '{username}'")
                return func.HttpResponse(
                    json.dumps({"result": False, "msg": "Username or password incorrect"}),
                    mimetype="application/json",
                    status_code=200
                )
    except Exception as e:
        logging.error(f"Error querying for username '{username}': {e}")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "An error occurred while checking username and password"}),
            mimetype="application/json",
            status_code=500
        )
    
# Player_Update
@app.route(route="player/update", methods=['PUT'], auth_level=func.AuthLevel.FUNCTION)
def player_update(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing /player/update request')

    try:
        req_body = req.get_json()
    except ValueError:
        logging.error("Invalid JSON input")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "Invalid JSON input"}),
            mimetype="application/json",
            status_code=400
        )

    username = req_body.get('username')
    add_to_games_played = req_body.get('add_to_games_played')
    add_to_score = req_body.get('add_to_score')

    # Validate presence of username and increment values
    if username is None or add_to_games_played is None or add_to_score is None:
        logging.warning("Username or increment values missing in the request")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "Invalid input data"}),
            mimetype="application/json",
            status_code=400
        )

    # Query the player container for the username
    try:
        query = "SELECT * FROM c WHERE c.username = @username"
        parameters = [{"name": "@username", "value": username}]
        items = list(player_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

        if not items:
            logging.info(f"Username '{username}' not found")
            return func.HttpResponse(
                json.dumps({"result": False, "msg": "Player does not exist"}),
                mimetype="application/json",
                status_code=200
            )
        else:
            player = items[0]
            # Update the player's games_played and total_score
            player['games_played'] += add_to_games_played
            player['total_score'] += add_to_score

            # Ensure that games_played and total_score are >= 0
            if player['games_played'] < 0:
                player['games_played'] = 0
            if player['total_score'] < 0:
                player['total_score'] = 0

            # Replace the item in the database
            player_container.replace_item(item=player, body=player)

            logging.info(f"User '{username}' updated successfully")
            return func.HttpResponse(
                json.dumps({"result": True, "msg": "OK"}),
                mimetype="application/json",
                status_code=200
            )
    except Exception as e:
        logging.error(f"Error updating player '{username}': {e}")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "An error occurred while updating the player"}),
            mimetype="application/json",
            status_code=500
        )

# Prompt_Create
@app.route(route="prompt/create", methods=['POST'], auth_level=func.AuthLevel.FUNCTION)
def prompt_create(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing /prompt/create request')

    try:
        req_body = req.get_json()
    except ValueError:
        logging.error("Invalid JSON input")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "Invalid JSON input"}),
            mimetype="application/json",
            status_code=400
        )

    text = req_body.get('text')
    username = req_body.get('username')

    # Validate presence of text and username
    if text is None or username is None:
        logging.warning("Text or username missing in the request")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "Text or username missing"}),
            mimetype="application/json",
            status_code=400
        )

    # Validate prompt length
    if not (20 <= len(text) <= 100):
        logging.warning(f"Invalid prompt length: {len(text)} characters")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "Prompt less than 20 characters or more than 100 characters"}),
            mimetype="application/json",
            status_code=200
        )

    # Check if player exists in the player container
    try:
        query = "SELECT * FROM c WHERE c.username = @username"
        parameters = [{"name": "@username", "value": username}]
        player_items = list(player_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

        if not player_items:
            logging.info(f"Player '{username}' does not exist")
            return func.HttpResponse(
                json.dumps({"result": False, "msg": "Player does not exist"}),
                mimetype="application/json",
                status_code=200
            )
    except Exception as e:
        logging.error(f"Error querying for player '{username}': {e}")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "An error occurred while checking player existence"}),
            mimetype="application/json",
            status_code=500
        )
    
    # Check if the prompt already exists 
    try:
        query = "SELECT * FROM c WHERE c.username = @username AND ARRAY_CONTAINS(c.texts, {'text': @text})"
        parameters = [
            {"name": "@username", "value": username},
            {"name": "@text", "value": text}
        ]
        prompt_items = list(prompt_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

        if prompt_items:
            logging.info(f"Prompt already exists for player '{username}'")
            return func.HttpResponse(
                json.dumps({"result": False, "msg": "Prompt already exists"}),
                mimetype="application/json",
                status_code=200
            )
    except Exception as e:
        logging.error(f"Error querying for existing prompt: {e}")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "An error occurred while checking prompt existence"}),
            mimetype="application/json",
            status_code=500
        )

    # Detect the language of the input text using the Translator class
    try:
        detected_language, confidence = translator.detect_language(text)
        logging.info(f"Detected language: {detected_language}, confidence: {confidence}")
    except Exception as e:
        logging.error(f"Error detecting language: {e}")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "An error occurred during language detection"}),
            mimetype="application/json",
            status_code=500
        )

    # Supported languages for the quiplash app
    supported_languages = translator.SUPPORTED_LANGUAGES

    # Check if detected language is supported and confidence >= 0.2
    if detected_language not in supported_languages or confidence < 0.7:
        logging.warning(f"Unsupported language detected: {detected_language} with confidence {confidence}")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "Unsupported language"}),
            mimetype="application/json",
            status_code=200
        )

    # Translate the text into supported languages using the Translator class
    try:
        translations = translator.translate_text(text, source_language=detected_language)
        # Filter translations to include only supported languages and exclude source language
        translations = [t for t in translations if t['language'] in supported_languages]
        # Add the original text if not already included
        if not any(t['language'] == detected_language for t in translations):
            translations.insert(0, {"language": detected_language, "text": text})
    except Exception as e:
        logging.error(f"Error translating text: {e}")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "An error occurred during translation"}),
            mimetype="application/json",
            status_code=500
        )

    # Create the prompt document
    prompt_doc = {
        "id": str(uuid.uuid4()),  # Generating a unique UUID for the 'id' field
        "username": username,
        "texts": translations
    }

    # Insert the prompt into the database
    try:
        prompt_container.create_item(body=prompt_doc)
        logging.info(f"Prompt created successfully with ID '{prompt_doc['id']}'") # turn to logging later
        # Return the prompt document as per the specification
        return func.HttpResponse(
            json.dumps(prompt_doc),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error inserting new prompt: {e}")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "An error occurred while creating the prompt"}),
            mimetype="application/json",
            status_code=500
        )

# Prompt_Suggest
@app.route(route="prompt/suggest", methods=['POST'], auth_level=func.AuthLevel.FUNCTION)
def prompt_suggest(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing /prompt/suggest request')

    try:
        req_body = req.get_json()
    except ValueError:
        logging.error("Invalid JSON input")
        return func.HttpResponse(
            json.dumps({"suggestion": "Cannot generate suggestion"}),
            mimetype="application/json",
            status_code=400
        )

    # Get the keyword from the request
    keyword = req_body.get('keyword')

    # Validate presence of keyword
    if not keyword:
        logging.warning("Keyword missing in the request")
        return func.HttpResponse(
            json.dumps({"suggestion": "Cannot generate suggestion"}),
            mimetype="application/json",
            status_code=200
        )

    # Use the PromptAdvisor to generate the suggestion
    try:
        suggestion_dict = advisor.generate_prompt({"keyword": keyword})
        suggestion = suggestion_dict.get('suggestion', 'Cannot generate suggestion')
        return func.HttpResponse(
            json.dumps({"suggestion": suggestion}),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error generating suggestion: {e}")
        return func.HttpResponse(
            json.dumps({"suggestion": "Cannot generate suggestion"}),
            mimetype="application/json",
            status_code=500
        )

@app.route(route="prompt/delete", methods=['POST'], auth_level=func.AuthLevel.FUNCTION)
def prompt_delete(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing /prompt/delete request')

    try:
        req_body = req.get_json()
    except ValueError:
        logging.error("Invalid JSON input")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "Invalid JSON input"}),
            mimetype="application/json",
            status_code=400
        )

    username = req_body.get('player')

    # Validate presence of username
    if not username:
        logging.warning("Player username missing in the request")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "Player username missing"}),
            mimetype="application/json",
            status_code=400
        )

    # Query the prompt container for prompts authored by the player
    try:
        # Use the username as partition key
        prompts = list(prompt_container.query_items(
            query="SELECT * FROM c",
            partition_key=username
        ))

        if not prompts:
            logging.info(f"No prompts found for player '{username}'")
            return func.HttpResponse(
                json.dumps({"result": True, "msg": "0 prompts deleted"}),
                mimetype="application/json",
                status_code=200
            )

        # Delete each prompt
        for prompt in prompts:
            prompt_container.delete_item(item=prompt['id'], partition_key=username)

        logging.info(f"Deleted {len(prompts)} prompts for player '{username}'")
        return func.HttpResponse(
            json.dumps({"result": True, "msg": f"{len(prompts)} prompts deleted"}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error deleting prompts for player '{username}': {e}")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "An error occurred during deletion"}),
            mimetype="application/json",
            status_code=500
        )

# Podium
@app.route(route="utils/podium", methods=['GET'], auth_level=func.AuthLevel.FUNCTION)
def utils_podium(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing /utils/podium request')

    try:
        podium = podium_utils.get_podium()
        return func.HttpResponse(
            json.dumps(podium),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error generating podium: {e}")
        return func.HttpResponse(
            json.dumps({"result": False, "msg": "An error occurred while generating the podium"}),
            mimetype="application/json",
            status_code=500
        )

# Get
@app.route(route="utils/get", methods=['GET', 'POST'], auth_level=func.AuthLevel.FUNCTION)
def utils_get(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing /utils/get request')

    try:
        req_body = req.get_json()
    except ValueError:
        logging.error("Invalid JSON input")
        return func.HttpResponse(
            json.dumps([]),  # Return empty list on invalid input
            mimetype="application/json",
            status_code=400
        )

    players = req_body.get('players', [])
    language = req_body.get('language')

    # Validate presence of 'language'
    if not language:
        logging.warning("Language code missing in the request")
        return func.HttpResponse(
            json.dumps([]),  # Return empty list if language is missing
            mimetype="application/json",
            status_code=200
        )

    try:
        prompts = prompts_utils.retrieve_prompts(players, language)
        return func.HttpResponse(
            json.dumps(prompts),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error retrieving prompts: {e}")
        return func.HttpResponse(
            json.dumps([]),  # Return empty list on error
            mimetype="application/json",
            status_code=500
        )