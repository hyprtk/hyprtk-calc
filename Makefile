.PHONY: test run install version qa shot

test:
	PYTHONPATH=. python3 -m unittest discover -s tests -v

run:
	./bin/hyprtk-calc

install:
	./install.sh

version:
	PYTHONPATH=. python3 -m hyprtk_calc --version

qa:
	./scripts/qa.sh

shot:
	python3 scripts/screenshot.py docs/shot.png
