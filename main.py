import os
import re
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="Cited")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=str(ROOT / "templates"))

SAMPLE = """Harbor desk notes, March 2026.

The yard shift starts at 06:30. Late arrivals sign the paper log by the north door. The log is not a substitute for the badge reader.

License NX-DEMO-1042 belongs to Northline Studio. It is an active Desk plan. It was issued for one seat and does not include the Bench tools.

Refunds are not offered after a license is revoked. A revoked license can be reissued only by an admin, and the old key stays revoked.

The loading dock is closed on Sundays. Deliveries on Sunday are refused at the gate, even with a booking.
"""

STOP = {"the", "a", "an", "is", "are", "was", "were", "of", "to", "for", "and", "or", "in", "on", "at", "it", "this", "that", "with", "does", "do", "what", "when", "where", "who", "how"}
docs: dict[str, dict] = {}


def words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9-]{3,}", text.lower()) if w not in STOP]


def chunks(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if parts:
        return parts
    return [text.strip()] if text.strip() else []


def read_upload(raw: bytes, name: str) -> str:
    if name.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(raw))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    return raw.decode("utf-8", errors="ignore")


def answer(text: str, question: str) -> dict:
    passages = chunks(text)
    query = words(question)
    if not passages or not query:
        return {"ok": False, "reason": "Add a document and a real question first."}
    best_score = 0
    best = ""
    best_no = 0
    for number, passage in enumerate(passages, start=1):
        passage_words = set(words(passage))
        score = sum(1 for term in query if term in passage_words)
        if score > best_score:
            best_score = score
            best = passage
            best_no = number
    needed = 2 if len(query) >= 2 else 1
    if best_score < needed:
        return {"ok": False, "reason": "That is not in this document."}
    return {"ok": True, "passage": best, "passage_no": best_no, "score": best_score}


def session_id(request: Request) -> str:
    return request.cookies.get("cited") or os.urandom(8).hex()


def page(request: Request, **extra):
    sid = request.cookies.get("cited")
    doc = docs.get(sid or "", {})
    context = {
        "doc_name": doc.get("name", "No document loaded"),
        "draft": doc.get("text", ""),
        "question": "",
        "result": None,
    }
    context.update(extra)
    response = templates.TemplateResponse(request, "index.html", context)
    if sid and request.cookies.get("cited") != sid:
        response.set_cookie("cited", sid, httponly=True, samesite="lax")
    return response


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return page(request)


@app.post("/document", response_class=HTMLResponse)
async def set_document(
    request: Request,
    text: str = Form(""),
    file: UploadFile | None = File(None),
):
    sid = session_id(request)
    body = text.strip()
    name = "Pasted text"
    if file and file.filename:
        raw = await file.read()
        if raw:
            body = read_upload(raw, file.filename).strip()
            name = file.filename
    docs[sid] = {"name": name if body else "No document loaded", "text": body}
    response = page(request, draft=body, doc_name=docs[sid]["name"])
    response.set_cookie("cited", sid, httponly=True, samesite="lax")
    return response


@app.post("/sample", response_class=HTMLResponse)
def sample(request: Request):
    sid = session_id(request)
    docs[sid] = {"name": "Harbor desk notes", "text": SAMPLE}
    response = page(request, draft=SAMPLE, doc_name="Harbor desk notes")
    response.set_cookie("cited", sid, httponly=True, samesite="lax")
    return response


@app.post("/ask", response_class=HTMLResponse)
def ask(request: Request, question: str = Form(...)):
    sid = request.cookies.get("cited")
    doc = docs.get(sid or "")
    if not doc or not doc.get("text"):
        return page(request, question=question, result={"ok": False, "reason": "Load a document first."})
    return page(request, question=question, result=answer(doc["text"], question), draft=doc["text"], doc_name=doc["name"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
