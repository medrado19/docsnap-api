from fastapi import FastAPI, UploadFile, File
import base64
import os
from openai import OpenAI

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/")
def home():
    return {"message": "DocSnap API is running 🚀"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    
    # convert file to base64 (so AI can read it)
    encoded = base64.b64encode(contents).decode()

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Extract key info: client name, total amount, date"},
                    {
                        "type": "input_image",
                        "image_base64": encoded,
                    },
                ],
            }
        ],
    )

    return {
        "filename": file.filename,
        "ai_output": response.output_text
    }
