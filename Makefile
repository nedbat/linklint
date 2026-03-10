.PHONY: venv install test quality clean dist release

venv: .venv
.venv:
	uv venv -p 3.12 --prompt "linklint"

install: .venv
	uv pip install -e .[dev]

test:
	coverage run -m pytest
	coverage combine -q
	coverage report
	coverage html

quality:
	ty check
	ruff check
	ruff format

clean:
	rm -rf .coverage htmlcov tmp
	rm -rf build/ dist/ src/*.egg-info
	rm -rf __pycache__ */__pycache__

dist:
	python -m build --sdist --wheel

release:
	@echo "Update src/linklint/__init__.py"
	@echo "Update README.rst"
	@echo "Tag in git"
	@echo "Push to GitHub"
