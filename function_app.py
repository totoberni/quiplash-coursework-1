import azure.functions as func
import logging


from shared_code.db_utils import player_container, prompts_container
from shared_code.translator_utils import detect_language, translate_text


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="setup_function")
def setup_function(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )