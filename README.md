PyAudacity
======

A Python module to control a running instance of Audacity through its [mod-script-pipe macro system](https://manual.audacityteam.org/man/scripting.html).

The main macros listed on https://manual.audacityteam.org/man/scripting_reference.html are supported, but many still are not. If a function call raises `NotImplementedError`, that function isn't finished yet.

IMPORTANT! If you use this module, please get in touch with al@inventwithpython.com I'd like to hear how people are using it and what changes I can make or features I should prioritize.

Installation
------------

To install with pip, run:

    pip install pyaudacity

Quickstart Guide
----------------

NOTE: Audacity must be running to use this module.

NOTE: The module works on the latest Audacity window opened if there are multiple Audacity windows open.

NOTE: On Windows, you'll have to run the Python script with admin privs.

Python 3.4 minimum

TODO - fill this in later
