init:
	pip3 install -r dev/requirements.txt

test:
	pylint notesnv/search.py
	eval "PYTHONPATH=`pwd` py.test --flake8 tests/"

run:
	VERBOSE=1 ULAUNCHER_WS_API=ws://127.0.0.1:5054/com.github.pbkhrv.ulauncher-notes-nv PYTHONPATH=/usr/lib/python3/dist-packages /usr/bin/python3 `pwd`/main.py
