from __future__ import division, print_function
import pytest
import pyaudacity as pa

from pathlib import Path


def test_open():
    # Testing basic usage with Path:
    pa.new()
    pa.open(Path(__file__).parent / 'brown_noise.aup3')
    pa.close()

    # Testing basic usage with string:
    pa.new()
    pa.open(str(Path(__file__).parent / 'brown_noise.aup3'))
    pa.close()

    # Testing basic usage with add_to_history=True:
    pa.new()
    pa.open(Path(__file__).parent / 'brown_noise.aup3')
    pa.close()

    # Testing basic usage with add_to_history=False:
    pa.new()
    pa.open(Path(__file__).parent / 'brown_noise.aup3')
    pa.close()


    # Test missing file:
    with pytest.raises(pa.PyAudacityException):
        pa.new()
        pa.open(Path(__file__).parent / 'DOES_NOT_EXIST.aup3')
    pa.close()

    # Test bad filename arg:
    with pytest.raises(pa.PyAudacityException):
        pa.new()
        pa.open(12345)
    pa.close()

    # Test bad add_to_history arg:
    with pytest.raises(pa.PyAudacityException):
        pa.new()
        pa.open(Path(__file__).parent / 'brown_noise.aup3', 'INVALID')
    pa.close()


"""
def __test_chirp():
    pa.new()
    pa.new_mono_track()
    pa.select_tracks()


    pa.chirp()

    # Save to prevent a pop-up dialog when closing:
    #pa.save(Path(__file__).parent / 'deleteme.aup3')
    #pa.close()
"""

if __name__ == "__main__":
    pytest.main()
