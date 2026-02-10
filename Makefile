.PHONY: test

test:
	coverage run --branch --source=. -m pytest
	coverage report -m
	coverage html

CHECKABLE := linklint.py test_linklint.py

quality:
	uvx ty check ${CHECKABLE}
	uvx ruff check ${CHECKABLE}
