# tests/test_prompt_advisor.py
import os
import unittest
import logging
import json

# Set environment variables before importing function_app
settings_file = os.path.join(os.path.dirname(__file__), '..', 'local.settings.json')
with open(settings_file) as f:
    settings = json.load(f).get('Values', {})
# Set environment variables
for key, value in settings.items():
    os.environ[key] = value

from shared_code.prompt_advisor import PromptAdvisor
from shared_code.translator_utils import Translator

# Configure logging to display on the console for testing purposes
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TestPromptAdvisor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Set up environment variables and initialize the PromptAdvisor once for all tests.
        """
        # Initialize the PromptAdvisor instance
        try:
            cls.advisor = PromptAdvisor()
            print("Test Setup: PromptAdvisor instantiated successfully.\n")
        except Exception as e:
            print(f"Test Setup Failed: {e}")
            cls.advisor = None

    def test_correct_keyword(self):
        """
        Test generating a prompt with a correct keyword.
        """
        print("Running test_correct_keyword...")
        input_data = {"keyword": "innovation"}
        result = self.advisor.generate_prompt(input_data)
        print(f"Input: {input_data}")
        print(f"Output: {result}\n")
        #Assertions to check the output format and content
        self.assertIsInstance(result, dict, "Output is not a dictionary.")
        self.assertIn('suggestion', result, "Key 'suggestion' not found in output.")
        self.assertNotEqual(result['suggestion'], "Cannot generate suggestion", "Unexpected failure to generate suggestion.")
        self.assertIn(input_data['keyword'].lower(), result['suggestion'].lower(), "Keyword not found in suggestion.")
        self.assertGreaterEqual(len(result['suggestion']), 20, "Suggestion is shorter than 20 characters.")
        self.assertLessEqual(len(result['suggestion']), 100, "Suggestion is longer than 100 characters.")
    
    def test_correct_keywords(self):
        """
        Test generating prompts with multiple correct keywords.
        """
        print("Running test_correct_keywords...")
        valid_keywords = ["innovation", "technology", "constipation", "happiness", "education"]
        for keyword in valid_keywords:
            input_data = {"keyword": f"{keyword}"}
            result = self.advisor.generate_prompt(input_data)
            print(f"Input: {input_data}")
            print(f"Output: {result}\n")
            #Assertions to check the output format and content
            self.assertIsInstance(result, dict, "Output is not a dictionary.")
            self.assertIn('suggestion', result, "Key 'suggestion' not found in output.")
            self.assertNotEqual(result['suggestion'], "Cannot generate suggestion", "Unexpected failure to generate suggestion.")
            self.assertIn(input_data['keyword'].lower(), result['suggestion'].lower(), "Keyword not found in suggestion.")
            self.assertGreaterEqual(len(result['suggestion']), 20, "Suggestion is shorter than 20 characters.")
            self.assertLessEqual(len(result['suggestion']), 100, "Suggestion is longer than 100 characters.")

    def test_too_short_keyword(self):
        """
        Test generating a prompt with a too short keyword.
        """
        print("Running test_too_short_keyword...")
        input_data = {"keyword": "a"}  # Assuming single character is too short
        result = self.advisor.generate_prompt(input_data)
        print(f"Input: {input_data}")
        print(f"Output: {result}\n")

        # Assertions to check the output format and expected failure
        self.assertIsInstance(result, dict, "Output is not a dictionary.")
        self.assertIn('suggestion', result, "Key 'suggestion' not found in output.")
        self.assertEqual(result['suggestion'], "Cannot generate suggestion", "Expected 'Cannot generate suggestion' for too short keyword.")

    def test_gibberish_keyword(self):
        """
        Test generating a prompt with a gibberish keyword that likely has no detected language.
        """
        print("Running test_gibberish_keyword...")
        input_data = {"keyword": "asdlkjasdklj7559"}  # Gibberish string
        result = self.advisor.generate_prompt(input_data)
        print(f"Input: {input_data}")
        print(f"Output: {result}\n")

        # Assertions to check the output format and expected failure
        self.assertIsInstance(result, dict, "Output is not a dictionary.")
        self.assertIn('suggestion', result, "Key 'suggestion' not found in output.")
        self.assertEqual(result['suggestion'], "Cannot generate suggestion", "Expected 'Cannot generate suggestion' for gibberish keyword.")

    def test_low_confidence_language_detection(self):
        """
        Test generating a prompt with a keyword that results in low confidence language detection.
        """
        print("Running test_low_confidence_language_detection...")
        input_data = {"keyword": "qwertyuiop"}  # A string that might cause low confidence
        result = self.advisor.generate_prompt(input_data)
        print(f"Input: {input_data}")
        print(f"Output: {result}\n")

        # Assertions to check the output format and expected failure due to low confidence
        self.assertIsInstance(result, dict, "Output is not a dictionary.")
        self.assertIn('suggestion', result, "Key 'suggestion' not found in output.")
        self.assertEqual(result['suggestion'], "Cannot generate suggestion", "Expected 'Cannot generate suggestion' due to low confidence language detection.")

    def test_keyword_not_in_suggestion(self):
        """
        Test that if the generated prompt does not include the keyword, it returns 'Cannot generate suggestion'.
        """
        print("Running test_keyword_not_in_suggestion...")
        input_data = {"keyword": "uniquekeywordthatdoesnotappear"}
        # Assuming that the LLM may fail to include such a unique keyword
        result = self.advisor.generate_prompt(input_data)
        print(f"Input: {input_data}")
        print(f"Output: {result}\n")

        # Assertions to check that the method handles the absence of keyword appropriately
        self.assertIsInstance(result, dict, "Output is not a dictionary.")
        self.assertIn('suggestion', result, "Key 'suggestion' not found in output.")
        # Depending on implementation, it may retry or return 'Cannot generate suggestion'
        self.assertEqual(result['suggestion'], "Cannot generate suggestion", "Expected 'Cannot generate suggestion' when keyword is not included in prompt.")

    def test_invalid_input(self):
        """
        Test passing invalid input to the generate_prompt method.
        """
        print("Running test_invalid_input...")
        input_data = {"wrongkey": "somevalue"}
        result = self.advisor.generate_prompt(input_data)
        print(f"Input: {input_data}")
        print(f"Output: {result}\n")

        # Assertions to verify handling of invalid input
        self.assertIsInstance(result, dict, "Output is not a dictionary.")
        self.assertIn('suggestion', result, "Key 'suggestion' not found in output.")
        self.assertEqual(result['suggestion'], "Cannot generate suggestion", "Expected 'Cannot generate suggestion' for invalid input.")
    
    def test_invalid_character_keyword(self):
        """
        Test generating a prompt with an invalid character (emoji) as keyword.
        """
        print("Running test_invalid_character_keyword...")
        input_data = {"keyword": "😀"}  # Emoji as keyword
        result = self.advisor.generate_prompt(input_data)
        print(f"Input: {input_data}")
        print(f"Output: {result}\n")

        # Assertions to check the output format and expected failure
        self.assertIsInstance(result, dict, "Output is not a dictionary.")
        self.assertIn('suggestion', result, "Key 'suggestion' not found in output.")
        self.assertEqual(
            result['suggestion'],
            "Cannot generate suggestion",
            "Expected 'Cannot generate suggestion' for keyword with invalid character."
        )

if __name__ == '__main__':
    unittest.main(verbosity=2)
