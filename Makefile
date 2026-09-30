.PHONY: setup app test eval config
setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install -r requirements-dev.txt
app:
	.venv/bin/streamlit run app.py --server.port 8504
test:
	.venv/bin/python -m pytest -q
eval:
	.venv/bin/python scripts/evaluate.py
config:
	.venv/bin/python scripts/export_config.py
