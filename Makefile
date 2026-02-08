.PHONY: test

test:
	coverage run --branch --source=. -m pytest
	coverage report -m
	coverage html
