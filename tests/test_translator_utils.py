# tests/test_translator_utils.py

import unittest
import os
import logging
import json

# Import the Translator class from shared_code.translator_utils
from shared_code.translator_utils import Translator

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

class TestTranslator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Set up the Translator instance for all tests.
        This method is called once before all tests.
        """
        try:
            cls.translator = Translator()
            logging.info("Translator instance created successfully.")
        except Exception as e:
            logging.error(f"Failed to create Translator instance: {e}")
            raise e

    def test_translator_connection(self):
        """
        Test that the translator client is initialized properly.
        """
        try:
            # Access the translator_client from the Translator instance
            self.assertIsNotNone(self.translator.translator_client, "Translator client is not initialized.")
            print("Successfully accessed the Translator service.")
        except Exception as e:
            self.fail(f"Failed to access Translator service: {str(e)}")

    def test_translator_instantiation(self):
        """
        Test that the Translator class is instantiated properly.
        """
        try:
            self.assertIsInstance(self.translator, Translator, "translator is not an instance of Translator.")
            print("Translator instance is properly instantiated.")
        except Exception as e:
            self.fail(f"Translator instantiation failed: {str(e)}")

    def test_translation_spanish_to_italian(self):
        """
        Test translating text from Spanish to Italian.
        """
        try:
            source_text = "Este es un mensaje de prueba. Hola mundo!"
            source_language = "es"
            target_language = "it"
    
            # Perform translation
            translations = self.translator.translate_text(source_text, source_language)
    
            # Find the Italian translation in the results
            italian_translation = next((t for t in translations if t['language'] == target_language), None)
    
            # Assertions
            self.assertIsNotNone(italian_translation, "Italian translation not found in the results.")
            self.assertIsInstance(italian_translation['text'], str, "Translated text is not a string.")
            self.assertGreater(len(italian_translation['text']), 0, "Translated text is empty.")
    
            print(f"Translation from '{source_language}' to '{target_language}': '{italian_translation['text']}'")
        except Exception as e:
            self.fail(f"Translation from Spanish to Italian failed: {str(e)}")
    
    def test_language_detection_italian(self):
        """
        Test detecting the language of an Italian sentence.
        """
        try:
            text = "Questo è un messaggio di prova."
            expected_language = "it"

            # Perform language detection
            detected_language, confidence = self.translator.detect_language(text)

            # Assertions
            self.assertEqual(
                detected_language,
                expected_language,
                f"Expected language '{expected_language}' but detected '{detected_language}'."
            )
            self.assertGreater(
                confidence,
                0.5,
                f"Confidence {confidence} is too low."
            )

            print(f"Detected language: '{detected_language}' with confidence {confidence}")
        except Exception as e:
            self.fail(f"Language detection failed: {str(e)}")


if __name__ == '__main__':
    unittest.main()
