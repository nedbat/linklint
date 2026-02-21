.PHONY: test quality clean

test:
	DUMP_DOCTREE=1 coverage run --branch --source=. -m pytest
	coverage report -m
	coverage html

quality:
	uvx ty check
	uvx ruff check

clean:
	rm -rf .coverage htmlcov tmp
