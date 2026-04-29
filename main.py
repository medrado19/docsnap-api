from fastapi import FastAPI, UploadFile, File
import base64
import os
import json
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
                    "role": "system",
                    "content": "You are a strict JSON generator. You ONLY return valid JSON. No text. No explanations."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """
Extract the invoice data.

Return ONLY JSON in this format:
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

        raw_output = response.choices[0].message.content

        # 🔥 Try to convert to real JSON
        try:
            parsed_output = json.loads(raw_output)
        except:
            parsed_output = {"raw_text": raw_output}

        return {
            "filename": file.filename,
            "structured_data": parsed_output
        }

    except Exception as e:
        return {"error": str(e)}
