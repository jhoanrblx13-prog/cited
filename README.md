# Cited

Ask a question about a document. The answer is a passage from that document, or a refusal if the document does not contain it.

Demo: https://cited-nnf4.onrender.com

Load the sample, or paste text, or upload a PDF or txt file. Then ask.

Questions that work on the sample: when does the yard shift start, what plan is NX-DEMO-1042, are Sunday deliveries accepted.

A question about payroll is refused. There is no model call and no key. Matching is term overlap against the passages in the file.

## Run

```bash
cd cited
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
