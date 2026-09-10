import os
import uuid

import markdown as md_lib
from xhtml2pdf import pisa

from app.agent.state import TravelState
from app.config import PDF_BUCKET, PDF_URL_EXPIRY_SECONDS, LOCAL_PDF_DIR
from app.logging_config import logger

os.makedirs(LOCAL_PDF_DIR, exist_ok=True)

PDF_CSS = """
<style>
    body { font-family: Helvetica, Arial, sans-serif; font-size: 11pt; color: #222; line-height: 1.5; }
    h1 { font-size: 20pt; color: #1a4d8f; border-bottom: 2px solid #1a4d8f; padding-bottom: 6px; }
    h2 { font-size: 15pt; color: #1a4d8f; margin-top: 22px; }
    h3 { font-size: 12.5pt; color: #333; margin-top: 14px; }
    table { border-collapse: collapse; width: 100%; margin: 10px 0; }
    th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: left; font-size: 10pt; }
    th { background-color: #eef3fb; }
    ul, ol { margin-left: 4px; }
</style>
"""


def markdown_to_pdf(markdown_text: str, output_path: str) -> str:
    """Converts a Markdown string into a styled PDF file on disk. Returns the file path."""
    html_body = md_lib.markdown(markdown_text, extensions=["extra", "sane_lists", "nl2br"])
    full_html = f"<html><head><meta charset='utf-8'>{PDF_CSS}</head><body>{html_body}</body></html>"

    with open(output_path, "wb") as f:
        pisa_status = pisa.CreatePDF(src=full_html, dest=f)

    if pisa_status.err:
        raise RuntimeError(f"xhtml2pdf reported {pisa_status.err} error(s) while rendering the PDF.")

    return output_path


def _upload_to_s3(local_path: str, key: str) -> str:
    import boto3  # imported lazily so boto3 is only required if S3 mode is used

    s3 = boto3.client("s3")
    s3.upload_file(local_path, PDF_BUCKET, key, ExtraArgs={"ContentType": "application/pdf"})
    os.remove(local_path)  # don't accumulate files on the container's ephemeral disk
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": PDF_BUCKET, "Key": key},
        ExpiresIn=PDF_URL_EXPIRY_SECONDS,
    )


def pdf_agent(state: TravelState):
    """Takes the latest assistant answer (final proposal or follow-up) and
    exports it as a downloadable PDF. Uploads to S3 if PDF_BUCKET is
    configured (recommended for production); otherwise falls back to a
    local file path (fine for local dev, NOT durable in production since
    container filesystems are ephemeral and non-shared across replicas).
    """
    last_message = state["messages"][-1]
    content_for_pdf = getattr(last_message, "content", "") or state.get("itinerary", "")

    if not content_for_pdf.strip():
        logger.warning("pdf_agent: nothing to render, skipping PDF generation")
        return {"pdf_path": ""}

    filename = f"itinerary_{uuid.uuid4().hex[:10]}.pdf"
    local_path = os.path.join(LOCAL_PDF_DIR, filename)

    try:
        markdown_to_pdf(content_for_pdf, local_path)
    except Exception as e:
        logger.exception("PDF generation failed")
        return {"pdf_path": f"PDF generation failed: {e}"}

    if PDF_BUCKET:
        try:
            url = _upload_to_s3(local_path, key=filename)
            return {"pdf_path": url}
        except Exception as e:
            logger.exception("S3 upload failed, falling back to local path")
            return {"pdf_path": local_path}

    logger.warning("PDF_BUCKET not set - using local disk storage (not durable in production)")
    return {"pdf_path": local_path}
