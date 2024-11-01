# shared_code/prompt_advisor.py
import os
import logging
import time  # Import time for adding delays
from openai import AzureOpenAI  # Updated import for new API
from shared_code.translator_utils import Translator

class PromptAdvisor:
    def __init__(self):
        """
        Initializes the PromptAdvisor by setting up the Azure OpenAI client and the Translator.
        """
        # Retrieve OpenAI credentials from environment variables
        self.api_key = os.environ.get('OAI_KEY')
        self.api_base = os.environ.get('OAI_ENDPOINT')
        self.api_version = "2024-02-01"
        self.model_name = "gpt-35-turbo-ab3u21" # must match deployed model name

        if not self.api_key or not self.api_base:
            logging.error("OpenAI API credentials are not set in environment variables.")
            raise ValueError("OpenAI API credentials are missing.")

        # Initialize the AzureOpenAI client using the new API
        self.client = AzureOpenAI(
            azure_endpoint=self.api_base,
            api_key=self.api_key,
            api_version=self.api_version
        )

        # Initialize the Translator
        self.translator = Translator()

    def generate_prompt(self, input_dict):
        """
        Generates a prompt suggestion that includes the specified keyword and meets the length requirements.

        Parameters:
            input_dict (dict): A dictionary with the key "keyword" and its corresponding string value.

        Returns:
            dict: A dictionary containing the key "suggestion" with the generated prompt or an error message.
        """
        keyword = input_dict.get("keyword")
        if not keyword or not isinstance(keyword, str):
            logging.error("Invalid input: 'keyword' is missing or not a string.")
            return {"suggestion": "Cannot generate suggestion"}

        attempts = 0
        max_attempts = 3
        delay_seconds = 10  # Delay between attempts

        while attempts < max_attempts:
            try:
                # Define the system and user messages for the chat completion
                messages = [
                    {"role": "system", "content": "You are an assistant that generates creative prompts based on a given keyword."},
                    {"role": "user", "content": f"Generate a creative prompt that includes the keyword '{keyword}'. Limit your answer between 20 and 100 characters."}
                ]

                # Call the Azure OpenAI Chat Completion API using the new client
                response = self.client.chat.completions.create(
                    model=self.model_name,  # Deployment name
                    messages=messages,
                    temperature=0.7,
                    max_tokens=150  # Ensure enough tokens for the response
                )

                # Extract the generated prompt from the response
                generated_prompt = response.choices[0].message.content.strip()

                # Check if the keyword is included in the prompt (case-insensitive)
                if keyword.lower() not in generated_prompt.lower():
                    logging.warning(f"Attempt {attempts + 1}: Generated prompt does not include the keyword '{keyword}'.")
                    attempts += 1
                    if attempts < max_attempts:
                        time.sleep(delay_seconds)
                    continue

                # Check if the prompt length is within the specified range
                prompt_length = len(generated_prompt)
                if prompt_length < 20 or prompt_length > 100:
                    logging.warning(f"Attempt {attempts + 1}: Generated prompt length {prompt_length} is out of bounds (20-100).")
                    attempts += 1
                    if attempts < max_attempts:
                        time.sleep(delay_seconds)
                    continue

                # Detect the language of the generated prompt
                language_code, confidence = self.translator.detect_language(generated_prompt)
                if language_code not in Translator.SUPPORTED_LANGUAGES or confidence < 0.2:
                    logging.warning(f"Attempt {attempts + 1}: Generated prompt language '{language_code}' is unsupported or confidence {confidence} is low.")
                    attempts += 1
                    if attempts < max_attempts:
                        time.sleep(delay_seconds)
                    continue

                # If all validations pass, return the generated prompt
                logging.info(f"Generated prompt on attempt {attempts + 1}: {generated_prompt}")
                return {"suggestion": generated_prompt}

            except Exception as e:
                logging.error(f"Attempt {attempts + 1}: Exception during prompt generation: {e}")
                attempts += 1
                if attempts < max_attempts:
                    time.sleep(delay_seconds)
                continue

        # If all attempts fail, return an error message
        logging.error("Failed to generate a valid prompt after 3 attempts.")
        return {"suggestion": "Cannot generate suggestion"}