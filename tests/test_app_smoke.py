from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_app_renders_without_exception():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
    assert not app.exception
    assert app.title[0].value == "Validator Deployment QA"
    assert app.button[0].label == "Jalankan Validasi"
    assert not app.toggle
