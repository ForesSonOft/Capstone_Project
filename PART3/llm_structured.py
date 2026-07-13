import os
import json
import logging
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, ValidationError, Field
from google import genai   # ✅ new client

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("❌ No API key found. Please set GOOGLE_API_KEY in your .env file.")

client = genai.Client(api_key=API_KEY)

class Awardee(BaseModel):
    name: str = Field(..., description="Full name of the awardee")
    profession: str = Field(..., description="Profession or field of contribution")
    age: int = Field(..., description="Age of the awardee")
    biopic: str = Field(..., description="Two-line biographical summary")

class PadmaShriList(BaseModel):
    state: str = Field(..., description="State of awardees")
    year: int = Field(..., description="Year of awards")
    awardees: list[Awardee]


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_gemini(prompt: str):
    logging.info("Calling Gemini API...")
    response = client.responses.generate(
        model="gemini-1.5-flash",
        contents=[{"role": "user", "parts": [prompt]}]
    )

    if response.candidates and response.candidates[0].content.parts:
        reply = response.candidates[0].content.parts[0].text
        return reply
    else:
        raise ValueError("No text returned from Gemini API")

prompt = """
Return Padma Shri awardees from Tamil Nadu (India) for the year 2026
in strict JSON format with fields:
{
  "state": "Tamil Nadu",
  "year": 2026,
  "awardees": [
    {"name": "", "profession": "", "age": 0, "biopic": ""}
  ]
}
Each biopic must be exactly two lines.
"""

def parse_and_validate(response_text: str):
    try:
        data = json.loads(response_text)
        validated = PadmaShriList(**data)
        logging.info("✅ JSON validated successfully.")
        return validated
    except (json.JSONDecodeError, ValidationError) as e:
        logging.error(f"❌ Validation failed: {e}")
        raise

def main():
    try:
        raw_output = call_gemini(prompt)
        result = parse_and_validate(raw_output)
        print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    except Exception as e:
        logging.error(f"Error in workflow: {e}")

if __name__ == "__main__":
    main()