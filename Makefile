.PHONY: test quality clean

test:
	coverage run --branch --source=. -m pytest
	coverage report -m
	coverage html

EXCLUDE := --exclude dump.py

quality:
	uvx ty check ${EXCLUDE}
	uvx ruff check ${EXCLUDE}

clean:
	rm -rf .coverage htmlcov
