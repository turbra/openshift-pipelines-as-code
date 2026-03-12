import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="sample-app", docs_url=None, redoc_url=None, openapi_url=None)


def _response_message() -> str:
    return os.getenv("RESPONSE", "Hello OpenShift!")


@app.get("/", include_in_schema=False)
def root() -> HTMLResponse:
    hostname = os.getenv("HOSTNAME", "unknown")
    body = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Sample OpenShift App</title>
    <style>
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background: linear-gradient(180deg, #f4efe4 0%, #e5dcc7 100%);
        color: #1f2933;
        font-family: Georgia, "Times New Roman", serif;
      }}
      main {{
        width: min(92vw, 640px);
        padding: 2.5rem;
        border: 1px solid #b89b66;
        background: rgba(255, 252, 246, 0.94);
        box-shadow: 0 20px 50px rgba(49, 38, 17, 0.12);
      }}
      h1 {{
        margin: 0 0 0.75rem;
        font-size: clamp(2rem, 4vw, 3rem);
      }}
      p {{
        margin: 0.5rem 0;
        line-height: 1.5;
        font-size: 1.05rem;
      }}
      code {{
        padding: 0.1rem 0.35rem;
        background: #efe4cf;
      }}
    </style>
  </head>
  <body>
    <main>
      <h1>{_response_message()}</h1>
      <p>This starter app is configured for OpenShift Pipelines as Code.</p>
      <p>Current pod hostname: <code>{hostname}</code></p>
      <p>Change the <code>RESPONSE</code> environment variable to customize this page.</p>
    </main>
  </body>
</html>"""
    return HTMLResponse(content=body)


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict[str, str]:
    return {"status": "ok"}
