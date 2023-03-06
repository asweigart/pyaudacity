"""PyAudacity
By Al Sweigart al@inventwithpython.com

A Python module to control a running instance of Audacity through its macro system."""

__version__ = '0.1.0'

import os, sys

# Set the end-of-line character that comes at the end of Audacity macro commands:
"""
if sys.platform == 'win32':
    EOL = '\r\n\0'
else:
    EOL = '\n'
"""

class PyAudacityException(Exception):
    """The base exception class for PyAudacity-related exceptions."""
    pass


def do_command(command):
    if sys.platform == 'win32':
        print("pipe-test.py, running on windows")
        write_file_name = '\\\\.\\pipe\\ToSrvPipe'
        read_file_name = '\\\\.\\pipe\\FromSrvPipe'
        EOL = '\r\n\0'
    else:
        print("pipe-test.py, running on linux or mac")
        write_file_name = '/tmp/audacity_script_pipe.to.' + str(os.getuid())
        read_file_name = '/tmp/audacity_script_pipe.from.' + str(os.getuid())
        EOL = '\n'

    print("Write to  \"" + write_file_name +"\"")
    if not os.path.exists(write_file_name):
        print(" ..does not exist.  Ensure Audacity is running with mod-script-pipe.")
        sys.exit()

    print("Read from \"" + read_file_name +"\"")
    if not os.path.exists(read_file_name):
        print(" ..does not exist.  Ensure Audacity is running with mod-script-pipe.")
        sys.exit()

    print("-- Both pipes exist.  Good.")

    WRITE_FILE = open(write_file_name, 'w')
    print("-- File to write to has been opened")
    READ_FILE = open(read_file_name, 'rt')
    print("-- File to read from has now been opened too\r\n")    


    print("Send: >>> \n"+command)
    WRITE_FILE.write(command + EOL)
    WRITE_FILE.flush()

    response = ''
    line = ''
    while True:
        response += line
        line = READ_FILE.readline()
        if line == '\n' and len(response) > 0:
            break
    print("Rcvd: <<< \n" + response)


    WRITE_FILE.close()
    READ_FILE.close()    
    return response

def quick_test():

    do_command('Help: Command=Help')
    do_command('Help: Command="GetInfo"')
    #do_command('SetPreference: Name=GUI/Theme Value=classic Reload=1')


quick_test()
