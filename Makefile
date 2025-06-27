.PHONY: all lint test test-cov test-docker install dev clean distclean

PYTHON ?= python

all: ;

lint:
	q2lint
	flake8

test: all
	py.test

test-cov: all
	python -m pytest --cov=q2_checkm -n 4 && coverage xml -o coverage.xml

test-docker: all
	qiime info
	qiime checkm --help

install: all
	bash install-pplacer.sh
	$(PYTHON) -m pip install -v .
	$(PYTHON) -m pip install -v git+https://github.com/Ecogenomics/CheckM.git@4c11fed446ae7b728031f67b3c0d618ebc0ea39c

dev: all
	bash install-pplacer.sh
	$(PYTHON) -m pip install pre-commit git+https://github.com/Ecogenomics/CheckM.git@4c11fed446ae7b728031f67b3c0d618ebc0ea39c
	$(PYTHON) -m pip install -e .
	pre-commit install

clean: distclean

distclean: ;
