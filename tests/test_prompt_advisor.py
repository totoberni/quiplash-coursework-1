# tests/test_prompt_advisor.py
import os
import unittest
import logging
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
        # Ensure that the necessary environment variables are set for testing
        os.environ.setdefault('OAI_KEY', 'your_openai_api_key')  # Replace with a valid key for actual testing
        os.environ.setdefault('OAI_ENDPOINT', 'https://your-azure-openai-endpoint/')  # Replace with a valid endpoint

        # Initialize the PromptAdvisor instance
        try:
            cls.advisor = PromptAdvisor()
            print("Test Setup: PromptAdvisor instantiated successfully.\n")
        except Exception as e:
            print(f"Test Setup Failed: {e}")
            cls.advisor = None

    def test_proper_instantiation(self):
        """
        Test that the PromptAdvisor class instantiates properly without errors.
        """
        print("Running test_proper_instantiation...")
        try:
            advisor = PromptAdvisor()
            print("Result: Proper instantiation - SUCCESS\n")
        except Exception as e:
            print(f"Result: Proper instantiation - FAILED with exception: {e}\n")

    def test_correct_keyword(self):
        """
        Test generating a prompt with a correct keyword.
        """
        print("Running test_correct_keyword...")
        input_data = {"keyword": "innovation"}
        result = self.advisor.generate_prompt(input_data)
        print(f"Input: {input_data}")
        print(f"Output: {result}\n")

    def test_too_short_keyword(self):
        """
        Test generating a prompt with a too short keyword.
        """
        print("Running test_too_short_keyword...")
        input_data = {"keyword": "a"}  # Assuming single character is too short
        result = self.advisor.generate_prompt(input_data)
        print(f"Input: {input_data}")
        print(f"Output: {result}\n")

    def test_too_long_keyword(self):
        """
        Test generating a prompt with a too long keyword.
        """
        print("Running test_too_long_keyword...")
        input_data = {"keyword": "a" * 101}  # Assuming 101 characters is too long
        result = self.advisor.generate_prompt(input_data)
        print(f"Input: {input_data}")
        print(f"Output: {result}\n")

    def test_gibberish_keyword(self):
        """
        Test generating a prompt with gibberish keyword that likely has no detected language.
        """
        print("Running test_gibberish_keyword...")
        input_data = {"keyword": "asdlkjasdklj"}  # Gibberish string
        result = self.advisor.generate_prompt(input_data)
        print(f"Input: {input_data}")
        print(f"Output: {result}\n")

if __name__ == '__main__':
    unittest.main(verbosity=2)
