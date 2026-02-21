.PHONY: venv install test quality clean dist

venv: .venv
.venv:
	uv venv -p 3.12 --prompt "linklint"

install: .venv
	uv pip install -e .[dev]

test:
	DUMP_DOCTREE=1 coverage run --branch --source=. -m pytest
	coverage report -m
	coverage html

quality:
	uvx ty check
	uvx ruff check

clean:
	rm -rf .coverage htmlcov tmp
	rm -rf build/ dist/ src/*.egg-info

dist: 	## Build the distributions.
	python -m build --sdist --wheel
