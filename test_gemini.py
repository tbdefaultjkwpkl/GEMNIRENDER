import google.generativeai as genai
import os

# Load API key
os.environ['GOOGLE_API_KEY'] = 'AIzaSyDDUg7a80PHfYnIGoJKBpaeDVcPDfw8ySg'

# Configure the model
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# Test prompt
prompt = "Hello, how are you?"

# Generate a response
try:
    response = model.generate_content(prompt)
    print("Gemini Response:", response.text)
except Exception as e:
    print("Error:", e)
