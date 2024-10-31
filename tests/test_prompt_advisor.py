# tests/test_prompt_advisor.py

import unittest
import os
import json
import logging
from unittest.mock import patch, MagicMock

from shared_code.prompt_advisor import PromptAdvisor

class TestPromptAdvisor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Set up the PromptAdvisor instance for testing by loading environment variables
        from local.settings.json and initializing the PromptAdvisor class.
        """
        # Load settings from local.settings.json
        settings_file = os.path.join(os.path.dirname(__file__), '..', 'local.settings.json')
        try:
            with open(settings_file) as f:
                settings = json.load(f).get('Values', {})
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find {settings_file}. Ensure it exists and is correctly formatted.")
        except json.JSONDecodeError:
            raise ValueError(f"Error decoding JSON from {settings_file}. Ensure it is properly formatted.")

        # Set environment variables
        for key, value in settings.items():
            os.environ[key] = value

        # Initialize PromptAdvisor instance
        try:
            cls.prompt_advisor = PromptAdvisor()
            logging.info("PromptAdvisor instance initialized successfully.")
        except ValueError as e:
            cls.prompt_advisor = None
            logging.error(f"Initialization failed: {e}")

    @patch('shared_code.prompt_advisor.openai.ChatCompletion.create')
    def test_instantiation_of_llm(self, mock_chat_create):
        """
        Test that the PromptAdvisor class instantiates the OpenAI LLM correctly.
        """
        if self.prompt_advisor is None:
            self.fail("PromptAdvisor instance was not initialized.")

        # Ensure that OpenAI API is configured correctly
        self.assertIsNotNone(self.prompt_advisor.api_key, "API key should be set.")
        self.assertIsNotNone(self.prompt_advisor.api_base, "API base should be set.")
        self.assertEqual(self.prompt_advisor.model_name, "gpt-35-turbo", "Model name should be 'gpt-35-turbo'.")

    @patch('shared_code.prompt_advisor.openai.ChatCompletion.create')
    def test_connection_to_api(self, mock_chat_create):
        """
        Test that the PromptAdvisor can successfully connect to the OpenAI API.
        """
        if self.prompt_advisor is None:
            self.fail("PromptAdvisor instance was not initialized.")

        # Mock a successful API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="This is a valid prompt including the keyword."))]
        mock_chat_create.return_value = mock_response

        try:
            result = self.prompt_advisor.generate_prompt({"keyword": "test"})
            self.assertIn("suggestion", result, "Result should contain 'suggestion' key.")
        except Exception as e:
            self.fail(f"Connection to API failed with exception: {e}")

    @patch('shared_code.prompt_advisor.openai.ChatCompletion.create')
    @patch('shared_code.prompt_advisor.Translator.detect_language')
    def test_correct_keywords_generate_correct_prompts(self, mock_detect_language, mock_chat_create):
        """
        Test that correct keywords generate valid prompts.
        """
        if self.prompt_advisor is None:
            self.fail("PromptAdvisor instance was not initialized.")

        # Define a series of correct keywords
        correct_keywords = ["Python", "Azure", "OpenAI", "Quiplash", "Testing"]

        for keyword in correct_keywords:
            with self.subTest(keyword=keyword):
                # Mock the API response
                mock_response = MagicMock()
                mock_response.choices = [MagicMock(message=MagicMock(content=f"This is a prompt including {keyword}."))]
                mock_chat_create.return_value = mock_response

                # Mock the language detection to return a supported language with high confidence
                mock_detect_language.return_value = ("en", 0.99)

                result = self.prompt_advisor.generate_prompt({"keyword": keyword})
                self.assertIn("suggestion", result, "Result should contain 'suggestion' key.")
                self.assertIn(keyword.lower(), result["suggestion"].lower(), f"Suggestion should include the keyword '{keyword}'.")
                self.assertGreaterEqual(len(result["suggestion"]), 20, "Suggestion should be at least 20 characters long.")
                self.assertLessEqual(len(result["suggestion"]), 100, "Suggestion should be at most 100 characters long.")

    @patch('shared_code.prompt_advisor.openai.ChatCompletion.create')
    @patch('shared_code.prompt_advisor.Translator.detect_language')
    def test_incorrect_inputs_generate_cannot_generate_suggestion(self, mock_detect_language, mock_chat_create):
        """
        Test that incorrect inputs result in 'Cannot generate suggestion'.
        """
        if self.prompt_advisor is None:
            self.fail("PromptAdvisor instance was not initialized.")

        # Define a series of incorrect keywords or scenarios
        incorrect_inputs = [
            {},  # Missing 'keyword'
            {"keyword": ""},  # Empty keyword
            {"keyword": 123},  # Non-string keyword
            {"keyword": "🖖"},  # Unsupported language or non-latin characters
            {"keyword": "a" * 1000}  # Extremely long keyword
        ]

        for input_dict in incorrect_inputs:
            with self.subTest(input_dict=input_dict):
                # Mock the API response to always return a prompt that does not include the keyword
                mock_response = MagicMock()
                mock_response.choices = [MagicMock(message=MagicMock(content="This prompt does not include the keyword."))]
                mock_chat_create.return_value = mock_response

                # Mock the language detection to return an unsupported language or low confidence
                mock_detect_language.return_value = ("xx", 0.1)

                result = self.prompt_advisor.generate_prompt(input_dict)
                self.assertIn("suggestion", result, "Result should contain 'suggestion' key.")
                self.assertEqual(result["suggestion"], "Cannot generate suggestion", "Suggestion should be 'Cannot generate suggestion'.")

    @patch('shared_code.prompt_advisor.openai.ChatCompletion.create')
    @patch('shared_code.prompt_advisor.Translator.detect_language')
    def test_generate_prompt_with_invalid_language(self, mock_detect_language, mock_chat_create):
        """
        Test that prompts with unsupported languages are handled correctly.
        """
        if self.prompt_advisor is None:
            self.fail("PromptAdvisor instance was not initialized.")

        # Mock the API to return a valid prompt with an unsupported language
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="これはサポートされていない言語のプロンプトです。"))]  # Japanese
        mock_chat_create.return_value = mock_response

        # Mock the language detection to return an unsupported language with high confidence
        mock_detect_language.return_value = ("ja", 0.99)

        result = self.prompt_advisor.generate_prompt({"keyword": "test"})
        self.assertIn("suggestion", result, "Result should contain 'suggestion' key.")
        self.assertEqual(result["suggestion"], "Cannot generate suggestion", "Suggestion should be 'Cannot generate suggestion' due to unsupported language.")

    @patch('shared_code.prompt_advisor.openai.ChatCompletion.create')
    @patch('shared_code.prompt_advisor.Translator.detect_language')
    def test_generate_prompt_with_low_confidence_language_detection(self, mock_detect_language, mock_chat_create):
        """
        Test that prompts with low confidence in language detection are handled correctly.
        """
        if self.prompt_advisor is None:
            self.fail("PromptAdvisor instance was not initialized.")

        # Mock the API to return a valid prompt
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="This is a valid prompt including the keyword."))]
        mock_chat_create.return_value = mock_response

        # Mock the language detection to return a supported language with low confidence
        mock_detect_language.return_value = ("en", 0.1)

        result = self.prompt_advisor.generate_prompt({"keyword": "test"})
        self.assertIn("suggestion", result, "Result should contain 'suggestion' key.")
        self.assertEqual(result["suggestion"], "Cannot generate suggestion", "Suggestion should be 'Cannot generate suggestion' due to low confidence in language detection.")

if __name__ == '__main__':
    # Configure logging to display INFO level messages
    logging.basicConfig(level=logging.INFO)
    unittest.main()
