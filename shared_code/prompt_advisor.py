# shared_code/prompt_advisor.py
import os
import logging
import time  # Import time for adding delays
from openai import AzureOpenAI  # Updated import for new API
from shared_code.translator_utils import Translator

class PromptAdvisor:
    # Class-level constants for easy configuration and to avoid magic numbers
    MIN_KEYWORD_LENGTH = 2
    MAX_KEYWORD_LENGTH = 100
    MIN_PROMPT_LENGTH = 20
    MAX_PROMPT_LENGTH = 100
    LANGUAGE_CONFIDENCE_THRESHOLD = 0.8
    MAX_ATTEMPTS = 3
    DELAY_SECONDS = 10  # Delay between attempts in seconds

    def __init__(self):
        """
        Initializes the PromptAdvisor by setting up the Azure OpenAI client and the Translator.
        """
        # Retrieve OpenAI credentials from environment variables
        self.api_key = os.environ.get('OAI_KEY')
        self.api_base = os.environ.get('OAI_ENDPOINT')
        self.api_version = "2024-02-01"
        self.model_name = "gpt-35-turbo"  # Must match deployed model name

        if not self.api_key or not self.api_base:
            logging.error("OpenAI API credentials are not set in environment variables.")
            raise ValueError("OpenAI API credentials are missing.")

        # Initialize the Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=self.api_base,
            api_key=self.api_key,
            api_version=self.api_version
        )

        # Initialize the Translator
        self.translator = Translator()

    def is_valid_keyword(self, keyword):
        """
        Validates the keyword based on length and language detection.

        Parameters:
            keyword (str): The keyword to validate.

        Returns:
            bool: True if the keyword is valid, False otherwise.
        """
        if not keyword or not isinstance(keyword, str):
            logging.error("Invalid input: 'keyword' is missing or not a string.")
            return False

        if not (self.MIN_KEYWORD_LENGTH <= len(keyword) <= self.MAX_KEYWORD_LENGTH):
            logging.error(
                f"Keyword length {len(keyword)} is out of bounds "
                f"({self.MIN_KEYWORD_LENGTH}-{self.MAX_KEYWORD_LENGTH})."
            )
            return False

        # Detect the language of the keyword
        try:
            language_code, confidence = self.translator.detect_language(keyword)
            if (language_code not in Translator.SUPPORTED_LANGUAGES or
                    confidence < self.LANGUAGE_CONFIDENCE_THRESHOLD):
                logging.error(
                    f"Keyword language '{language_code}' is unsupported or confidence "
                    f"{confidence} is below threshold."
                )
                return False
        except Exception as e:
            logging.error(f"Language detection failed for keyword: {e}")
            return False

        return True

    def is_valid_prompt(self, prompt, keyword):
        """
        Validates the generated prompt based on keyword inclusion, length, and language detection.

        Parameters:
            prompt (str): The generated prompt to validate.
            keyword (str): The keyword that should be included in the prompt.

        Returns:
            bool: True if the prompt is valid, False otherwise.
        """
        # Check if the keyword is included in the prompt (case-insensitive)
        if keyword.lower() not in prompt.lower():
            logging.warning(f"Generated prompt does not include the keyword '{keyword}'.")
            return False

        # Check if the prompt length is within the specified range
        prompt_length = len(prompt)
        if not (self.MIN_PROMPT_LENGTH <= prompt_length <= self.MAX_PROMPT_LENGTH):
            logging.warning(
                f"Generated prompt length {prompt_length} is out of bounds "
                f"({self.MIN_PROMPT_LENGTH}-{self.MAX_PROMPT_LENGTH})."
            )
            return False

        # Detect the language of the generated prompt
        try:
            language_code, confidence = self.translator.detect_language(prompt)
            if (language_code not in Translator.SUPPORTED_LANGUAGES or
                    confidence < self.LANGUAGE_CONFIDENCE_THRESHOLD):
                logging.warning(
                    f"Generated prompt language '{language_code}' is unsupported or confidence "
                    f"{confidence} is below threshold."
                )
                return False
        except Exception as e:
            logging.error(f"Language detection failed for prompt: {e}")
            return False

        return True

    def generate_prompt(self, input_dict):
        """
        Generates a prompt suggestion that includes the specified keyword and meets the length requirements.

        Parameters:
            input_dict (dict): A dictionary with the key "keyword" and its corresponding string value.

        Returns:
            dict: A dictionary containing the key "suggestion" with the generated prompt or an error message.
        """
        keyword = input_dict.get("keyword")
        if not self.is_valid_keyword(keyword):
            return {"suggestion": "Cannot generate suggestion"}

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                # Define the system and user messages for the chat completion
                messages = [
                    {
                        "role": "system",
                        "content": "You are an assistant that generates creative chat messages based on a given keyword."
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Generate a chat message that includes the keyword '{keyword}'. "
                            f"Your output MUST include '{keyword}' and be between "
                            f"{self.MIN_PROMPT_LENGTH} and {self.MAX_PROMPT_LENGTH} characters."
                        )
                    }
                ]

                # Call the Azure OpenAI Chat Completion API
                response = self.client.chat.completions.create(
                    model=self.model_name,  # Deployment name
                    messages=messages,
                    temperature=0.7,
                    max_tokens=150  # Ensure enough tokens for the response
                )

                # Extract the generated prompt from the response
                generated_prompt = response.choices[0].message.content.strip()

                # Validate the generated prompt
                if self.is_valid_prompt(generated_prompt, keyword):
                    logging.info(f"Generated prompt on attempt {attempt}: {generated_prompt}")
                    return {"suggestion": generated_prompt}
                else:
                    logging.warning(f"Attempt {attempt}: Generated prompt did not pass validation.")

            except Exception as e:
                logging.error(f"Attempt {attempt}: Exception during prompt generation: {e}")

            # Delay before the next attempt, if any
            if attempt < self.MAX_ATTEMPTS:
                time.sleep(self.DELAY_SECONDS)

        # If all attempts fail, return an error message
        logging.error("Failed to generate a valid prompt after maximum attempts.")
        return {"suggestion": "Cannot generate suggestion"}