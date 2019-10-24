init:
	pip3 install -r dev/requirements.txt

test:
	pylint notesnv/search.py
	eval "PYTHONPATH=`pwd` py.test"

