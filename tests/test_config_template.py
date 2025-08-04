from pathlib import Path

def test_config_template_exists():
    assert (Path(__file__).resolve().parent.parent / "config.template.cfg").is_file()
