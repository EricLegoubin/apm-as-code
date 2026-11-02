.PHONY: install check site
install:
	pip install -e .[dev]
check:
	pytest -q
	apm validate catalog
site:
	apm build catalog -o site
