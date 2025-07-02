import os
from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import tempfile
import openai
import fitz  # PyMuPDF

app = FastAPI()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_index():
    return FileResponse("static/index.html")

def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def summarize_text(text: str, max_tokens:int=200) -> str:
    prompt = (
        "Summarize the following startup pitch deck for an investor. "
        "Focus on team, product, market, financials, and potential risks:\n\n"
        f"{text}\n\nSummary:"
    )
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.5,
    )
    return response.choices[0].text.strip()

@app.post("/summarize-pdf/")
async def summarize_pdf(file: UploadFile = File(...), max_tokens: int = 200):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name
    text = extract_text_from_pdf(tmp_path)
    os.remove(tmp_path)
    summary = summarize_text(text, max_tokens=max_tokens)
    return {"summary": summary}