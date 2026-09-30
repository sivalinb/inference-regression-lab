BUTTON='Run benchmark'
from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_primary_portable_workflow():
    root=Path(__file__).resolve().parents[1]
    app=AppTest.from_file(str(root/'app.py'),default_timeout=30).run()
    assert not app.exception
    next(b for b in app.button if b.label==BUTTON).click().run(timeout=30)
    assert not app.exception
    assert not app.error
    assert len(app.metric)+len(app.json)+len(app.dataframe)>0
