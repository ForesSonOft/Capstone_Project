import os
import json
import httpx
import asyncio
from pydantic import BaseModel, ValidationError
from pydantic_settings import BaseSettings

# Settings
class Settings(BaseSettings):
    openai_api_key: str
    class Config:
        env_file = "Key.env"

settings = Settings()

# Schema
class AwardeeSchema(BaseModel):
    name: str
    age: int
    profession: str
    biopic: str

# Prompt
prompt = """
List the Padma Shri awardees from Tamil Nadu.
For each awardee, return JSON with fields:
- name
- age
- profession
- biopic (two-line summary)

Ensure the output is a JSON array under key 'awardees'.
"""

# Call LLM
async def call_llm():
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

# Parse, validate, and save
async def safe_parse_llm(max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            raw_output = await call_llm()
            data = json.loads(raw_output)

            validated_awardees = []
            for entry in data.get("awardees", []):
                validated_awardees.append(AwardeeSchema(**entry).model_dump())

            # ✅ Print to terminal
            print("✅ Validated awardees:")
            for awardee in validated_awardees:
                print(awardee)

            # ✅ Save raw JSON output
            with open("llm_output.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # ✅ Save validated Python dict
            with open("llm_output_python.json", "w", encoding="utf-8") as f:
                json.dump(validated_awardees, f, indent=2, ensure_ascii=False)

            print("📂 Files saved: llm_output.json & llm_output_python.json")
            return validated_awardees

        except (json.JSONDecodeError, ValidationError) as e:
            print(f"⚠️ Attempt {attempt}: Malformed output -> {e}")
            if attempt == max_retries:
                print("❌ Failed after maximum retries.")
                return None
            print("🔄 Retrying...")

if __name__ == "__main__":
    asyncio.run(safe_parse_llm())
