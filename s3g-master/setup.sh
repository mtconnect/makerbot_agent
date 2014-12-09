#! /bin/sh

if [ ! -d virtualenv/ ]
then
	python virtualenv.py virtualenv
fi

. virtualenv/bin/activate
pip install --use-mirrors coverage doxypy unittest-xml-reporting mock
easy_install submodule/conveyor_bins/pyserial-2.7_mb2.1-py2.7.egg
export PYTHONPATH=./:$PYTHONPATH
