import requests
import json
import logging

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434", model="llama3.2:3b"):
        self.base_url = base_url
        self.model = model
        self.logger = logging.getLogger(__name__)

    def generate_completion(self, prompt: str, system_prompt: str = None) -> str:
        """
        Generates a completion from Ollama.
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error communicating with Ollama: {e}")
            return None
            
    def process_profile(self, profile_data: dict, custom_prompt: str = None) -> str:
        """
        Process a LinkedIn profile dictionary with the LLM.
        """
        profile_json_str = json.dumps(profile_data, indent=2)
        
        if not custom_prompt:
            prompt = f"""
            Analyze the following LinkedIn profile data and provide a brief summary of the candidate's key skills and experience level.
            
            Profile Data:
            {profile_json_str}
            """
        else:
            prompt = f"{custom_prompt}\n\nProfile Data:\n{profile_json_str}"
            
        return self.generate_completion(prompt)
