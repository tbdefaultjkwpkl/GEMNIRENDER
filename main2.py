import asyncio
import json
import os
import websockets
from google import genai
import base64

# Retrieve your Gemini API key from the environment
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "AIzaSyDDUg7a80PHfYnIGoJKBpaeDVcPDfw8ySg")
MODEL = "gemini-2.0-flash-exp"  # Update this as required

# Your PieSocket channel URL
PIE_SOCKET_URL = "wss://s14182.blr1.piesocket.com/v3/1?api_key=AKsu6asGbktozdAbrTU7DLYgoV48Y9aeHpWqqB3d&notify_self=1"

# Initialize the Gemini client (make sure google-genai is installed)
client = genai.Client(http_options={'api_version': 'v1alpha'})

async def process_message(data):
    """
    Process incoming data from PieSocket.
    If it's a chat message, forward it to Gemini and return Gemini's text response.
    """
    if "chat_message" in data:
        chat_text = data["chat_message"].get("text", "").strip()
        if chat_text:
            print("Received chat message:", chat_text)
            try:
                # Connect to Gemini API
                async with client.aio.live.connect(model=MODEL, config={}) as session:
                    await session.send({"text": chat_text})
                    # For simplicity, take the first text response
                    async for response in session.receive():
                        if response.server_content and response.server_content.model_turn:
                            for part in response.server_content.model_turn.parts:
                                if hasattr(part, 'text') and part.text:
                                    print("Gemini replied:", part.text)
                                    # Return Gemini's reply
                                    return {"text": part.text}
                        # If the turn is complete, break out
                        if response.server_content.turn_complete:
                            break
            except Exception as e:
                print("Error calling Gemini API:", e)
    return None

async def listen_and_process():
    """
    Connects to the PieSocket channel and listens for incoming messages.
    For each chat message received, processes it and publishes the response.
    """
    async with websockets.connect(PIE_SOCKET_URL) as ws:
        print("Connected to PieSocket as Gemini bot")
        # Optionally, send a setup message if required by Gemini.
        await ws.send(json.dumps({"setup": {"generation_config": {"response_modalities": ["AUDIO"]}}}))
        while True:
            try:
                message = await ws.recv()
                try:
                    data = json.loads(message)
                except Exception as parse_err:
                    print("Error parsing incoming message:", parse_err)
                    continue

                # Optionally ignore messages that the bot itself sent (if needed)
                # For demo purposes, if the message has a key "from_bot", skip processing.
                if data.get("from_bot"):
                    continue

                # Process chat messages
                if "chat_message" in data:
                    response_payload = await process_message(data)
                    if response_payload:
                        # Mark this message as coming from the bot
                        response_payload["from_bot"] = True
                        await ws.send(json.dumps(response_payload))
                        print("Sent Gemini response:", response_payload)
            except Exception as e:
                print("Error in PieSocket message loop:", e)
                await asyncio.sleep(5)  # Retry delay

async def main():
    # Continuously try to connect to PieSocket
    while True:
        try:
            await listen_and_process()
        except Exception as e:
            print("Connection error, retrying in 5 seconds:", e)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
