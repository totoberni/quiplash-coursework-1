# shared_code/translator_utils.py

import os
import logging
from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.text import TextTranslationClient
from azure.ai.translation.text.models import InputTextItem

# Retrieve environment variables
# Fix - env not correct call
translator_key = os.environ.get('TRANSLATOR_TEXT_SUBSCRIPTION_KEY')
translator_endpoint = os.environ.get('TRANSLATOR_TEXT_ENDPOINT')
translator_region = os.environ.get('TRANSLATOR_TEXT_REGION')

if not translator_endpoint:
    logging.error("One or more Translator Text environment variables are missing.")
    raise ValueError("Translator Endpoint environment variable not set.")
if not translator_key:
    logging.error("One or more Translator Text environment variables are missing.")
    raise ValueError("Translator Text Subscription Key environment variable not set.")
if not translator_region:
    logging.error("One or more Translator Text environment variables are missing.")
    raise ValueError("Translator Text Region environment variable not set.")

# Initialize the Translator Text client
try:
    credential = AzureKeyCredential(translator_key)
    translator_client = TextTranslationClient(
        endpoint=translator_endpoint,
        credential=credential
    )
except Exception as e:
    logging.error(f"Failed to create Translator Text client: {e}")
    raise e

# Supported languages for quiplash
SUPPORTED_LANGUAGES = ["en", "es", "it", "sv", "ru", "id", "bg", "zh-Hans"]

def detect_language(text):
    """
    Detects the language of the given text.

    Parameters:
    - text (str): The text to detect the language for.

    Returns:
    - str: The ISO 639-1 language code.
    - float: The confidence score.
    """
    try:
        input_text_elements = [InputTextItem(text=text)]
        detect_result = translator_client.detect_language(inputs=input_text_elements)
        language_detected = detect_result[0].primary_language
        return language_detected.iso6391_name, language_detected.confidence
    except Exception as e:
        logging.error(f"Language detection failed: {e}")
        raise e

def translate_text(text, source_language):
    """
    Translates the input text into all supported languages.

    Parameters:
    - text (str): The text to translate.
    - source_language (str): The ISO 639-1 code of the source language.

    Returns:
    - List[Dict]: A list of dictionaries with 'language' and 'text' keys.
    """
    translations = []

    # Add the original text
    translations.append({
        "language": source_language,
        "text": text
    })

    # Target languages excluding the source language
    target_languages = [lang for lang in SUPPORTED_LANGUAGES if lang != source_language]

    # Prepare input text
    input_text_elements = [InputTextItem(text=text)]

    if target_languages:
        try:
            translation_response = translator_client.translate(
                content=input_text_elements,
                to=target_languages,
                from_parameter=source_language
            )
            translation = translation_response[0]
            for translated_text in translation.translations:
                translations.append({
                    "language": translated_text.to,
                    "text": translated_text.text
                })
        except Exception as e:
            logging.error(f"Translation failed: {e}")
            raise e

    return translations