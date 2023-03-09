PyAudacity
======

A Python module to control a running instance of Audacity through its [mod-script-pipe macro system](https://manual.audacityteam.org/man/scripting.html).

The main macros listed on https://manual.audacityteam.org/man/scripting_reference.html are supported, but many still are not. If a function call raises `NotImplementedError`, that function isn't finished yet.

IMPORTANT! If you use this module, please get in touch with al@inventwithpython.com I'd like to hear how people are using it and what changes I can make or features I should prioritize.

Installation
------------

To install with pip, run:

    pip install pyaudacity

PyAudacity is a pure Python module and has no dependencies, although you must install Audacity. Audacity must be open while your PyAudacity-using Python scripts run. (That is, there is no "headless" mode for PyAudacity.)

Quickstart Guide
----------------

NOTE: Audacity must be running to use this module.

NOTE: If you have multiple Audacity windows open, the macros you run work on the last Audacity window opened. You can't select which window you want the macros sent to.

NOTE: Macros run from PyAudacity or the mod-script-pipe system aren't added to the undo history of a project.

NOTE: On Windows, if you see `OSError: [Errno 22] Invalid argument: '\\\\.\\pipe\\ToSrvPipe'` you'll have to run your Python script as an Administrator. I don't know why this is sometimes needed and not needed other times.

Currently, PyAudacity is in a semi-complete state. I'm waiting to hear back from folks to see if this module is actually useful. Please email me at al@inventwithpython.com

Check out the [Scripting Reference page on the Audacity wiki](https://manual.audacityteam.org/man/scripting_reference.html) for documentation about the various macros. You can call `pyaudacity.do()` to run these macros on the currently opened Audacity project.

For example, this creates a new project and adds a two-second Brownian noise sample:

    >>> import pyaudacity as pa
    >>> pa.do('New')
    '\nBatchCommand finished: OK\n'
    >>> pa.do('NewMonoTrack')
    '\nBatchCommand finished: OK\n'
    >>> pa.do('SelectTime: Start="1" End="3"')
    '\nBatchCommand finished: OK\n'
    >>> pa.do('Noise: Type="Brownian" Amplitude="0.8"')
    '\nBatchCommand finished: OK\n'

If you enter wrong parameter names, Audacity's macros fail silently. (Or other times, a pop-up alert window appears, which will also stop any automation until a human closes it.)

The aim of PyAudacity is to make the Audacity macro system easy to use by providing the `do()` function and also several convenience functions that raise `PyAudacityException` if you pass invalid arguments.

For example, the following does the same as the above example:

    >>> import pyaudacity as pa
    >>> pa.new()
    '\nBatchCommand finished: OK\n'
    >>> pa.new_mono_track()
    '\nBatchCommand finished: OK\n'
    >>> pa.select_time(1.0, 3.0)
    '\nBatchCommand finished: OK\n'
    >>> pa.noise(noise_type='Brownian', amplitude=0.8)
    '\nBatchCommand finished: OK\n'

PyAudacity is still under development, and a lot of work needs be done for argument validation. You can always use the `do()` function, but keep in mind that the convenience functions can have their function signatures rapidly change in the future as this library is developed. As such, the best way to find functions is to examine the source code, unfortunately.


PyAudacity Wishlist for Audacity Macro Features
----------------

It'd be great if Audacity added the following the macro system:

* A macro batch command to retrieve the version number of Audacity.

