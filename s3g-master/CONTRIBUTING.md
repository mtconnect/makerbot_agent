# Contributing to MakerBot Driver
This covers how to contribute to the magic of MakerBot Driver

## MakerBot Dirver Is
 - A device driver for MakerBot products, using the s3g protocol
 - A magic and fun way to connect to your robot buddies
 - A Open Source community effort to create stable, awesome drivers in python

## Guidelines
 If you want to contribute to makerbot_driver, you'll need to make sure it hits pep-8

## Tools
First, install pep8 checker (pip install pep8) and then you probably want the pep-8 converter (pip intall autopep8). Then move the pep8 precommit hook over into your git hooks directory (cp git_hook_pre-commit .git/hooks/pre-commit | sudo chmod 777 .git/hooks/pre-commit'

Now your git setup will always check pep8 before you commit. It will drive you crazy, but keep everyone else sane.

If you want to convert a whole file to pep8, use autopep8 <FILENAME> to do so
autopep8 makerbot_driver/ --recursive --in-place

### Thanks!
Thanks to Matt Mets for starting this awesome codebase
