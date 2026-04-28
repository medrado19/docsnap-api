from fastapi import FastAPI, UploadFile, File
import base64
import os
from openai import OpenAI

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        encoded = base64.b64encode(contents).decode()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract client name, total amount, and date from this invoice"},
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{encoded}"
                        }
                    ]
                }
            ]
        )

        return {
            "filename": file.filename,
            "ai_output": response.choices[0].message.content
        }

    except Exception as e:
        return {"error": str(e)}

