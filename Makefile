test:
	pylint3 search.py
	python3 -m unittest tests/test_*.py

