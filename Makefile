install:
		pip install --upgrade pip &&\
				pip instal - requirements.txt

test:
	python -m pytest -vv 

format:
		black *.py

lint:	
		pylint --disable=R,C 

all: install lint test 		


