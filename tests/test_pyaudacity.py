from __future__ import division, print_function
import pytest
import pyaudacity as pa

from pathlib import Path

def test_basic():
    pass  # TODO - add unit tests


def __test_chirp():
    pa.new()
    pa.new_mono_track()
    pa.select_tracks()


    pa.chirp()

    # Save to prevent a pop-up dialog when closing:
    #pa.save(Path(__file__).parent / 'deleteme.aup3')
    #pa.close()

if __name__ == "__main__":
    pytest.main()
