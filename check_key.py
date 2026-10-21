"""Quick sanity check: is the Gemini key in .env and does it work?"""
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
key = os.getenv("GEMINI_API_KEY", "").strip()
if not key:
    raise SystemExit("No key found. Paste it after GEMINI_API_KEY= in the .env file and save.")

client = genai.Client(api_key=key)
reply = client.models.generate_content(model="gemini-flash-latest", contents="Reply with just: key works")
print(reply.text.strip())
