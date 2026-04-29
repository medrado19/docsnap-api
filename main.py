from fastapi import FastAPI, UploadFile, File
import base64
import os
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/")
def home():
    return {"message": "DocSnap API is running 🚀"}

@app.get("/test")
def test():
    return {"status": "working"}

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
                            "text": """
Extract the invoice data from this image.

Return ONLY valid JSON.
Do not include explanations.
Do not use markdown.

Use this exact format:
{
  "client_name": "",
  "invoice_date": "",
  "total_amount": 0,
  "services": [
    {
      "description": "",
      "quantity": 0,
      "unit_price": 0,
      "total": 0
    }
  ]
}
"""
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
