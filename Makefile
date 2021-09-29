VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

.PHONY: run clean

run: $(VENV)/bin/activate
	$(PYTHON) app.py

$(VENV)/bin/activate: Pipfile
	PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

clean:
	rm -rf __pycache__
	rm -rf $(VENV)