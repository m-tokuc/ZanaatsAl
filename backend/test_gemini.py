import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel('gemini-2.5-flash')
try:
    response = model.generate_content("Merhaba")
    print("Success:", response.text)
except Exception as e:
    print("Error:", str(e))
