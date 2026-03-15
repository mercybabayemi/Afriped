"""
HuggingFace Spaces entry point.
Single-server: Gradio mounted inside FastAPI on port 7860.
  - FastAPI handles /api/v1/* routes
  - Gradio UI served at /
  - One uvicorn, one event loop — queue starts cleanly
"""
import gradio as gr
import uvicorn

from app.main import app as fastapi_app
from app.ui.gradio_app import create_app

demo = create_app()
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info")
