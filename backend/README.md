# PaperChat Backend

Sprint 1 establishes the FastAPI backend foundation for PaperChat. It includes application setup, environment-based settings, logging, base exceptions, and health endpoints only.

## Create a Virtual Environment

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Install Dependencies

```powershell
pip install -r requirements.txt
```

## Configure Environment

Create a local `.env` file from `.env.example` and adjust values as needed.

```powershell
Copy-Item .env.example .env
```

PDF generation defaults to the existing Playwright engine:

```powershell
PDF_ENGINE=playwright
```

To try the print-aware WeasyPrint engine:

```powershell
PDF_ENGINE=weasyprint
```

Optional document layout modes are configured without changing API payloads:

```powershell
DOCUMENT_LAYOUT=single      # default
DOCUMENT_LAYOUT=two-column  # prose may flow in columns
DOCUMENT_LAYOUT=auto        # browser/renderer chooses column width
```

On Windows, WeasyPrint also requires native GTK/Pango libraries. If PDF generation fails with a missing library such as `libgobject-2.0-0`, install the GTK runtime dependencies documented by WeasyPrint/CourtBouillon, then restart the shell so the DLLs are on `PATH`. The Playwright exporter is lazy-loaded and remains usable with `PDF_ENGINE=playwright` even when WeasyPrint native dependencies are unavailable.

## Run the API

```powershell
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Endpoints

- `GET /` returns API metadata.
- `GET /health` returns service health status.

## Project Structure

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   ├── utils/
│   └── main.py
├── tests/
├── config.py
├── exceptions.py
├── logger.py
├── main.py
├── settings.py
├── requirements.txt
├── .env.example
└── README.md
```
