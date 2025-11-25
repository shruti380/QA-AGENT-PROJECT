"""
Groq API Client for LLM interactions
"""
import os
import json
from typing import Optional, Dict, Any
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class GroqClient:
    """Client for interacting with Groq API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize Groq client
        
        Args:
            api_key: Groq API key (if None, reads from GROQ_API_KEY env var)
            model: Model to use for generation
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not provided. Set GROQ_API_KEY environment variable.")
        
        self.model = model
        self.client = Groq(api_key=self.api_key)
        
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate text using Groq API
        
        Args:
            prompt: User prompt
            system_prompt: System prompt to set context
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")
    
    def generate_structured(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        format_type: str = "json",
        temperature: float = 0.5,
        max_tokens: int = 3000
    ) -> Dict[Any, Any]:
        """
        Generate structured output (JSON) using Groq API
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            format_type: Output format (currently only 'json' supported)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Parsed JSON response
        """
        try:
            # Add JSON format instruction to system prompt
            json_instruction = "\n\nYou must respond ONLY with valid JSON. Do not include any preamble, explanation, or markdown formatting. Return raw JSON only."
            
            if system_prompt:
                system_prompt = system_prompt + json_instruction
            else:
                system_prompt = "You are a helpful assistant that responds in JSON format." + json_instruction
            
            # Generate response
            response_text = self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Clean response - remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            try:
                parsed_response = json.loads(response_text)
                return parsed_response
            except json.JSONDecodeError as e:
                # If JSON parsing fails, try to extract JSON from text
                import re
                json_match = re.search(r'\{.*\}|\[.*\]', response_text, re.DOTALL)
                if json_match:
                    parsed_response = json.loads(json_match.group())
                    return parsed_response
                else:
                    raise Exception(f"Failed to parse JSON response: {str(e)}\nResponse: {response_text[:200]}")
                    
        except Exception as e:
            raise Exception(f"Groq structured generation error: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Test connection to Groq API
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.generate(
                prompt="Say 'Connection successful' if you can read this.",
                system_prompt="You are a helpful assistant.",
                max_tokens=50
            )
            return "successful" in response.lower()
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False


# Singleton instance
_groq_client_instance = None


def get_groq_client() -> GroqClient:
    """
    Get or create singleton Groq client instance
    
    Returns:
        GroqClient instance
    """
    global _groq_client_instance
    
    if _groq_client_instance is None:
        _groq_client_instance = GroqClient()
    
    return _groq_client_instance


if __name__ == "__main__":
    # Test the client
    print("Testing Groq client...")
    
    try:
        client = GroqClient()
        
        # Test basic generation
        print("\n1. Testing basic generation...")
        response = client.generate("What is 2+2?", max_tokens=50)
        print(f"Response: {response}")
        
        # Test structured generation
        print("\n2. Testing structured generation...")
        structured_response = client.generate_structured(
            prompt="List 3 colors in JSON format with 'colors' as key",
            system_prompt="You are a helpful assistant that returns JSON."
        )
        print(f"Structured response: {json.dumps(structured_response, indent=2)}")
        
        # Test connection
        print("\n3. Testing connection...")
        is_connected = client.test_connection()
        print(f"Connection status: {'✓ Connected' if is_connected else '✗ Failed'}")
        
    except Exception as e:
        print(f"Error: {str(e)}")