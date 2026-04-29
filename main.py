from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import base64
import os
import json
from openai import OpenAI
import psycopg2

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()


@app.get("/")
def home():
    return {"message": "DocSnap API is running 🚀"}


@app.get("/test")
def test():
    return {"status": "working"}


@app.get("/invoices")
def get_invoices():
    try:
        cursor.execute("""
            SELECT client_name, invoice_date, total_amount, category, services, created_at
            FROM invoices
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        invoices = []

        for row in rows:
            invoices.append({
                "client_name": row[0],
                "invoice_date": row[1],
                "total_amount": float(row[2]) if row[2] is not None else 0,
                "category": row[3],
                "services": row[4],
                "created_at": str(row[5])
            })

        return invoices

    except Exception as e:
        return {"error": str(e)}


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
                    "content": "You are a strict JSON generator. You only return valid JSON."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """
Extract the invoice data AND categorize it.

Return ONLY JSON in this format:
{
  "client_name": "",
  "invoice_date": "",
  "total_amount": 0,
  "category": "",
  "services": [
    {
      "description": "",
      "quantity": 0,
      "unit_price": 0,
      "total": 0
    }
  ]
}

Choose ONE category:
Repairs, Utilities, Rent, Supplies, Food, Marketing, Software, Transportation, Professional Services, Other.
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
        cleaned = raw_output.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        try:
            parsed_output = json.loads(cleaned)
        except:
            parsed_output = {"raw_text": cleaned}

        if "client_name" in parsed_output:
            cursor.execute("""
                INSERT INTO invoices (client_name, invoice_date, total_amount, category, services)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                parsed_output.get("client_name"),
                parsed_output.get("invoice_date"),
                parsed_output.get("total_amount"),
                parsed_output.get("category"),
                json.dumps(parsed_output.get("services"))
            ))

            conn.commit()

        return {
            "filename": file.filename,
            "structured_data": parsed_output
        }

    except Exception as e:
        return {"error": str(e)}
