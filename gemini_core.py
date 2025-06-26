import os
import google.generativeai as genai
import google.api_core.exceptions
from dotenv import load_dotenv
import time
from functools import wraps
from datetime import datetime

load_dotenv()

def retry_on_rate_limit(max_retries=3, initial_delay=5):
    """A decorator to handle Gemini API rate limiting with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = initial_delay
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except google.api_core.exceptions.ResourceExhausted as e:
                    retries += 1
                    if retries >= max_retries:
                        print(f"API rate limit exceeded. Max retries reached for function '{func.__name__}'. Failing.")
                        raise e
                    
                    print(f"API rate limit exceeded on '{func.__name__}'. Retrying in {delay} seconds... ({retries}/{max_retries})")
                    time.sleep(delay)
                    delay *= 2 # Exponential backoff
            return None
        return wrapper
    return decorator

def get_gemini_client(model_name='gemini-2.5-pro-preview-06-05'):
    """Initializes and returns a specific Gemini client with timeout configuration."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY must be set in the environment variables.")
    genai.configure(api_key=api_key)
    
    # Configure generation settings for better timeout handling
    generation_config = genai.types.GenerationConfig(
        temperature=0.7,
        max_output_tokens=8192,  # Reasonable limit for most responses
        top_p=0.9,
        top_k=40
    )
    
    return genai.GenerativeModel(model_name, generation_config=generation_config)

def get_current_date():
    """Returns the current date in a formatted string."""
    return datetime.now().strftime("%B %d, %Y")