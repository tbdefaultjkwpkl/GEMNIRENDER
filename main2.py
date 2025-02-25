import asyncio
import json
import os
import websockets
from google import genai
import base64
import http

# Load API key from environment
os.environ['GOOGLE_API_KEY'] = 'AIzaSyDDUg7a80PHfYnIGoJKBpaeDVcPDfw8ySg'
MODEL = "gemini-2.0-flash-exp"  # use your model ID

client = genai.Client(
    http_options={'api_version': 'v1alpha'}
)

# Custom process_request to handle non-websocket requests gracefully (e.g., HEAD)
async def process_request(path, request_headers):
    if request_headers.get("Upgrade", "").lower() != "websocket":
        # Return a simple HTTP 200 response with proper headers
        return http.HTTPStatus.OK, [("Content-Type", "text/plain"), ("Content-Length", "2")], b"OK"

async def gemini_session_handler(client_websocket: websockets.WebSocketServerProtocol):
    """Handles the interaction with Gemini API within a websocket session."""
    try:
        config_message = await client_websocket.recv()
        config_data = json.loads(config_message)
        config = config_data.get("setup", {})

        async with client.aio.live.connect(model=MODEL, config=config) as session:
            print("Connected to Gemini API")

            async def send_to_gemini():
                try:
                    async for message in client_websocket:
                        try:
                            data = json.loads(message)
                            if "realtime_input" in data:
                                for chunk in data["realtime_input"]["media_chunks"]:
                                    if chunk["mime_type"] == "audio/pcm":
                                        await session.send({"mime_type": "audio/pcm", "data": chunk["data"]})
                                    elif chunk["mime_type"] == "image/jpeg":
                                        await session.send({"mime_type": "image/jpeg", "data": chunk["data"]})
                            if "chat_message" in data:
                                chat_text = data["chat_message"].get("text", "")
                                print("Sending chat text to Gemini:", chat_text)
                                await session.send({"text": chat_text})
                                if "image" in data["chat_message"]:
                                    await session.send({"mime_type": "image/jpeg", "data": data["chat_message"]["image"]})
                        except Exception as e:
                            print(f"Error sending to Gemini: {e}")
                    print("Client connection closed (send)")
                except Exception as e:
                    print(f"Error sending to Gemini: {e}")
                finally:
                    print("send_to_gemini closed")

            async def receive_from_gemini():
                try:
                    while True:
                        try:
                            print("Receiving from Gemini...")
                            async for response in session.receive():
                                if response.server_content is None:
                                    print(f"Unhandled server message: {response}")
                                    continue
                                model_turn = response.server_content.model_turn
                                if model_turn:
                                    for part in model_turn.parts:
                                        if hasattr(part, 'text') and part.text is not None:
                                            await client_websocket.send(json.dumps({"text": part.text}))
                                        elif hasattr(part, 'inline_data') and part.inline_data is not None:
                                            base64_audio = base64.b64encode(part.inline_data.data).decode('utf-8')
                                            await client_websocket.send(json.dumps({"audio": base64_audio}))
                                if response.server_content.turn_complete:
                                    print("<Turn complete>")
                        except websockets.exceptions.ConnectionClosedOK:
                            print("Client connection closed normally (receive)")
                            break
                        except Exception as e:
                            print(f"Error receiving from Gemini: {e}")
                            break
                except Exception as e:
                    print(f"Error receiving from Gemini: {e}")
                finally:
                    print("Gemini connection closed (receive)")

            send_task = asyncio.create_task(send_to_gemini())
            receive_task = asyncio.create_task(receive_from_gemini())
            await asyncio.gather(send_task, receive_task)

    except Exception as e:
        print(f"Error in Gemini session: {e}")
    finally:
        print("Gemini session closed.")

async def main():
    async with websockets.serve(
        gemini_session_handler, "0.0.0.0", 9080, process_request=process_request
    ):
        print("Running websocket server on port 9080...")
        await asyncio.Future()  # Keep the server running indefinitely

if __name__ == "__main__":
    asyncio.run(main())
