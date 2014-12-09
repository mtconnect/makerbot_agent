#! /bin/sh

# set -x

# virtualenv failing for now, avoiding that need for this
#source setup.sh
python unit_tests.py 
_code=$?
exit ${_code}
