import os
import logging
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry
import openai
load_dotenv()
API_KEY = os.getenv("API_KEY", "")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "10"))  # requests per minute
TIMEOUT = int(os.getenv("TIMEOUT", "10"))       # seconds

openai.api_key = API_KEY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

def validate_input(user_text: str) -> str:
    if not isinstance(user_text, str):
        raise ValueError("Input must be a string")
    cleaned = user_text.strip()
    if len(cleaned) == 0:
        raise ValueError("Input cannot be empty")
    return cleaned

def validate_output(response: str) -> str:
    if not isinstance(response, str):
        raise ValueError("Response must be text")
    cleaned = response.strip()
    if len(cleaned) == 0:
        raise ValueError("Empty response from model")
    return cleaned

def filter_content(response: str) -> str:
    banned_words = ["password", "credit card", "ssn"]
    for word in banned_words:
        if word in response.lower():
            raise ValueError("Unsafe content detected in response")
    return response

@sleep_and_retry
@limits(calls=RATE_LIMIT, period=60)
def rate_limited_call():
    """Enforce rate limit per minute."""
    return True

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_api(prompt: str):
    rate_limited_call()
    logging.info("Calling OpenAI Chat API")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",   # replace with your model
            messages=[{"role": "user", "content": prompt}],
            timeout=TIMEOUT
        )
        reply = response["choices"][0]["message"]["content"]
        log_usage("Chatbot response success", cost=0.002)
        return reply
    except Exception as e:
        log_usage(f"Chatbot error: {e}", cost=0)
        raise


def log_usage(event: str, cost: float = 0.0):
    logging.info(f"Event: {event}, Cost: {cost}")

def safe_chat(prompt: str):
    safe_prompt = validate_input(prompt)
    raw_reply = call_api(safe_prompt)
    reply = validate_output(raw_reply)
    reply = filter_content(reply)
    return reply
