# function_app.py

import azure.functions as func
import logging
import os
import json
import uuid

from shared_code.db_utils import CosmosDB
from shared_code.prompt_advisor import PromptAdvisor
from shared_code.translator_utils import Translator

# Initialize CosmosDB instance
cosmos_db = CosmosDB()
player_container = cosmos_db.get_player_container()
prompt_container = cosmos_db.get_prompt_container()

advisor = PromptAdvisor()
translator = Translator()
app = func.FunctionApp()

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

@app.route(route="player/login", methods=['GET'], auth_level=func.AuthLevel.FUNCTION)
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