.PHONY: venv install test quality clean dist

venv: .venv
.venv:
	uv venv -p 3.12 --prompt "linklint"

install: .venv
	uv pip install -e .[dev]

test:
	coverage run --branch -m pytest
	coverage report --show-missing --skip-covered
	coverage html

quality:
	ty check
	ruff check

clean:
	rm -rf .coverage htmlcov tmp
	rm -rf build/ dist/ src/*.egg-info

dist: 	## Build the distributions.
	python -m build --sdist --wheel
