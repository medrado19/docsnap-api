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
    try:
        contents = await file.read()
        encoded = base64.b64encode(contents).decode()

        data_url = f"data:{file.content_type};base64,{encoded}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract the client name, invoice date, total amount, and services from this invoice."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url
                            }
                        }
                    ]
                }
            ]
        )

        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "ai_output": response.choices[0].message.content
        }

    except Exception as e:
        return {"error": str(e)}
