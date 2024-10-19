# shared_code/translator_utils.py

import os
import logging
from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.text import TextTranslationClient
from azure.ai.translation.text.models import InputTextItem

class Translator:
    SUPPORTED_LANGUAGES = ["en", "es", "it", "sv", "ru", "id", "bg", "zh-Hans"]

    def __init__(self):
        """
        Initializes the Translator class by setting up the Translator Text client.
        Retrieves necessary environment variables and handles any missing configurations.
        """
        # Retrieve environment variables
        self.translator_key = os.environ.get('TRANSLATOR_TEXT_SUBSCRIPTION_KEY')
        self.translator_endpoint = os.environ.get('TRANSLATOR_TEXT_ENDPOINT')
        self.translator_region = os.environ.get('TRANSLATOR_TEXT_REGION')
    
        # Validate environment variables
        if not self.translator_endpoint:
            logging.error("Translator Endpoint environment variable is missing.")
            raise ValueError("Translator Endpoint environment variable not set.")
        if not self.translator_key:
            logging.error("Translator Text Subscription Key environment variable is missing.")
            raise ValueError("Translator Text Subscription Key environment variable not set.")
        if not self.translator_region:
            logging.error("Translator Text Region environment variable is missing.")
            raise ValueError("Translator Text Region environment variable not set.")
    
        # Initialize the Translator Text client with the region
        try:
            credential = AzureKeyCredential(self.translator_key)
            self.translator_client = TextTranslationClient(
                endpoint=self.translator_endpoint,
                credential=credential,
                region=self.translator_region  # Include the region here
            )
        except Exception as e:
            logging.error(f"Failed to create Translator Text client: {e}")
            raise e

    def detect_language(self, text):
        """
        Detects the language of the given text.

        Parameters:
            text (str): The text to detect the language for.

        Returns:
            tuple:
                - str: The ISO 639-1 language code.
                - float: The confidence score.
        """
        try:
            input_text_elements = [InputTextItem(text=text)]
            detect_result = self.translator_client.detect_language(inputs=input_text_elements)
            language_detected = detect_result[0].primary_language
            return language_detected.iso6391_name, language_detected.confidence
        except Exception as e:
            logging.error(f"Language detection failed: {e}")
            raise e

    def translate_text(self, text, source_language):
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
        target_languages = [lang for lang in self.SUPPORTED_LANGUAGES if lang != source_language]

        # Prepare input text as a list of strings
        input_text_elements = [text]

        if target_languages:
            try:
                # Perform translation
                response = self.translator_client.translate(
                    body=input_text_elements,
                    to_language=target_languages,
                    from_language=source_language
                )
                translation = response[0] if response else None

                if translation:
                    # Process the translations
                    for translated_text in translation.translations:
                        translations.append({
                            "language": translated_text.to,
                            "text": translated_text.text
                        })
            except Exception as e:
                logging.error(f"Translation failed: {e}")
                raise e

        return translations