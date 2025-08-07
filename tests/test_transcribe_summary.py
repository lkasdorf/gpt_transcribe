from pathlib import Path
import os
import builtins

import transcribe_summary as ts


def test_default_prompt_contains_iso_8601():
    assert "ISO 8601" in ts.DEFAULT_PROMPT


def test_strip_code_fences():
    text = """```
hello
world
```"""
    assert ts.strip_code_fences(text) == "hello\nworld"


def test_get_api_key_env_fallback(monkeypatch):
    cfg_path = ts.BASE_DIR / "config.cfg"
    # Prepare a minimal config
    cfg_path.write_text("""[openai]
api_key = YOUR_API_KEY
""", encoding="utf-8")
    cfg = ts.load_config(cfg_path)
    monkeypatch.setenv("OPENAI_API_KEY", "from_env")
    assert ts.get_api_key(cfg) == "from_env"


def test_markdown_to_pdf_smoke(tmp_path):
    md = "# Title\n\n- a\n- b\n\n```\ncode\n```\n\n## Sub\ntext"
    pdf_file = tmp_path / "out.pdf"
    ts.markdown_to_pdf(md, str(pdf_file))
    assert pdf_file.is_file()


