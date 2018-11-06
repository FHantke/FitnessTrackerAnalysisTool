.PHONY: all

all: venv requirements run

venv:
	virtualenv --python=python3 venv
    
requirements:
	venv/bin/pip install -r requirements.txt

run:
	venv/bin/python main.py --help
    
clean:
	find . -name '*.pyc' -exec rm {} +
	find . -name '__pycache__' -exec rm -rf {} +
