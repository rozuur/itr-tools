VENV_NAME?=.venv
VENV_BIN=$(VENV_NAME)/bin
SRC_DIR=src
TESTS_DIR=tests

.DEFAULT_GOAL := help

# Disable output buffering
export PYTHONUNBUFFERED=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

venv: $(VENV_NAME)/bin/black #: Setup virtual environment
$(VENV_NAME)/bin/black: $(VENV_BIN)/pip-compile requirements.in dev-requirements.in
	$(VENV_BIN)/pip-compile -q --build-isolation requirements.in
	$(VENV_BIN)/pip-compile -q --build-isolation dev-requirements.in
	$(VENV_BIN)/pip-sync -q requirements.txt dev-requirements.txt
	touch $(VENV_NAME)/bin/black

$(VENV_BIN)/pip-compile: $(VENV_NAME)/bin/activate
	$(VENV_BIN)/pip install -q pip-tools
	touch $(VENV_BIN)/pip-compile

$(VENV_NAME)/bin/activate:
	test -d $(VENV_NAME) || python -m venv $(VENV_NAME)
	touch $(VENV_NAME)/bin/activate


format: venv #: Format and fix python code
	$(VENV_BIN)/isort $(SRC_DIR) $(TESTS_DIR)
	$(VENV_BIN)/black $(SRC_DIR) $(TESTS_DIR)
	$(VENV_BIN)/autoflake --remove-all-unused-imports --remove-unused-variables \
		--remove-duplicate-keys --ignore-init-module-imports -i -r $(SRC_DIR) $(TESTS_DIR)

check-flake8: venv
	$(VENV_BIN)/flake8 $(SRC_DIR) $(TESTS_DIR)


test: venv #: Run tests and fail if coverage is not met
# Use `python -m pytest` which also adds current directory to `sys.path`.
	$(VENV_BIN)/python -m pytest --cov-report=html:htmlcov --cov $(SRC_DIR)

help: #: List make tasks which are documented, doc string starts with #:
	@grep -E '^[a-zA-Z0-9_-]+:.*?#: .*$$' $(MAKEFILE_LIST) \
	| cut -d: -f1,3-
