"""
Run with: pytest tests/test_pdf_export.py
"""
import os
import sys

os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agent.pdf_export import markdown_to_pdf  # noqa: E402


def test_markdown_to_pdf_produces_nonempty_valid_pdf(tmp_path):
    markdown_text = "# Trip to Tokyo\n\n## Day 1\n- Arrive at Narita\n- Check into hotel\n"
    output_path = tmp_path / "test_itinerary.pdf"

    result_path = markdown_to_pdf(markdown_text, str(output_path))

    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 0

    with open(result_path, "rb") as f:
        header = f.read(5)
    assert header == b"%PDF-"  # valid PDF magic bytes
