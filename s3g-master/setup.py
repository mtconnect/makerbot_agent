# setup.py for pySerial
#
# Windows installer:
#   "python setup.py bdist_wininst"
#
# Direct install (all systems):
#   "python setup.py install"
#
# For Python 3.x use the corresponding Python executable,
# e.g. "python3 setup.py ..."
import sys

from distutils.core import setup

import re
import os
if sys.version_info >= (3, 0):
    try:
        from distutils.command.build_py import build_py_2to3 as build_py
        from distutils.command.build_scripts import build_scripts_2to3 as build_scripts
    except ImportError:
        raise ImportError("build_py_2to3 not found in distutils - it is required for Python 3.x")
    suffix = "-py3k"
else:
    from distutils.command.build_py import build_py
    from distutils.command.build_scripts import build_scripts
    suffix = ""


if sys.version < '2.6':
    # distutils that old can't cope with the "classifiers" or "download_url"
    # keywords and True/False constants and basestring are missing
    raise ValueError("Sorry Python versions older than 2.6 are not "
                     "supported. Sadly we will probably never support them :(")

if sys.version >= '2.6' and sys.version < '3.0':
    import makerbot_driver
    version = makerbot_driver.__version__

elif sys.version >= 3.0:
    import re
    import os
    version = re.search(
        "__version__.*'(.+)'",
        open(os.path.join('makerbot_driver', '__init__.py')).read()).group(1)

# Walk the source tree to collect all the json files.
import fnmatch
json_files = []
for (path, dirs, files) in os.walk('makerbot_driver'):
    for f in files:
        if fnmatch.fnmatch(f, '*.json'):
            json_files.append(os.path.join(path, f))


setup(
    name='makerbot_driver' + suffix,
    version=version,
    author=['Matt Mets', 'David Sayles (MBI)', 'Far McKon (MBI)'],
    author_email=['cibomahto@gmail.com', 'david.sayles@makerbot.com',
                  'far@makerbot.com'],
    packages=[
        'makerbot_driver',
        'makerbot_driver.EEPROM',
        'makerbot_driver.Encoder',
        'makerbot_driver.FileReader',
        'makerbot_driver.Firmware',
        'makerbot_driver.Gcode',
        'makerbot_driver.GcodeProcessors',
        'makerbot_driver.Writer'
    ],
    package_data={'makerbot_driver.EEPROM': ['*.json'],
                  'makerbot_driver.Firmware': ['*.conf']},
    url='http://github.com/makerbot/s3g',
    license='LICENSE.txt',
    description='Python driver to connect to MakerBot 3D Printers which use the s3g protocol',
    long_description=open('README.md').read(),
        platforms='any',
)
