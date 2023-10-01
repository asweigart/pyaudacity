"""PyAudacity
By Al Sweigart al@inventwithpython.com

A Python module to control a running instance of Audacity through its macro system."""

# TODO - Bring up to the Audacity team that there's no way for the macros to just move the cursor to a timestamp in the project because there's no menu item for this. But there's literally no way to start a new project and create, like, a 1-second silence.

# TODO - Go through and create enums for the enum parameters to help people working with type-aware IDEs.

# TODO - Go through and check the online Audacity documentation for incorrect default
# values compared to the default values that appear in the various dialog boxes.

# TODO - Need to go through the docstrings and write up my own description (and explain the parameters and units), as well as add a link to the extended online docs.

"""
NOTE: PyAudacity has a general practice of using names and values from the
user interface rather than the Audacity macro documentation.

For example, for the LabelSounds macro, instead of the macro parameter names
we use their UI names:
    threshold_db    -> threshold_level
    measurement     -> threshold_measurement
    sil-dur         -> min_silence_duration
    snd-dur         -> min_label_interval
    type            -> label_type
    pre-offset      -> max_leading_silence
    post-offset     -> max_trailing_silence
    text            -> label_text

The same goes for values. For LabelSounds' threshold_measurement argument, we
take these values:
    'peak'  -> 'Peak level'
    'avg'   -> 'Average level'
    'rms'   -> 'RMS level'

(Enums are also provided for these values.)

The reasoning behind this is that the Audacity macros have very programmer-y
names instead of descriptive ones. Most likely the user of PyAudacity is going
to use positional arguments. But if they do use keyword arguments, the code
might as well be descriptive because code is read more often than it is
written.

The point of PyAudacity is to be easier to use than the dev just writing
to Audacity's named pipes themselves, so we might as well lean into that
direction all the way.

The names are based on the user interface as they appear in Audacity 3.2.5.
"""


__version__ = "0.1.2"

import os
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Optional, Union

# PyAudacity has functions called open() and print(), so save the originals:
_open = open
_type = type
_format = format
_print = print


class PyAudacityException(Exception):
    """The base exception class for PyAudacity-related exceptions."""

    pass


# Taking out the interactive warning stuff, since almost everything requires interaction.
# ("Interaction" meaning macros that could cause pop up dialogs that interrupt automation.)
# NON_INTERACTIVE_MODE = True  # type: bool
#
# def _requireInteraction():  # type: () -> None
#    if NON_INTERACTIVE_MODE:
#        raise RequiresInteractionException()
#
# class RequiresInteractionException(PyAudacityException):
#    """Raised when a macro that requires human user interaction (such as
#    selecting a file in the Open File dialog) was attempted while
#    NON_INTERACTIVE_MODE was set to True."""
#
#    pass


def do(command):  # type: (str) -> str
    if sys.platform == "win32":
        write_pipe_name = "\\\\.\\pipe\\ToSrvPipe"
        read_pipe_name = "\\\\.\\pipe\\FromSrvPipe"
        eol = "\r\n\0"
    else:
        write_pipe_name = "/tmp/audacity_script_pipe.to." + str(os.getuid())
        read_pipe_name = "/tmp/audacity_script_pipe.from." + str(os.getuid())
        eol = "\n"

    if not os.path.exists(write_pipe_name):
        raise PyAudacityException(
            write_pipe_name
            + " does not exist.  Ensure Audacity is running and mod-script-pipe is set to Enabled in the Preferences window."
        )
        sys.exit()

    # For reasons unknown, we need a slight pause after checking for the existence of the read file on Windows:
    time.sleep(0.0001)

    if not os.path.exists(read_pipe_name):
        raise PyAudacityException(
            read_pipe_name
            + " does not exist.  Ensure Audacity is running and mod-script-pipe is set to Enabled in the Preferences window."
        )
        sys.exit()

    # For reasons unknown, we need a slight pause after checking for the existence of the read file on Windows:
    time.sleep(0.0001)

    write_pipe = _open(write_pipe_name, "w")
    read_pipe = _open(read_pipe_name)

    write_pipe.write(command + eol)
    write_pipe.flush()

    response = ""
    line = ""
    while True:
        response += line
        line = read_pipe.readline()
        if line == "\n" and len(response) > 0:
            break

    write_pipe.close()

    # For reasons unknown, we need a slight pause after closing the write file on Windows:
    time.sleep(0.0001)

    read_pipe.close()

    # sys.stdout.write(response + '\n')  # DEBUG
    if "BatchCommand finished: Failed!" in response:
        raise PyAudacityException(response)

    return response


def new():
    # type: () -> str
    """Creates a new empty project window, to start working on new or
    imported tracks.

    NOTE: The macros issued from pyaudacity always apply to the last Audacity
    window opened. There's no way to pick which Audacity window macros are
    applied to."""
    return do("New")


# The open() function uses the OpenProject2 macro, not the Open macro which only opens the Open dialog.
def open(filename, add_to_history=False):
    # type: (Union[str, Path], bool) -> str
    """Presents a standard dialog box where you can select either audio files, a list of files (.LOF) or an Audacity Project file to open."""

    if not isinstance(filename, (Path, str)):
        raise PyAudacityException(
            "filename argument must be a Path or str, not" + str(type(add_to_history))
        )

    if not Path(filename).exists():
        raise PyAudacityException(str(filename) + " file not found.")
    if not isinstance(add_to_history, bool):
        raise PyAudacityException(
            "add_to_history argument must be a bool, not" + str(type(add_to_history))
        )

    return do(
        'OpenProject2: Filename="{}" AddToHistory="{}"'.format(filename, add_to_history)
    )


def close():
    # type: () -> str
    """TODO

    Audacity Documentation: Closes the current project window, prompting you to save your work if you have not saved.
    """
    return do("Close")


def page_setup():
    # type: () -> str
    """TODO

    Audacity Documentation: Opens the standard Page Setup dialog box prior to printing.
    """
    return do("PageSetup")


def print():
    # type: () -> str
    """TODO

    Audacity Documentation: Prints all the waveforms in the current project window (and the contents of Label Tracks or other tracks), with the Timeline above. Everything is printed to one page.
    """
    return do("Print")


def exit():
    # type: () -> str
    """TODO

    Audacity Documentation: Closes all project windows and exits Audacity. If there are any unsaved changes to your project, Audacity will ask if you want to save them.
    """
    return do("Exit")


# The save() function uses the SaveProject2 macro, not the Save macro which only opens the Save dialog.
def save(filename, add_to_history=False, compress=False, allow_overwrite=True):
    # type: (Union[str, Path], bool, bool, bool) -> str
    """Saves the current Audacity project .AUP3 file."""

    # Audacity will display a pop-up dialog if we try to save with an existing filename.
    if allow_overwrite and Path(filename).exists():
        os.unlink(Path(filename))

    if not isinstance(add_to_history, bool):
        raise PyAudacityException(
            "add_to_history argument must be a bool, not" + str(type(add_to_history))
        )
    if not isinstance(compress, bool):
        raise PyAudacityException(
            "compress argument must be a bool, not" + str(type(compress))
        )

    return do(
        'SaveProject2: Filename="{}" AddToHistory="{}" Compress="{}"'.format(
            filename, add_to_history, compress
        )
    )


def save_as():
    # type: () -> str
    """TODO

    Audacity Documentation: Same as save(), but allows you to save a copy of an open project
    to a different name or location."""

    return do("SaveAs")


def export_mp3():
    # type: () -> str
    """TODO

    Audacity Documentation: Exports to an MP3 file."""

    return do("ExportMp3")


def export_wav():
    # type: () -> str
    """TODO

    Audacity Documentation: Exports to an WAV file."""

    return do("ExportWav")


def export_ogg():
    # type: () -> str
    """TODO

    Audacity Documentation: Exports to an OGG file."""

    return do("ExportOgg")


# The export() function uses the Export2 macro, not the Export macro which only opens the Export Audio dialog.
def export(filename, num_channels=1):
    # type: (Union[str, Path], int) -> str
    """TODO

    Audacity Documentation: Exports selected audio to a named file. This version of export has the full set of export options. However, a current limitation is that the detailed option settings are always stored to and taken from saved preferences. The net effect is that for a given format, the most recently used options for that format will be used. In the current implementation, NumChannels should be 1 (mono) or 2 (stereo).
    """

    if not os.path.exists(filename):
        raise PyAudacityException(str(filename) + " file not found.")
    if not isinstance(num_channels, int):
        raise PyAudacityException(
            "num_channels argument must be a int, not" + str(type(num_channels))
        )

    return do('Export2: Filename="{}" NumChannels="{}"'.format(filename, num_channels))


def export_sel():
    # type: () -> str
    """TODO

    Audacity Documentation: Opens the Export Audio dialog to export the selected audio.
    """

    return do("ExportSel")


def export_labels():
    # type: () -> str
    """TODO

    Audacity Documentation: Opens the Exports Labels dialog."""

    return do("ExportLabels")


def export_multiple():
    # type: () -> str
    """TODO

    Audacity Documentation: Opens the Exports Multiple dialog."""

    return do("ExportMultiple")


def export_midi():
    # type: () -> str
    """TODO

    Audacity Documentation: Opens the Export MIDI As dialog."""

    return do("ExportMIDI")


# The import_audio() function uses the Import2 macro, not the ImportAudio macro which only opens the Import Audio dialog.
def import_audio(filename):
    # type: (Union[str, Path]) -> str
    """TODO

    Audacity Documentation: Imports from a file. The automation command uses a text box to get the file name rather than a normal file-open dialog.

    Note that this function is named import_audio() because import is a Python keyword.
    """

    if not os.path.exists(filename):
        raise PyAudacityException(str(filename) + " file not found.")

    return do("ImportAudio")


def import_labels():
    # type: () -> str
    """TODO

    Audacity Documentation: Open the Import Labels dialog."""

    return do("ImportLabels")


def import_midi():
    # type: () -> str
    """TODO

    Audacity Documentation: Opens the Import MIDI dialog."""

    return do("ImportMIDI")


def import_raw():
    # type: () -> str
    """TODO

    Audacity Documentation: Opens the Import Raw dialog."""

    return do("ImportRaw")


def undo():
    # type: () -> str
    """TODO

    Audacity Documentation: Undoes the most recent editing action."""

    return do("Undo")


def redo():
    # type: () -> str
    """TODO

    Audacity Documentation: Redoes the most recently undone editing action."""

    return do("Redo")


def cut():
    # type: () -> str
    """TODO

    Audacity Documentation: Removes the selected audio data and/or labels and places these on the Audacity clipboard. By default, any audio or labels to right of the selection are shifted to the left.
    """

    return do("Cut")


def delete():
    # type: () -> str
    """TODO

    Audacity Documentation: Removes the selected audio data and/or labels without copying these to the Audacity clipboard. By default, any audio or labels to right of the selection are shifted to the left.
    """
    return do("Delete")


def copy():
    # type: () -> str
    """TODO

    Audacity Documentation: Copies the selected audio data to the Audacity clipboard without removing it from the project.
    """
    return do("Copy")


def paste():
    # type: () -> str
    """TODO

    Audacity Documentation: Inserts whatever is on the Audacity clipboard at the position of the selection cursor in the project, replacing whatever audio data is currently selected, if any.
    """
    return do("Paste")


def duplicate():
    # type: () -> str
    """TODO

    Audacity Documentation: Creates a new track containing only the current selection as a new clip.
    """
    return do("Duplicate")


def edit_meta_data():
    # type: () -> str
    """TODO

    Audacity Documentation: Open the Edit Metadata Tags dialog."""
    return do("EditMetaData")


def preferences():
    # type: () -> str
    """TODO

    Audacity Documentation: Open the Preferences dialog."""
    return do("Preferences")


def split_cut():
    # type: () -> str
    """TODO

    Audacity Documentation: Same as Cut, but none of the audio data or labels to right of the selection are shifted.
    """
    return do("SplitCut")


def split_delete():
    # type: () -> str
    """TODO

    Audacity Documentation: Same as Delete, but none of the audio data or labels to right of the selection are shifted.
    """
    return do("SplitDelete")


def silence():
    # type: () -> str
    """TODO

    Audacity Documentation: Replaces the currently selected audio with absolute silence. Does not affect label tracks.
    """
    return do("Silence")


def trim():
    # type: () -> str
    """TODO

    Audacity Documentation: Deletes all audio but the selection. If there are other separate clips in the same track these are not removed or shifted unless trimming the entire length of a clip or clips. Does not affect label tracks.
    """
    return do("Trim")


def split():
    # type: () -> str
    """TODO

    Audacity Documentation: Splits the current clip into two clips at the cursor point, or into three clips at the selection boundaries.
    """
    return do("Split")


def split_new():
    # type: () -> str
    """TODO

    Audacity Documentation: Does a Split Cut on the current selection in the current track, then creates a new track and pastes the selection into the new track.
    """
    return do("SplitNew")


def join():
    # type: () -> str
    """TODO

    Audacity Documentation: If you select an area that overlaps one or more clips, they are all joined into one large clip. Regions in-between clips become silence.
    """
    return do("Join")


def disjoin():
    # type: () -> str
    """TODO

    Audacity Documentation: In a selection region that includes absolute silences, creates individual non-silent clips between the regions of silence. The silence becomes blank space between the clips.
    """
    return do("Disjoin")


def edit_labels():
    # type: () -> str
    """TODO

    Audacity Documentation: Open the Edit Labels dialog."""
    return do("EditLabels")


def add_label():
    # type: () -> str
    """TODO

    Audacity Documentation: Creates a new, empty label at the cursor or at the selection region.
    """
    return do("AddLabel")


def add_label_playing():
    # type: () -> str
    """TODO

    Audacity Documentation: Creates a new, empty label at the current playback or recording position.
    """
    return do("AddLabelPlaying")


def paste_new_label():
    # type: () -> str
    """TODO

    Audacity Documentation: Pastes the text on the Audacity clipboard at the cursor position in the currently selected label track. If there is no selection in the label track a point label is created. If a region is selected in the label track a region label is created. If no label track is selected one is created, and a new label is created.
    """
    return do("PasteNewLabel")


def type_to_create_label():
    # type: () -> str
    """TODO

    Audacity Documentation: Creates a new label and allows the user to type to fill it out.
    """
    return do("TypeToCreateLabel")


def cut_labels():
    # type: () -> str
    """TODO

    Audacity Documentation: Removes the selected labels and places these on the Audacity clipboard. By default, any audio or labels to right of the selection are shifted to the left.
    """
    return do("CutLabels")


def delete_labels():
    # type: () -> str
    """TODO

    Audacity Documentation: Removes the selected labels without copying these to the Audacity clipboard. By default, any audio or labels to right of the selection are shifted to the left.
    """
    return do("DeleteLabels")


def split_cut_labels():
    # type: () -> str
    """TODO

    Audacity Documentation: Removes the selected labels and places these on the Audacity clipboard, but none of the audio data or labels to right of the selection are shifted.
    """
    return do("SplitCutLabels")


def split_delete_labels():
    # type: () -> str
    """TODO

    Audacity Documentation: Removes the selected labels without copying these to the Audacity clipboard, but none of the audio data or labels to right of the selection are shifted.
    """
    return do("SplitDeleteLabels")


def copy_labels():
    # type: () -> str
    """TODO

    Audacity Documentation: Copies the selected labels to the Audacity clipboard without removing it from the project.
    """
    return do("CopyLabels")


def split_labels():
    # type: () -> str
    """TODO

    Audacity Documentation: Splits the current labeled audio regions into two regions at the cursor point, or into three regions at the selection boundaries.
    """
    return do("SplitLabels")


def join_labels():
    # type: () -> str
    """TODO

    Audacity Documentation: If you select an area that overlaps one or more labeled audio regions, they are all joined into one large clip.
    """
    return do("JoinLabels")


def disjoin_labels():
    # type: () -> str
    """TODO

    Audacity Documentation: Same as the Detach at Silences command, but operates on labeled audio regions.
    """
    return do("DisjoinLabels")


def select_all():
    # type: () -> str
    """TODO

    Audacity Documentation: Selects all of the audio in all of the tracks."""
    return do("SelectAll")


def select_none():
    # type: () -> str
    """TODO

    Audacity Documentation: Deselects all of the audio in all of the tracks."""
    return do("SelectNone")


def sel_cursor_stored_cursor():
    # type: () -> str
    """TODO

    Audacity Documentation: Selects from the position of the cursor to the previously stored cursor position.
    """
    return do("SelCursorStoredCursor")


def store_cursor_position():
    # type: () -> str
    """TODO

    Audacity Documentation: Stores the current cursor position for use in a later selection.
    """
    return do("StoreCursorPosition")


def zero_cross():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the edges of a selection region (or the cursor position) slightly so they are at a rising zero crossing point.
    """
    return do("ZeroCross")


def sel_all_tracks():
    # type: () -> str
    """TODO

    Audacity Documentation: Extends the current selection up and/or down into all tracks in the project.
    """
    return do("SelAllTracks")


def sel_sync_lock_tracks():
    # type: () -> str
    """TODO

    Audacity Documentation: Extends the current selection up and/or down into all sync-locked tracks in the currently selected track group.
    """
    return do("SelSyncLockTracks")


def left_at_playback_position():
    # type: () -> str
    """TODO

    Audacity Documentation: When Audacity is playing, recording or paused, sets the left boundary of a potential selection by moving the cursor to the current position of the green playback cursor (or red recording cursor). Otherwise, opens the "Set Left Selection Boundary" dialog for adjusting the time position of the left-hand selection boundary. If there is no selection, moving the time digits backwards creates a selection ending at the former cursor position, and moving the time digits forwards provides a way to move the cursor forwards to an exact point.
    """
    return do("Left at Playback Position")


def right_at_playback_position():
    # type: () -> str
    """TODO

    Audacity Documentation: When Audacity is playing, recording or paused, sets the right boundary of the selection, thus drawing the selection from the cursor position to the current position of the green playback cursor (or red recording cursor). Otherwise, opens the "Set Right Selection Boundary" dialog for adjusting the time position of the right-hand selection boundary. If there is no selection, moving the time digits forwards creates a selection starting at the former cursor position, and moving the time digits backwards provides a way to move the cursor backwards to an exact point.
    """
    return do("Right at Playback Position")


def sel_track_start_to_cursor():
    # type: () -> str
    """TODO

    Audacity Documentation: Selects a region in the selected track(s) from the start of the track to the cursor position.
    """
    return do("SelTrackStartToCursor")


def sel_cursor_to_track_end():
    # type: () -> str
    """TODO

    Audacity Documentation: Selects a region in the selected track(s) from the cursor position to the end of the track.
    """
    return do("SelCursorToTrackEnd")


def sel_track_start_to_end():
    # type: () -> str
    """TODO

    Audacity Documentation: Selects a region in the selected track(s) from the start of the track to the end of the track.
    """
    return do("SelTrackStartToEnd")


def sel_save():
    # type: () -> str
    """TODO

    Audacity Documentation: Stores the end points of a selection for later reuse."""
    return do("SelSave")


def sel_restore():
    # type: () -> str
    """TODO

    Audacity Documentation: Retrieves the end points of a previously stored selection.
    """
    return do("SelRestore")


def toggle_spectral_selection():
    # type: () -> str
    """TODO

    Audacity Documentation: Changes between selecting a time range and selecting the last selected spectral selection in that time range. This command toggles the spectral selection even if not in Spectrogram view, but you must be in Spectrogram view to use the spectral selection in one of the Spectral edit effects.
    """
    return do("ToggleSpectralSelection")


def next_higher_peak_frequency():
    # type: () -> str
    """TODO

    Audacity Documentation: When in Spectrogram view, snaps the center frequency to the next higher frequency peak, moving the spectral selection upwards.
    """
    return do("NextHigherPeakFrequency")


def next_lower_peak_frequency():
    # type: () -> str
    """TODO

    Audacity Documentation: When in Spectrogram views snaps the center frequency to the next lower frequency peak, moving the spectral selection downwards.
    """
    return do("NextLowerPeakFrequency")


def sel_prev_clip_boundary_to_cursor():
    # type: () -> str
    """TODO

    Audacity Documentation: Selects from the current cursor position back to the right-hand edge of the previous clip.
    """
    return do("SelPrevClipBoundaryToCursor")


def sel_cursor_to_next_clip_boundary():
    # type: () -> str
    """TODO

    Audacity Documentation: Selects from the current cursor position forward to the left-hand edge of the next clip.
    """
    return do("SelCursorToNextClipBoundary")


def sel_prev_clip():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the selection to the previous clip."""
    return do("SelPrevClip")


def sel_next_clip():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the selection to the next clip."""
    return do("SelNextClip")


def undo_history():
    # type: () -> str
    """TODO

    Audacity Documentation: Brings up the History window which can then be left open while using Audacity normally. History lists all undoable actions performed in the current project, including importing.
    """
    return do("UndoHistory")


def karaoke():
    # type: () -> str
    """TODO

    Audacity Documentation: Brings up the Karaoke window, which displays the labels in a "bouncing ball" scrolling display.
    """
    return do("Karaoke")


def mixer_board():
    # type: () -> str
    """TODO

    Audacity Documentation: Mixer Board is an alternative view to the audio tracks in the main tracks window. Analogous to a hardware mixer board, each audio track is displayed in a Track Strip.
    """
    return do("MixerBoard")


def show_extra_menus():
    # type: () -> str
    """TODO

    Audacity Documentation: Shows extra menus with many extra less-used commands."""
    return do("ShowExtraMenus")


def show_clipping():
    # type: () -> str
    """TODO

    Audacity Documentation: Option to show or not show audio that is too loud (in red) on the wave form.
    """
    return do("ShowClipping")


def zoom_in():
    # type: () -> str
    """TODO

    Audacity Documentation: Zooms in on the horizontal axis of the audio displaying more detail over a shorter length of time.
    """
    return do("ZoomIn")


def zoom_normal():
    # type: () -> str
    """TODO

    Audacity Documentation: Zooms to the default view which displays about one inch per second.
    """
    return do("ZoomNormal")


def zoom_out():
    # type: () -> str
    """TODO

    Audacity Documentation: Zooms out displaying less detail over a greater length of time.
    """
    return do("ZoomOut")


def zoom_sel():
    # type: () -> str
    """TODO

    Audacity Documentation: Zooms in or out so that the selected audio fills the width of the window.
    """
    return do("ZoomSel")


def zoom_toggle():
    # type: () -> str
    """TODO

    Audacity Documentation: Changes the zoom back and forth between two preset levels.
    """
    return do("ZoomToggle")


def advanced_v_zoom():
    # type: () -> str
    """TODO

    Audacity Documentation: Enable for left-click gestures in the vertical scale to control zooming.
    """
    return do("AdvancedVZoom")


def fit_in_window():
    # type: () -> str
    """TODO

    Audacity Documentation: Zooms out until the entire project just fits in the window.
    """
    return do("FitInWindow")


def fit_v():
    # type: () -> str
    """TODO

    Audacity Documentation: Adjusts the height of all the tracks until they fit in the project window.
    """
    return do("FitV")


def collapse_all_tracks():
    # type: () -> str
    """TODO

    Audacity Documentation: Collapses all tracks to take up the minimum amount of space.
    """
    return do("CollapseAllTracks")


def expand_all_tracks():
    # type: () -> str
    """TODO

    Audacity Documentation: Expands all collapsed tracks to their original size before the last collapse.
    """
    return do("ExpandAllTracks")


def skip_sel_start():
    # type: () -> str
    """TODO

    Audacity Documentation: When there is a selection, moves the cursor to the start of the selection and removes the selection.
    """
    return do("SkipSelStart")


def skip_sel_end():
    # type: () -> str
    """TODO

    Audacity Documentation: When there is a selection, moves the cursor to the end of the selection and removes the selection.
    """
    return do("SkipSelEnd")


def reset_toolbars():
    # type: () -> str
    """TODO

    Audacity Documentation: Using this command positions all toolbars in default location and size as they were when Audacity was first installed.
    """
    return do("ResetToolbars")


def show_transport_t_b():
    # type: () -> str
    """TODO

    Audacity Documentation: Controls playback and recording and skips to start or end of project when neither playing or recording.
    """
    return do("ShowTransportTB")


def show_tools_t_b():
    # type: () -> str
    """TODO

    Audacity Documentation: Chooses various tools for selection, volume adjustment, zooming and time-shifting of audio.
    """
    return do("ShowToolsTB")


def show_record_meter_t_b():
    # type: () -> str
    """TODO

    Audacity Documentation: Displays recording levels and toggles input monitoring when not recording.
    """
    return do("ShowRecordMeterTB")


def show_play_meter_t_b():
    # type: () -> str
    """TODO

    Audacity Documentation: Displays playback levels."""
    return do("ShowPlayMeterTB")


def show_mixer_t_b():
    # type: () -> str
    """TODO

    Audacity Documentation: Adjusts the recording and playback volumes of the devices currently selected in Device Toolbar.
    """
    return do("ShowMixerTB")


def show_edit_t_b():
    # type: () -> str
    """TODO

    Audacity Documentation: Cut, copy, paste, trim audio, silence audio, undo, redo, zoom tools.
    """
    return do("ShowEditTB")


def show_transcription_t_b():
    # type: () -> str
    """TODO

    Audacity Documentation: Plays audio at a slower or faster speed than normal, affecting pitch.
    """
    return do("ShowTranscriptionTB")


def show_scrubbing_t_b():
    # type: () -> str
    """TODO

    Audacity Documentation: Controls playback and recording and skips to start or end of project when neither playing or recording.
    """
    return do("ShowScrubbingTB")


def show_device_t_b():
    # type: () -> str
    """TODO

    Audacity Documentation: Selects audio host, recording device, number of recording channels and playback device.
    """
    return do("ShowDeviceTB")


def show_selection_t_b():
    # type: () -> str
    """TODO

    Audacity Documentation: Controls the sample rate of the project, snapping to the selection format and adjusts cursor and region position by keyboard input.
    """
    return do("ShowSelectionTB")


def show_spectral_selection_t_b():
    # type: () -> str
    """TODO

    Audacity Documentation: Displays and lets you adjust the current spectral (frequency) selection without having to be in Spectrogram view.
    """
    return do("ShowSpectralSelectionTB")


def rescan_devices():
    # type: () -> str
    """TODO

    Audacity Documentation: Rescan for audio devices connected to your computer, and update the playback and recording dropdown menus in Device Toolbar.
    """
    return do("RescanDevices")


def play_stop():
    # type: () -> str
    """TODO

    Audacity Documentation: Starts and stops playback or stops a recording (stopping does not change the restart position). Therefore using any play or record command after stopping with "Play/Stop" will start playback or recording from the same Timeline position it last started from. You can also assign separate shortcuts for Play and Stop.
    """
    return do("PlayStop")


def play_stop_select():
    # type: () -> str
    """TODO

    Audacity Documentation: Starts playback like "Play/Stop", but stopping playback sets the restart position to the stop point. When stopped, this command is the same as "Play/Stop". When playing, this command stops playback and moves the cursor (or the start of the selection) to the position where playback stopped.
    """
    return do("PlayStopSelect")


def pause():
    # type: () -> str
    """TODO

    Audacity Documentation: Temporarily pauses playing or recording without losing your place.
    """
    return do("Pause")


def record1st_choice():
    # type: () -> str
    """TODO

    Audacity Documentation: Starts recording at the end of the currently selected track(s).
    """
    return do("Record1stChoice")


def record2nd_choice():
    # type: () -> str
    """TODO

    Audacity Documentation: Recording begins on a new track at either the current cursor location or at the beginning of the current selection.
    """
    return do("Record2ndChoice")


def timer_record():
    # type: () -> str
    """TODO

    Audacity Documentation: Brings up the Timer Record dialog."""
    return do("TimerRecord")


def punch_and_roll():
    # type: () -> str
    """TODO

    Audacity Documentation: Re-record over audio, with a pre-roll of audio that comes before.
    """
    return do("PunchAndRoll")


def scrub():
    # type: () -> str
    """TODO

    Audacity Documentation: Scrubbing is the action of moving the mouse pointer right or left so as to adjust the position, speed or direction of playback, listening to the audio at the same time.
    """
    return do("Scrub")


def seek():
    # type: () -> str
    """TODO

    Audacity Documentation: Seeking is similar to Scrubbing except that it is playback with skips, similar to using the seek button on a CD player.
    """
    return do("Seek")


def toggle_scrub_ruler():
    # type: () -> str
    """TODO

    Audacity Documentation: Shows (or hides) the scrub ruler, which is just below the timeline.
    """
    return do("ToggleScrubRuler")


def curs_sel_start():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the left edge of the current selection to the center of the screen, without changing the zoom level.
    """
    return do("CursSelStart")


def curs_sel_end():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the right edge of the current selection to the center of the screen, without changing the zoom level.
    """
    return do("CursSelEnd")


def curs_track_start():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the cursor to the start of the selected track."""
    return do("CursTrackStart")


def curs_track_end():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the cursor to the end of the selected track."""
    return do("CursTrackEnd")


def curs_prev_clip_boundary():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the cursor position back to the right-hand edge of the previous clip.
    """
    return do("CursPrevClipBoundary")


def curs_next_clip_boundary():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the cursor position forward to the left-hand edge of the next clip.
    """
    return do("CursNextClipBoundary")


def curs_project_start():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the cursor to the beginning of the project."""
    return do("CursProjectStart")


def curs_project_end():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the cursor to the end of the project."""
    return do("CursProjectEnd")


def sound_activation_level():
    # type: () -> str
    """TODO

    Audacity Documentation: Sets the activation level above which Sound Activated Recording will record.
    """
    return do("SoundActivationLevel")


def sound_activation():
    # type: () -> str
    """TODO

    Audacity Documentation: Toggles on and off the Sound Activated Recording option."""
    return do("SoundActivation")


def pinned_head():
    # type: () -> str
    """TODO

    Audacity Documentation: You can change Audacity to play and record with a fixed head pinned to the Timeline. You can adjust the position of the fixed head by dragging it.
    """
    return do("PinnedHead")


def overdub():
    # type: () -> str
    """TODO

    Audacity Documentation: Toggles on and off the Overdub option."""
    return do("Overdub")


def s_w_playthrough():
    # type: () -> str
    """TODO

    Audacity Documentation: Toggles on and off the Software Playthrough option."""
    return do("SWPlaythrough")


def resample():
    # type: () -> str
    """TODO

    Audacity Documentation: Allows you to resample the selected track(s) to a new sample rate for use in the project.
    """
    return do("Resample")


def remove_tracks():
    # type: () -> str
    """TODO

    Audacity Documentation: Removes the selected track(s) from the project. Even if only part of a track is selected, the entire track is removed.
    """
    return do("RemoveTracks")


def sync_lock():
    # type: () -> str
    """TODO

    Audacity Documentation: Ensures that length changes occurring anywhere in a defined group of tracks also take place in all audio or label tracks in that group.
    """
    return do("SyncLock")


def new_mono_track():
    # type: () -> str
    """TODO

    Audacity Documentation: Creates a new empty mono audio track."""
    return do("NewMonoTrack")


def new_stereo_track():
    # type: () -> str
    """TODO

    Audacity Documentation: Adds an empty stereo track to the project."""
    return do("NewStereoTrack")


def new_label_track():
    # type: () -> str
    """TODO

    Audacity Documentation: Adds an empty label track to the project."""
    return do("NewLabelTrack")


def new_time_track():
    # type: () -> str
    """TODO

    Audacity Documentation: Adds an empty time track to the project. Time tracks are used to speed up and slow down audio.
    """
    return do("NewTimeTrack")


def stereo_to_mono():
    # type: () -> str
    """TODO

    Audacity Documentation: Converts the selected stereo track(s) into the same number of mono tracks, combining left and right channels equally by averaging the volume of both channels.
    """
    return do("Stereo to Mono")


def mix_and_render():
    # type: () -> str
    """TODO

    Audacity Documentation: Mixes down all selected tracks to a single mono or stereo track, rendering to the waveform all real-time transformations that had been applied (such as track gain, panning, amplitude envelopes or a change in project rate).
    """
    return do("MixAndRender")


def mix_and_render_to_new_track():
    # type: () -> str
    """TODO

    Audacity Documentation: Same as Tracks > Mix and Render except that the original tracks are preserved rather than being replaced by the resulting "Mix" track.
    """
    return do("MixAndRenderToNewTrack")


def mute_all_tracks():
    # type: () -> str
    """TODO

    Audacity Documentation: Mutes all the audio tracks in the project as if you had used the mute buttons from the Track Control Panel on each track.
    """
    return do("MuteAllTracks")


def unmute_all_tracks():
    # type: () -> str
    """TODO

    Audacity Documentation: Unmutes all the audio tracks in the project as if you had released the mute buttons from the Track Control Panel on each track.
    """
    return do("UnmuteAllTracks")


def mute_tracks():
    # type: () -> str
    """TODO

    Audacity Documentation: Mutes the selected tracks."""
    return do("MuteTracks")


def unmute_tracks():
    # type: () -> str
    """TODO

    Audacity Documentation: Unmutes the selected tracks."""
    return do("UnmuteTracks")


def pan_left():
    # type: () -> str
    """TODO

    Audacity Documentation: Pan selected audio to left speaker."""
    return do("PanLeft")


def pan_right():
    # type: () -> str
    """TODO

    Audacity Documentation: Pan selected audio centrally."""
    return do("PanRight")


def pan_center():
    # type: () -> str
    """TODO

    Audacity Documentation: Pan selected audio to right speaker."""
    return do("PanCenter")


def align__end_to_end():
    # type: () -> str
    """TODO

    Audacity Documentation: Aligns the selected tracks one after the other, based on their top-to-bottom order in the project window.
    """
    return do("Align_EndToEnd")


def align__together():
    # type: () -> str
    """TODO

    Audacity Documentation: Align the selected tracks so that they start at the same (averaged) start time.
    """
    return do("Align_Together")


def align__start_to_zero():
    # type: () -> str
    """TODO

    Audacity Documentation: Aligns the start of selected tracks with the start of the project.
    """
    return do("Align_StartToZero")


def align__start_to_sel_start():
    # type: () -> str
    """TODO

    Audacity Documentation: Aligns the start of selected tracks with the current cursor position or with the start of the current selection.
    """
    return do("Align_StartToSelStart")


def align__start_to_sel_end():
    # type: () -> str
    """TODO

    Audacity Documentation: Aligns the start of selected tracks with the end of the current selection.
    """
    return do("Align_StartToSelEnd")


def align__end_to_sel_start():
    # type: () -> str
    """TODO

    Audacity Documentation: Aligns the end of selected tracks with the current cursor position or with the start of the current selection.
    """
    return do("Align_EndToSelStart")


def align__end_to_sel_end():
    # type: () -> str
    """TODO

    Audacity Documentation: Aligns the end of selected tracks with the end of the current selection.
    """
    return do("Align_EndToSelEnd")


def move_selection_with_tracks():
    # type: () -> str
    """TODO

    Audacity Documentation: Toggles on/off the selection moving with the realigned tracks, or staying put.
    """
    return do("MoveSelectionWithTracks")


def sort_by_time():
    # type: () -> str
    """TODO

    Audacity Documentation: Sort tracks in order of start time."""
    return do("SortByTime")


def sort_by_name():
    # type: () -> str
    """TODO

    Audacity Documentation: Sort tracks in order by name."""
    return do("SortByName")


def manage_generators():
    # type: () -> str
    """TODO

    Audacity Documentation: Selecting this option from the Effect Menu (or the Generate Menu or Analyze Menu) takes you to a dialog where you can enable or disable particular Effects, Generators and Analyzers in Audacity. Even if you do not add any third-party plugins, you can use this to make the Effect menu shorter or longer as required. For details see Plugin Manager.
    """
    return do("ManageGenerators")


def built_in():
    # type: () -> str
    """TODO

    Audacity Documentation: Shows the list of available Audacity built-in effects but only if the user has effects "Grouped by Type" in Effects Preferences.
    """
    return do("Built-in")


def nyquist():
    # type: () -> str
    """TODO

    Audacity Documentation: Shows the list of available Nyquist effects but only if the user has effects "Grouped by Type" in Effects Preferences.
    """
    return do("Nyquist")


class ChirpWaveform(Enum):
    SINE = "Sine"
    SQUARE = "Square"
    SAWTOOTH = "Sawtooth"
    SQUARE_NO_ALIAS = "Square, no alias"
    TRIANGLE = "Triangle"  # Note: This option doesn't appear in the scripting documentation but does in the UI.


class ChirpInterpolation(Enum):
    LINEAR = "Linear"
    LOGARITHMIC = "Logarithmic"


def chirp(
    start_frequency=440,
    end_frequency=1320,
    start_amplitude=0.8,
    end_amplitude=0.1,
    waveform="Sine",
    interpolation="Linear",
):
    # type: (float, float, float, float, Union[ChirpWaveform, str], Union[ChirpInterpolation, str]) -> str
    """TODO

    Audacity Documentation: Generates four different types of tone waveforms like the Tone Generator, but additionally allows setting of the starting and ending amplitude and frequency.
    """

    # Convert enums to strings:
    if isinstance(waveform, ChirpWaveform):
        waveform = waveform.value
    if isinstance(interpolation, ChirpInterpolation):
        interpolation = interpolation.value

    # Argument type checks:
    if not isinstance(start_frequency, (float, int)):
        raise PyAudacityException(
            "start_frequency argument must be float or int, not "
            + str(type(start_frequency))
        )
    if not isinstance(end_frequency, (float, int)):
        raise PyAudacityException(
            "end_frequency argument must be float or int, not "
            + str(type(end_frequency))
        )
    if not isinstance(start_amplitude, (float, int)):
        raise PyAudacityException(
            "start_amplitude argument must be float or int, not "
            + str(type(start_amplitude))
        )
    if not isinstance(end_amplitude, (float, int)):
        raise PyAudacityException(
            "end_amplitude argument must be float or int, not "
            + str(type(end_amplitude))
        )

    # Argument value checks:
    if waveform.lower() not in ("sine", "square", "sawtooth", "square, no alias"):
        raise PyAudacityException(
            'waveform argument must be one of "Sine", "Square", "Sawtooth", or "Square, no alias"'
        )
    if interpolation.lower() not in ("linear", "logarithmic"):
        raise PyAudacityException(
            'interpolation argument must be one of "Linear" or "Logarithmic"'
        )

    if not (0.0 <= start_amplitude <= 1.0):
        raise PyAudacityException(
            "start_amplitude argument must be between 0.0 and 1.0"
        )
    if not (0.0 <= end_amplitude <= 1.0):
        raise PyAudacityException("end_amplitude argument must be between 0.0 and 1.0")
    if start_frequency < 0:
        raise PyAudacityException("start_frequency must be positive")
    if end_frequency < 0:
        raise PyAudacityException("end_frequency must be positive")

    # Convert str args to their expected case:
    waveform = waveform[0].upper() + waveform[1:].lower()
    interpolation = interpolation.title()

    # Run macro:
    return do(
        'Chirp: StartFreq="{}" EndFreq="{}" StartAmp="{}" EndAmp="{}" Waveform="{}" Interpolation="{}"'.format(
            start_frequency,
            end_frequency,
            start_amplitude,
            end_amplitude,
            waveform,
            interpolation,
        )
    )


def dtmf_tones(DTMF_sequence="audacity", duty_cycle=55, amplitude=0.8):
    # type: (str, float, float) -> str
    """This macro is broken. The UI specifies Tone/Silence Ratio instead of Duty Cycle,
    but the macro can't seem to set this. Passing any value for Duty Cycle doesn't have
    any effect."""

    raise NotImplementedError

    # Old code:

    """TODO

    Audacity Documentation: Generates dual-tone multi-frequency (DTMF) tones like those produced by the keypad on telephones.
    """

    if not isinstance(DTMF_sequence, str):
        raise PyAudacityException(
            "DTMF_sequence argument must be a str, not " + str(type(DTMF_sequence))
        )
    if not isinstance(duty_cycle, (float, int)):
        raise PyAudacityException(
            "duty_cycle argument must be float or int, not " + str(type(duty_cycle))
        )
    if not isinstance(amplitude, (float, int)):
        raise PyAudacityException(
            "amplitude argument must be float or int, not " + str(type(amplitude))
        )

    return do(
        'DtmfTones: Sequence="{}" DutyCycle="{}" Amplitude="{}"'.format(
            DTMF_sequence, duty_cycle, amplitude
        )
    )


class NoiseType(Enum):
    WHITE = "White"
    PINK = "Pink"
    BROWNIAN = "Brownian"


def noise(noise_type="White", amplitude=0.8):
    # type: (Union[NoiseType, str], float) -> str
    """Fills the selected area with noise.

    Audacity Documentation: Generates 'white', 'pink' or 'brown' noise."""

    # Convert enums to strings:
    if isinstance(noise_type, NoiseType):
        noise_type = noise_type.value
    noise_type = noise_type.title()

    if noise_type not in ("White", "Pink", "Brownian"):
        raise PyAudacityException(
            'type argument must be one of "White", "Pink" or "Brownian"'
        )
    if not isinstance(amplitude, (float, int)):
        raise PyAudacityException(
            "amplitude argument must be float or int, not " + str(type(amplitude))
        )

    # Argument value checks:
    if not (0.0 <= amplitude <= 1.0):
        raise PyAudacityException("amplitude argument must be between 0.0 and 1.0")

    return do('Noise: Type="{}" Amplitude="{}"'.format(noise_type, amplitude))


class ToneWaveform(Enum):
    SINE = "Sine"
    SQUARE = "Square"
    SAWTOOTH = "Sawtooth"
    SQUARE_NO_ALIAS = "Square, no alias"
    TRIANGLE = "Triangle"  # Note: This option doesn't appear in the scripting documentation but does in the UI.


def tone(frequency=440, amplitude=0.8, waveform="Sine"):
    # type: (float, float, Union[ToneWaveform, str]) -> str
    """TODO

    Audacity Documentation: Generates one of four different tone waveforms: Sine, Square, Sawtooth or Square (no alias), and a frequency between 1 Hz and half the current project rate.
    """

    # TODO - NOTE: The documentation is wrong; there doesn't seem to be an "Interpolation" parameter anymore for Tone.

    # Convert enums to strings:
    if isinstance(waveform, ToneWaveform):
        waveform = waveform.value

    if not isinstance(frequency, (float, int)):
        raise PyAudacityException(
            "frequency argument must be float or int, not " + str(type(frequency))
        )
    if not isinstance(amplitude, (float, int)):
        raise PyAudacityException(
            "amplitude argument must be float or int, not " + str(type(amplitude))
        )
    if waveform.lower() not in ("sine", "square", "sawtooth", "square, no alias"):
        raise PyAudacityException(
            'waveform argument must be one of "Sine", "Square", "Sawtooth", or "Square, no alias"'
        )

    waveform = waveform[0].upper() + waveform[1:].lower()

    return do(
        'Tone: Frequency="{}" Amplitude="{}" Waveform="{}"'.format(
            frequency, amplitude, waveform
        )
    )


class PluckFade(Enum):
    ABRUPT = "Abrupt"
    GRADUAL = "Gradual"


def pluck(pitch=60, fade="Abrupt", duration=1.0):
    # type: (int, Union[PluckFade, str], float) -> str
    """TODO

    Audacity Documentation: A synthesized pluck tone with abrupt or gradual fade-out, and selectable pitch corresponding to a MIDI note.
    """

    # NOTE: A region of a track must be selected. It's not enough to just set the cursor where you want the pluck to begin. The length of the selected region is, however, ignored.

    # Convert enums to strings:
    if isinstance(fade, PluckFade):
        fade = fade.value
    fade = fade.title()

    if not isinstance(pitch, int):
        raise PyAudacityException("pitch argument must be int, not " + str(type(pitch)))
    if not isinstance(duration, (float, int)):
        raise PyAudacityException(
            "duration argument must be float or int, not " + str(type(duration))
        )
    if fade not in ("Abrupt", "Gradual"):
        raise PyAudacityException('fade argument must be one of "Abrupt" or "Gradual"')

    # The user interface says 60 seconds is the max duration.
    if duration > 60:
        raise PyAudacityException(
            "duration is larger than the 60 seconds maximum allowed limit"
        )

    # Note: The parameter names are lowercase in the documentation so I'm making them lowercase here.
    # https://manual.audacityteam.org/man/scripting_reference.html
    return do('Pluck: pitch="{}" fade="{}" dur="{}"'.format(pitch, fade, duration))


class RhythmTrackBeatSound(Enum):
    METRONOME_TICK = "Metronome Tick"
    PING_SHORT = "Ping (short)"
    PING_LONG = "Ping (long)"
    COWBELL = "Cowbell"
    RESONANT_NOISE = "Resonant Noise"
    NOISE_CLICK = "Noise Click"
    DRIP_SHORT = "Drip (short)"
    DRIP_LONG = "Drip (long)"


def rhythm_track(
    tempo=120.0,
    beats_per_bar=4,
    swing=0.0,
    number_of_bars=16,
    rhythm_track_duration=0,
    start_time_offset=0,
    beat_sound="Metronome",
    pitch_of_strong_beat=84,
    pitch_of_weak_beat=0,
):
    # type: (float, int, float, int, float, float, Union[RhythmTrackBeatSound, str], int, int) -> str
    """TODO

    Audacity Documentation: Generates a track with regularly spaced sounds at a specified tempo and number of beats per measure (bar).
    """

    # Convert enums to strings:
    if isinstance(beat_sound, RhythmTrackBeatSound):
        beat_sound = beat_sound.value

    if not isinstance(tempo, (float, int)):
        raise PyAudacityException(
            "tempo argument must be float or int, not " + str(type(tempo))
        )
    if not isinstance(beats_per_bar, int):
        raise PyAudacityException(
            "beats_per_bar argument must be int, not " + str(type(beats_per_bar))
        )
    if not isinstance(swing, (float, int)):
        raise PyAudacityException(
            "swing argument must be float or int, not " + str(type(swing))
        )
    if not isinstance(number_of_bars, int):
        raise PyAudacityException(
            "number_of_bars argument must be int, not " + str(type(number_of_bars))
        )
    if not isinstance(rhythm_track_duration, (float, int)):
        raise PyAudacityException(
            "rhythm_track_duration argument must be float or int, not "
            + str(type(rhythm_track_duration))
        )
    if not isinstance(start_time_offset, (float, int)):
        raise PyAudacityException(
            "start_time_offset argument must be float or int, not "
            + str(type(start_time_offset))
        )
    if beat_sound.lower() not in (
        "metronome tick",
        "ping (short)",
        "ping (long)",
        "cowbell",
        "resonant noise",
        "noise click",
        "drip (short)",
        "drip (long)",
    ):
        raise PyAudacityException(
            'beat_sound argument must be one of "Abrupt" or "Gradual"'
        )
    if not isinstance(pitch_of_strong_beat, int):
        raise PyAudacityException(
            "pitch_of_strong_beat argument must be int, not "
            + str(type(pitch_of_strong_beat))
        )
    if not isinstance(pitch_of_weak_beat, int):
        raise PyAudacityException(
            "pitch_of_weak_beat argument must be int, not "
            + str(type(pitch_of_weak_beat))
        )

    beat_sound = {
        "metronome tick": "Metronome",
        "ping (short)": "Ping (short)",
        "ping (long)": "Ping (long)",
        "cowbell": "Cowbell",
        "resonant noise": "ResonantNoise",
        "noise click": "NoiseClick",
        "drip (short)": "Drip (short)",
        "drip (long)": "Drip (long)",
    }[beat_sound.lower()]

    # The documentation has the parameters as lowercase, so I do too:
    return do(
        'RhythmTrack: tempo="{}" timesig="{}" swing="{}" bars="{}" click-track-dur="{}" offset="{}" click-type="{}" high="{}" low="{}"'.format(
            tempo,
            beats_per_bar,
            swing,
            number_of_bars,
            rhythm_track_duration,
            start_time_offset,
            beat_sound,
            pitch_of_strong_beat,
            pitch_of_weak_beat,
        )
    )


def risset_drum(
    frequency=0,
    decay=0,
    center_frequency_of_noise=0,
    width_of_noise_band=0,
    noise=0,
    gain=0,
):
    # type: (float, float, float, float, float, float) -> str
    """TODO

    Audacity Documentation: Produces a realistic drum sound."""

    if not isinstance(frequency, (float, int)):
        raise PyAudacityException(
            "frequency argument must be float or int, not " + str(type(frequency))
        )
    if not isinstance(decay, (float, int)):
        raise PyAudacityException(
            "decay argument must be float or int, not " + str(type(decay))
        )
    if not isinstance(center_frequency_of_noise, (float, int)):
        raise PyAudacityException(
            "center_frequency_of_noise argument must be float or int, not "
            + str(type(center_frequency_of_noise))
        )
    if not isinstance(width_of_noise_band, (float, int)):
        raise PyAudacityException(
            "width_of_noise_band argument must be float or int, not "
            + str(type(width_of_noise_band))
        )
    if not isinstance(noise, (float, int)):
        raise PyAudacityException(
            "noise argument must be float or int, not " + str(type(noise))
        )
    if not isinstance(gain, (float, int)):
        raise PyAudacityException(
            "gain argument must be float or int, not " + str(type(gain))
        )

    # The documentation has lowercase parameters, so I do too:
    return do(
        'RissetDrum: freq="{}" decay="{}" cf="{}" bw="{}" noise="{}" gain="{}"'.format(
            frequency,
            decay,
            center_frequency_of_noise,
            width_of_noise_band,
            noise,
            gain,
        )
    )


def manage_effects():
    # type: () -> str
    """TODO

    Audacity Documentation: Selecting this option from the Effect Menu (or the Generate Menu or Analyze Menu) takes you to a dialog where you can enable or disable particular Effects, Generators and Analyzers in Audacity. Even if you do not add any third-party plugins, you can use this to make the Effect menu shorter or longer as required. For details see Plugin Manager.
    """
    return do("ManageEffects")


def repeat_last_effect():
    # type: () -> str
    """TODO

    Audacity Documentation: Repeats the last used effect at its last used settings and without displaying any dialog.
    """
    return do("RepeatLastEffect")


def ladspa():
    # type: () -> str
    """TODO

    Audacity Documentation: Shows the list of available LADSPA effects but only if the user has effects "Grouped by Type" in Effects Preferences.
    """
    return do("LADSPA")


def amplify(ratio=0.9, allow_clipping=False):
    # type: (float, bool) -> str
    """TODO

    Audacity Documentation: Increases or decreases the volume of the audio you have selected.
    """

    if not isinstance(ratio, (float, int)):
        raise PyAudacityException(
            "ratio argument must be float or int, not " + str(type(ratio))
        )
    if not isinstance(allow_clipping, bool):
        raise PyAudacityException(
            "allow_clipping argument must be a bool, not" + str(type(allow_clipping))
        )

    return do('Amplify: Ratio="{}" AllowClipping="{}"'.format(ratio, allow_clipping))


def auto_duck(
    duck_amount_db=-12,
    inner_fade_down_len=0,
    inner_fade_up_len=0,
    outer_fade_down_len=0.5,
    outer_fade_up_len=0.5,
    threshold_db=-30,
    maximum_pause=1,
):
    # type: (float, float, float, float, float, float, float) -> str
    """TODO

    Audacity Documentation: Reduces (ducks) the volume of one or more tracks whenever the volume of a specified "control" track reaches a particular level. Typically used to make a music track softer whenever speech in a commentary track is heard.
    """

    if not isinstance(duck_amount_db, (float, int)):
        raise PyAudacityException(
            "duck_amount_db argument must be float or int, not "
            + str(type(duck_amount_db))
        )
    if not isinstance(inner_fade_down_len, (float, int)):
        raise PyAudacityException(
            "inner_fade_down_len argument must be float or int, not "
            + str(type(inner_fade_down_len))
        )
    if not isinstance(inner_fade_up_len, (float, int)):
        raise PyAudacityException(
            "inner_fade_up_len argument must be float or int, not "
            + str(type(inner_fade_up_len))
        )
    if not isinstance(outer_fade_down_len, (float, int)):
        raise PyAudacityException(
            "outer_fade_down_len argument must be float or int, not "
            + str(type(outer_fade_down_len))
        )
    if not isinstance(outer_fade_up_len, (float, int)):
        raise PyAudacityException(
            "outer_fade_up_len argument must be float or int, not "
            + str(type(outer_fade_up_len))
        )
    if not isinstance(threshold_db, (float, int)):
        raise PyAudacityException(
            "threshold_db argument must be float or int, not " + str(type(threshold_db))
        )
    if not isinstance(maximum_pause, (float, int)):
        raise PyAudacityException(
            "maximum_pause argument must be float or int, not "
            + str(type(maximum_pause))
        )

    return do(
        'AutoDuck: DuckAmountDb="{}" InnerFadeDownLen="{}" InnerFadeUpLen="{}" OuterFadeDownLen="{}" OuterFadeUpLen="{}" ThresholdDb="{}" MaximumPause="{}"'.format(
            duck_amount_db,
            inner_fade_down_len,
            inner_fade_up_len,
            outer_fade_down_len,
            outer_fade_up_len,
            threshold_db,
            maximum_pause,
        )
    )


def bass_and_treble(bass=0, treble=0, gain=0, link_sliders=False):
    # type: (float, float, float, bool) -> str
    """TODO

    Audacity Documentation: Increases or decreases the lower frequencies and higher frequencies of your audio independently; behaves just like the bass and treble controls on a stereo system.
    """

    if not isinstance(bass, (float, int)):
        raise PyAudacityException(
            "bass argument must be float or int, not " + str(type(bass))
        )
    if not isinstance(treble, (float, int)):
        raise PyAudacityException(
            "treble argument must be float or int, not " + str(type(treble))
        )
    if not isinstance(gain, (float, int)):
        raise PyAudacityException(
            "gain argument must be float or int, not " + str(type(gain))
        )
    if not isinstance(link_sliders, bool):
        raise PyAudacityException(
            "link_sliders argument must be a bool, not" + str(type(link_sliders))
        )

    # TODO - The documentation shows it as "Link Sliders" but I don't know if the space is intentional or not.
    # There's no way to tell since Audacity's macro system doesn't give errors for bad parameter names.
    return do(
        'BassAndTreble: Bass="{}" Treble="{}" Gain="{}" LinkSliders="{}"'.format(
            bass, treble, gain, link_sliders
        )
    )


def change_pitch(percentage=0.0, use_high_quality_stretching=False):
    # type: (float, bool) -> str
    """TODO

    Audacity Documentation: Change the pitch of a selection without changing its tempo.
    """

    # TODO - the documentation is unclear as to what SBSMS stands for, but it's
    # a bool and the only checkbox in the Change Pitch dialog is the one marked
    # "Use high quality stretching (slow)", and SBSMS and this checkbox are
    # also found in the Change Tempo dialog.
    # I've decided to rename SBSMS to use_high_quality_stretching

    # TODO - there seem to be several fields in the Change Pitch dialog that
    # aren't captured by the parameters for this macro. What's up with that?

    if not isinstance(percentage, (float, int)):
        raise PyAudacityException(
            "percentage argument must be float or int, not " + str(type(percentage))
        )
    if not isinstance(use_high_quality_stretching, bool):
        raise PyAudacityException(
            "use_high_quality_stretching argument must be a bool, not"
            + str(type(use_high_quality_stretching))
        )

    return do(
        'ChangePitch: Percentage="{}" SBSMS="{}"'.format(
            percentage, use_high_quality_stretching
        )
    )


def change_speed(percentage=0.0):
    # type: (float) -> str
    """TODO

    Audacity Documentation: Change the speed of a selection, also changing its pitch."""

    if not isinstance(percentage, (float, int)):
        raise PyAudacityException(
            "percentage argument must be float or int, not " + str(type(percentage))
        )

    return do('ChangeSpeed: Percentage="{}"'.format(percentage))


def change_tempo(percentage=0.0, use_high_quality_stretching=False):
    # type: (float, bool) -> str
    """TODO

    Audacity Documentation: Change the tempo and length (duration) of a selection without changing its pitch.
    """

    if not isinstance(percentage, (float, int)):
        raise PyAudacityException(
            "percentage argument must be float or int, not " + str(type(percentage))
        )
    if not isinstance(use_high_quality_stretching, bool):
        raise PyAudacityException(
            "use_high_quality_stretching argument must be a bool, not"
            + str(type(use_high_quality_stretching))
        )

    return do(
        'ChangeTempo: Percentage="{}" SBSMS="{}"'.format(
            percentage, use_high_quality_stretching
        )
    )


def click_removal(threshold=200, width=20):
    # type: (int, int) -> str
    """TODO

    Audacity Documentation: Click Removal is designed to remove clicks on audio tracks and is especially suited to declicking recordings made from vinyl records.
    """

    if not isinstance(threshold, int):
        raise PyAudacityException(
            "threshold argument must be int, not " + str(type(threshold))
        )
    if not isinstance(width, int):
        raise PyAudacityException("width argument must be int, not " + str(type(width)))

    return do('ClickRemoval: Threshold="{}" Width="{}"'.format(threshold, width))


def compressor(
    threshold=-12.0,
    noise_floor=-40.0,
    ratio=2.0,
    attack_time=0.2,
    release_time=1.0,
    normalize=True,
    use_peak=False,
):
    # type: (float, float, float, float, float, bool, bool) -> str
    """TODO

    Audacity Documentation: Compresses the dynamic range by two alternative methods. The default "RMS" method makes the louder parts softer, but leaves the quieter audio alone. The alternative "peaks" method makes the entire audio louder, but amplifies the louder parts less than the quieter parts. Make-up gain can be applied to either method, making the result as loud as possible without clipping, but not changing the dynamic range further.
    """

    if not isinstance(threshold, (float, int)):
        raise PyAudacityException(
            "threshold argument must be float or int, not " + str(type(threshold))
        )
    if not isinstance(noise_floor, (float, int)):
        raise PyAudacityException(
            "noise_floor argument must be float or int, not " + str(type(noise_floor))
        )
    if not isinstance(ratio, (float, int)):
        raise PyAudacityException(
            "ratio argument must be float or int, not " + str(type(ratio))
        )
    if not isinstance(attack_time, (float, int)):
        raise PyAudacityException(
            "attack_time argument must be float or int, not " + str(type(attack_time))
        )
    if not isinstance(release_time, (float, int)):
        raise PyAudacityException(
            "release_time argument must be float or int, not " + str(type(release_time))
        )
    if not isinstance(normalize, bool):
        raise PyAudacityException(
            "normalize argument must be a bool, not" + str(type(normalize))
        )
    if not isinstance(use_peak, bool):
        raise PyAudacityException(
            "use_peak argument must be a bool, not" + str(type(use_peak))
        )

    return do(
        'Compressor: Threshold="{}" NoiseFloor="{}" Ratio="{}" AttackTime="{}" ReleaseTime="{}" Normalize="{}" UsePeak="{}"'.format(
            threshold,
            noise_floor,
            ratio,
            attack_time,
            release_time,
            normalize,
            use_peak,
        )
    )


def distortion():
    """TODO

    Audacity Documentation: Use the Distortion effect to make the audio sound distorted. By distorting the waveform the frequency content is changed, which will often make the sound "crunchy" or "abrasive". Technically this effect is a waveshaper. The result of waveshaping is equivalent to applying non-linear amplification to the audio waveform. Preset shaping functions are provided, each of which produces a different type of distortion.
    """
    raise NotImplementedError


def echo(delay=1.0, decay=0.5):
    # type: (float, float) -> str
    """TODO

    Audacity Documentation: Repeats the selected audio again and again, normally softer each time and normally not blended into the original sound until some time after it starts. The delay time between each repeat is fixed, with no pause in between each repeat. For a more configurable echo effect with a variable delay time and pitch-changed echoes, see Delay.
    """

    if not isinstance(delay, (float, int)):
        raise PyAudacityException(
            "delay argument must be float or int, not " + str(type(delay))
        )
    if not isinstance(decay, (float, int)):
        raise PyAudacityException(
            "decay argument must be float or int, not " + str(type(decay))
        )

    return do('Echo: Delay="{}" Decay="{}"'.format(delay, decay))


def fade_in():
    # type: () -> str
    """TODO

    Audacity Documentation: Applies a linear fade-in to the selected audio - the rapidity of the fade-in depends entirely on the length of the selection it is applied to. For a more customizable logarithmic fade, use the Envelope Tool on the Tools Toolbar.
    """

    return do("FadeIn")


def fade_out():
    # type: () -> str
    """TODO

    Audacity Documentation: Applies a linear fade-out to the selected audio - the rapidity of the fade-out depends entirely on the length of the selection it is applied to. For a more customizable logarithmic fade, use the Envelope Tool on the Tools Toolbar.
    """

    return do("FadeOut")


def filter_curve():
    """TODO

    Audacity Documentation: Adjusts the volume levels of particular frequencies."""
    raise NotImplementedError


def graphic_eq():
    """TODO

    Audacity Documentation: Adjusts the volume levels of particular frequencies."""
    raise NotImplementedError


def invert():
    # type: () -> str
    """TODO

    Audacity Documentation: This effect flips the audio samples upside-down. This normally does not affect the sound of the audio at all. It is occasionally useful for vocal removal.
    """

    return do("Invert")


def loudness_normalization(
    stereo_independent=False,
    LUFS_level=-23.0,
    RMS_level=-20.0,
    dual_mono=True,
    normalize_to=0,
):
    # type: (bool, float, float, bool, int) -> str
    """TODO

    Audacity Documentation: Changes the perceived loudness of the audio."""

    if not isinstance(stereo_independent, bool):
        raise PyAudacityException(
            "stereo_independent argument must be a bool, not"
            + str(type(stereo_independent))
        )
    if not isinstance(LUFS_level, (float, int)):
        raise PyAudacityException(
            "LUFS_level argument must be float or int, not " + str(type(LUFS_level))
        )
    if not isinstance(RMS_level, (float, int)):
        raise PyAudacityException(
            "RMS_level argument must be float or int, not " + str(type(RMS_level))
        )
    if not isinstance(dual_mono, bool):
        raise PyAudacityException(
            "dual_mono argument must be a bool, not" + str(type(dual_mono))
        )
    if not isinstance(normalize_to, int):
        raise PyAudacityException(
            "normalize_to argument must be int, not " + str(type(normalize_to))
        )

    return do(
        'LoudnessNormalization: StereoIndependent="{}" LUFSLevel="{}" RMFSLevel="{}" DualMono="{}" NormalizeTo="{}"'.format(
            stereo_independent, LUFS_level, RMS_level, dual_mono, normalize_to
        )
    )


# The documentation says this effect is not available for scripting.
# def noise_reduction():
#    # type: () -> str
#    """TODO
#
#    Audacity Documentation: This effect is ideal for reducing constant background noise such as fans, tape noise, or hums. It will not work very well for removing talking or music in the background. More details here
#    This effect is not currently available from scripting."""
#    return do('NoiseReduction')


def normalize(
    peak_level=-1.0, apply_gain=True, remove_dc_offset=True, stereo_independent=False
):
    # type: (float, bool, bool, bool) -> str
    """TODO

    Audacity Documentation: Use the Normalize effect to set the maximum amplitude of a track, equalize the amplitudes of the left and right channels of a stereo track and optionally remove any DC offset from the track.
    """

    if not isinstance(peak_level, (float, int)):
        raise PyAudacityException(
            "peak_level argument must be float or int, not " + str(type(peak_level))
        )
    if not isinstance(apply_gain, bool):
        raise PyAudacityException(
            "apply_gain argument must be a bool, not" + str(type(apply_gain))
        )
    if not isinstance(remove_dc_offset, bool):
        raise PyAudacityException(
            "remove_dc_offset argument must be a bool, not"
            + str(type(remove_dc_offset))
        )
    if not isinstance(stereo_independent, bool):
        raise PyAudacityException(
            "stereo_independent argument must be a bool, not"
            + str(type(stereo_independent))
        )

    return do(
        'Normalize: PeakLevel="{}" ApplyGain="{}" RemoveDcOffset="{}" StereoIndependent="{}"'.format(
            peak_level, apply_gain, remove_dc_offset, stereo_independent
        )
    )


def paulstretch(stretch_factor=10.0, time_resolution=0.25):
    # type: (float, float) -> str
    """TODO

    Audacity Documentation: Use Paulstretch only for an extreme time-stretch or "stasis" effect, This may be useful for synthesizer pad sounds, identifying performance glitches or just creating interesting aural textures. Use Change Tempo or Sliding Time Scale rather than Paulstretch for tasks like slowing down a song to a "practice" tempo.
    """

    if not isinstance(stretch_factor, (float, int)):
        raise PyAudacityException(
            "stretch_factor argument must be float or int, not "
            + str(type(stretch_factor))
        )
    if not isinstance(time_resolution, (float, int)):
        raise PyAudacityException(
            "time_resolution argument must be float or int, not "
            + str(type(time_resolution))
        )

    # TODO - documentation uses "Time Resolution" with a space. Check this out. I assume that there is no space for now.
    return do(
        'Paulstretch: StretchFactor="{}" TimeResolution="{}"'.format(
            stretch_factor, time_resolution
        )
    )


def phaser(
    stages=2, dry_wet=128, frequency=0.4, phase=0.0, depth=100, feedback=0, gain=-6.0
):
    # type: (int, int, float, float, int, int, float) -> str
    """TODO

    Audacity Documentation: The name "Phaser" comes from "Phase Shifter", because it works by combining phase-shifted signals with the original signal. The movement of the phase-shifted signals is controlled using a Low Frequency Oscillator (LFO).
    """

    if not isinstance(stages, int):
        raise PyAudacityException(
            "stages argument must be int, not " + str(type(stages))
        )
    if not isinstance(dry_wet, int):
        raise PyAudacityException(
            "dry_wet argument must be int, not " + str(type(dry_wet))
        )
    if not isinstance(frequency, (float, int)):
        raise PyAudacityException(
            "frequency argument must be float or int, not " + str(type(frequency))
        )
    if not isinstance(phase, (float, int)):
        raise PyAudacityException(
            "phase argument must be float or int, not " + str(type(phase))
        )
    if not isinstance(depth, int):
        raise PyAudacityException("depth argument must be int, not " + str(type(depth)))
    if not isinstance(feedback, int):
        raise PyAudacityException(
            "feedback argument must be int, not " + str(type(feedback))
        )
    if not isinstance(gain, (float, int)):
        raise PyAudacityException(
            "gain argument must be float or int, not " + str(type(gain))
        )

    return do(
        'Phaser: Stages="{}" DryWet="{}" Freq="{}" Phase="{}" Depth="{}" Feedback="{}" Gain="{}"'.format(
            stages, dry_wet, frequency, phase, depth, feedback, gain
        )
    )


def repair():
    # type: () -> str
    """TODO

    Audacity Documentation: Fix one particular short click, pop or other glitch no more than 128 samples long.
    """

    return do("Repair")


def repeat(count=1):
    # type: (int) -> str
    """TODO

    Audacity Documentation: Repeats the selection the specified number of times."""

    if not isinstance(count, int):
        raise PyAudacityException("count argument must be int, not " + str(type(count)))

    return do('Repeat: Count="{}"'.format(count))


def reverb(
    room_size=75.0,
    delay=10.0,
    reverberance=50.0,
    hf_damping=50.0,
    tone_low=100.0,
    tone_high=100.0,
    wet_gain=-1.0,
    dry_gain=-1.0,
    stereo_width=100.0,
    wet_only=False,
):
    # type: (float, float, float, float, float, float, float, float, float, bool) -> str
    """TODO

    Audacity Documentation: A configurable stereo reverberation effect with built-in and user-added presets. It can be used to add ambience (an impression of the space in which a sound occurs) to a mono sound. Also use it to increase reverberation in stereo audio that sounds too "dry" or "close".
    """

    if not isinstance(room_size, (float, int)):
        raise PyAudacityException(
            "room_size argument must be float or int, not " + str(type(room_size))
        )
    if not isinstance(delay, (float, int)):
        raise PyAudacityException(
            "delay argument must be float or int, not " + str(type(delay))
        )
    if not isinstance(reverberance, (float, int)):
        raise PyAudacityException(
            "reverberance argument must be float or int, not " + str(type(reverberance))
        )
    if not isinstance(hf_damping, (float, int)):
        raise PyAudacityException(
            "hf_damping argument must be float or int, not " + str(type(hf_damping))
        )
    if not isinstance(tone_low, (float, int)):
        raise PyAudacityException(
            "tone_low argument must be float or int, not " + str(type(tone_low))
        )
    if not isinstance(tone_high, (float, int)):
        raise PyAudacityException(
            "tone_high argument must be float or int, not " + str(type(tone_high))
        )
    if not isinstance(wet_gain, (float, int)):
        raise PyAudacityException(
            "wet_gain argument must be float or int, not " + str(type(wet_gain))
        )
    if not isinstance(dry_gain, (float, int)):
        raise PyAudacityException(
            "dry_gain argument must be float or int, not " + str(type(dry_gain))
        )
    if not isinstance(stereo_width, (float, int)):
        raise PyAudacityException(
            "stereo_width argument must be float or int, not " + str(type(stereo_width))
        )
    if not isinstance(wet_only, bool):
        raise PyAudacityException(
            "wet_only argument must be a bool, not" + str(type(wet_only))
        )

    return do(
        'Reverb: RoomSize="{}" Delay="{}" Reverberance="{}" HfDamping="{}" ToneLow="{}" ToneHigh="{}" WetGain="{}" DryGain="{}" StereoWidth="{}" WetOnly="{}"'.format(
            room_size,
            delay,
            reverberance,
            hf_damping,
            tone_low,
            tone_high,
            wet_gain,
            dry_gain,
            stereo_width,
            wet_only,
        )
    )


def reverse():
    # type: () -> str
    """TODO

    Audacity Documentation: Reverses the selected audio; after the effect the end of the audio will be heard first and the beginning last.
    """

    return do("Reverse")


def sliding_stretch(
    rate_percent_change_start=0.0,
    rate_percent_change_end=0.0,
    pitch_half_steps_start=0.0,
    pitch_half_steps_end=0.0,
    pitch_percent_change_start=0.0,
    pitch_percent_change_end=0.0,
):
    # type: (float, float, float, float, float, float) -> str
    """TODO

    Audacity Documentation: This effect allows you to make a continuous change to the tempo and/or pitch of a selection by choosing initial and/or final change values.
    """

    if not isinstance(rate_percent_change_start, (float, int)):
        raise PyAudacityException(
            "rate_percent_change_start argument must be float or int, not "
            + str(type(rate_percent_change_start))
        )
    if not isinstance(rate_percent_change_end, (float, int)):
        raise PyAudacityException(
            "rate_percent_change_end argument must be float or int, not "
            + str(type(rate_percent_change_end))
        )
    if not isinstance(pitch_half_steps_start, (float, int)):
        raise PyAudacityException(
            "pitch_half_steps_start argument must be float or int, not "
            + str(type(pitch_half_steps_start))
        )
    if not isinstance(pitch_half_steps_end, (float, int)):
        raise PyAudacityException(
            "pitch_half_steps_end argument must be float or int, not "
            + str(type(pitch_half_steps_end))
        )
    if not isinstance(pitch_percent_change_start, (float, int)):
        raise PyAudacityException(
            "pitch_percent_change_start argument must be float or int, not "
            + str(type(pitch_percent_change_start))
        )
    if not isinstance(pitch_percent_change_end, (float, int)):
        raise PyAudacityException(
            "pitch_percent_change_end argument must be float or int, not "
            + str(type(pitch_percent_change_end))
        )

    return do(
        'SlidingStretch: RatePercentChangeStart="{}" RatePercentChangeEnd="{}" PitchHalfStepsStart="{}" PitchHalfStepsEnd="{}" PitchPercentChangeStart="{}" PitchPercentChangeEnd="{}"'.format(
            rate_percent_change_start,
            rate_percent_change_end,
            pitch_half_steps_start,
            pitch_half_steps_end,
            pitch_percent_change_start,
            pitch_percent_change_end,
        )
    )


def truncate_silence(
    threshold=-20.0,
    action="Truncate",
    minimum=0.5,
    truncate=0.5,
    compress=50.0,
    independent=False,
):
    # type: (float, str, float, float, float, bool) -> str
    """TODO

    Audacity Documentation: Automatically try to find and eliminate audible silences. Do not use this with faded audio.
    """

    if not isinstance(threshold, (float, int)):
        raise PyAudacityException(
            "threshold argument must be float or int, not " + str(type(threshold))
        )
    # TODO action check
    if not isinstance(minimum, (float, int)):
        raise PyAudacityException(
            "minimum argument must be float or int, not " + str(type(minimum))
        )
    if not isinstance(truncate, (float, int)):
        raise PyAudacityException(
            "truncate argument must be float or int, not " + str(type(truncate))
        )
    if not isinstance(compress, (float, int)):
        raise PyAudacityException(
            "compress argument must be float or int, not " + str(type(compress))
        )
    if not isinstance(independent, bool):
        raise PyAudacityException(
            "independent argument must be a bool, not" + str(type(independent))
        )

    return do(
        'TruncateSilence: Threshold="{}" Action="{}" Minimum="{}" Truncate="{}" Compress="{}" Independent="{}"'.format(
            threshold, action, minimum, truncate, compress, independent
        )
    )


def wahwah(freq=1.5, phase=0.0, depth=70, resonance=2.5, offset=30, gain=-6.0):
    # type: (float, float, int, float, int, float) -> str
    """TODO

    Audacity Documentation: Rapid tone quality variations, like that guitar sound so popular in the 1970's.
    """

    if not isinstance(freq, (float, int)):
        raise PyAudacityException(
            "freq argument must be float or int, not " + str(type(freq))
        )
    if not isinstance(phase, (float, int)):
        raise PyAudacityException(
            "phase argument must be float or int, not " + str(type(phase))
        )
    if not isinstance(depth, int):
        raise PyAudacityException("depth argument must be int, not " + str(type(depth)))
    if not isinstance(resonance, (float, int)):
        raise PyAudacityException(
            "resonance argument must be float or int, not " + str(type(resonance))
        )
    if not isinstance(offset, int):
        raise PyAudacityException(
            "offset argument must be int, not " + str(type(offset))
        )
    if not isinstance(gain, (float, int)):
        raise PyAudacityException(
            "gain argument must be float or int, not " + str(type(gain))
        )

    return do(
        'Wahwah: Freq="{}" Phase="{}" Depth="{}" Resonance="{}" Offset="{}" Gain="{}"'.format(
            freq, phase, depth, resonance, offset, gain
        )
    )


def adjustable_fade(
    fade_type="Up", curve=0.0, units="Percent", gain0=0, gain1=0, preset="None"
):
    # type: (str, float, str, float, float, str) -> str
    """TODO

    Audacity Documentation: Enables you to control the shape of the fade (non-linear fading) to be applied by adjusting various parameters; allows partial (that is not from or to zero) fades up or down.
    """

    # TODO add param checks

    return do(
        'AdjustableFade: type="{}" curve="{}" units="{}" gain0="{}" gain1="{}" preset="{}"'.format(
            fade_type, curve, units, gain0, gain1, preset
        )
    )


def clip_fix(threshold=0.0, gain=0.0):
    # type: (float, float) -> str
    """TODO

    Audacity Documentation: Clip Fix attempts to reconstruct clipped regions by interpolating the lost signal.
    """

    if not isinstance(threshold, (float, int)):
        raise PyAudacityException(
            "threshold argument must be float or int, not " + str(type(threshold))
        )
    if not isinstance(gain, (float, int)):
        raise PyAudacityException(
            "gain argument must be float or int, not " + str(type(gain))
        )

    return do('ClipFix: threshold="{}" gain="{}"'.format(threshold, gain))


def crossfade_clips():
    # type: () -> str
    """TODO

    Audacity Documentation: Use Crossfade Clips to apply a simple crossfade to a selected pair of clips in a single audio track.
    """

    return do("CrossfadeClips")


def crossfade_tracks(xfade_type="ConstantGain", curve=0.0, direction="Automatic"):
    # type: (str, float, str) -> str
    """TODO

    Audacity Documentation: Use Crossfade Tracks to make a smooth transition between two overlapping tracks one above the other. Place the track to be faded out above the track to be faded in then select the overlapping region in both tracks and apply the effect.
    """

    # TODO - add param checks
    return do(
        'CrossfadeTracks: type="{}" curve="{}" direction="{}"'.format(
            xfade_type, curve, direction
        )
    )


def delay(
    delay_type="Regular",
    d_gain=0.0,
    delay=0.0,
    pitch_type="PitchTempo",
    shift=0.0,
    number=0,
    constrain="Yes",
):
    # type: (str, float, float, str, float, int, str) -> str
    """TODO

    Audacity Documentation: A configurable delay effect with variable delay time and pitch shifting of the delays.
    """

    # TODO - add param checks

    return do(
        'Delay: delay-type="{}" dgain="{}" delay="{}" pitch-type="{}" shift="{}" number="{}" constrain="{}"'.format(
            delay_type, d_gain, delay, pitch_type, shift, number, constrain
        )
    )


def high_pass_filter(frequency=0.0, roll_off="dB6"):
    # type: (float, str) -> str
    """TODO

    Audacity Documentation: Passes frequencies above its cutoff frequency and attenuates frequencies below its cutoff frequency.
    """

    return do(
        'High-passFilter: frequency="{}" rolloff="{}"'.format(frequency, roll_off)
    )


def limiter(
    limiter_type="SoftLimit", gain_left=0, gain_right=0, limit=0, hold=0, makeup="No"
):
    # type: (str, float, float, float, float, str) -> str
    """TODO

    Audacity Documentation: Limiter passes signals below a specified input level unaffected or gently reduced, while preventing the peaks of stronger signals from exceeding this threshold. Mastering engineers often use this type of dynamic range compression combined with make-up gain to increase the perceived loudness of an audio recording during the audio mastering process.
    """

    return do(
        'Limiter: type="{}" gain-L="{}" gain-R="{}" thresh="{}" hold="{}" makeup="{}"'.format(
            limiter_type, gain_left, gain_right, limit, hold, makeup
        )
    )


def low_pass_filter(frequency=0.0, roll_off="db6"):
    # type: (float, str) -> str
    """TODO

    Audacity Documentation: Passes frequencies below its cutoff frequency and attenuates frequencies above its cutoff frequency.
    """

    return do('Low-passFilter: frequency="{}" rolloff="{}"'.format(frequency, roll_off))


def notch_filter(frequency=0.0, q=0.0):
    # type: (float, float) -> str
    """TODO

    Audacity Documentation: Greatly attenuate ("notch out"), a narrow frequency band. This is a good way to remove mains hum or a whistle confined to a specific frequency with minimal damage to the remainder of the audio.
    """

    if not isinstance(frequency, (float, int)):
        raise PyAudacityException(
            "frequency argument must be float or int, not " + str(type(frequency))
        )
    if not isinstance(q, (float, int)):
        raise PyAudacityException(
            "q argument must be float or int, not " + str(type(q))
        )

    return do('NotchFilter: frequency="{}" q="{}"'.format(frequency, q))


def spectral_edit_multi_tool():
    # type: () -> str
    """TODO

    Audacity Documentation: When the selected track is in spectrogram or spectrogram log(f) view, applies a notch filter, high pass filter or low pass filter according to the spectral selection made. This effect can also be used to change the audio quality as an alternative to using Equalization.
    """
    return do("SpectralEditMultiTool")


def spectral_edit_parametric_eq(control_gain=0.0):
    # type: (float) -> str
    """TODO

    Audacity Documentation: When the selected track is in spectrogram or spectrogram log(f) view and the spectral selection has a center frequency and an upper and lower boundary, performs the specified band cut or band boost. This can be used as an alternative to Equalization or may also be useful to repair damaged audio by reducing frequency spikes or boosting other frequencies to mask spikes.
    """

    if not isinstance(control_gain, (float, int)):
        raise PyAudacityException(
            "control_gain argument must be float or int, not " + str(type(control_gain))
        )

    # TODO - double check other macros for parameter names with dashes.
    return do('SpectralEditParametricEq: control-gain="{}"'.format(control_gain))


def spectral_edit_shelves(control_gain=0.0):
    # type: (float) -> str
    """TODO

    Audacity Documentation: When the selected track is in spectrogram or spectrogram log(f) view, applies either a low- or high-frequency shelving filter or both filters, according to the spectral selection made. This can be used as an alternative to Equalization or may also be useful to repair damaged audio by reducing frequency spikes or boosting other frequencies to mask spikes.
    """

    if not isinstance(control_gain, (float, int)):
        raise PyAudacityException(
            "control_gain argument must be float or int, not " + str(type(control_gain))
        )

    return do('SpectralEditShelves: control-gain="{}"'.format(control_gain))


def studio_fade_out():
    # type: () -> str
    """TODO

    Audacity Documentation: Applies a more musical fade out to the selected audio, giving a more pleasing sounding result.
    """

    return do("StudioFadeOut")


def tremolo(wave="Sine", phase=0, wet=0, lfo=0.0):
    # type: (str, int, int, float) -> str
    """TODO

    Audacity Documentation: Modulates the volume of the selection at the depth and rate selected in the dialog. The same as the tremolo effect familiar to guitar and keyboard players.
    """

    # TODO check wave argument

    # TODO in the Tremolo dialog, wet's default is 40 and frequency's default is 4.0. Are the docs wrong?

    # TODO in the Tremolo dialog, lfo is labeled "Frequency". What's the correct name?

    if not isinstance(phase, int):
        raise PyAudacityException("phase argument must be int, not " + str(type(phase)))
    if not isinstance(wet, int):
        raise PyAudacityException("wet argument must be int, not " + str(type(wet)))
    if not isinstance(lfo, (float, int)):
        raise PyAudacityException(
            "lfo argument must be float or int, not " + str(type(lfo))
        )

    return do(
        'Tremolo: wave="{}" phase="{}" wet="{}" lfo="{}"'.format(wave, phase, wet, lfo)
    )


def vocal_reduction_and_isolation(
    action="RemoveToMono", strength=0.0, low_transition=0.0, high_transition=0.0
):
    # type: (str, float, float, float) -> str
    """TODO

    Audacity Documentation: Attempts to remove or isolate center-panned audio from a stereo track. Most "Remove" options in this effect preserve the stereo image.
    """

    actions = "RemoveToMono Remove Isolate IsolateInvert RemoveCenterToMono RemoveCenter IsolateCenter IsolateCenterInvert Analyze".split()

    if action not in actions:
        raise PyAudacityException(
            "action must be one of "
            + ", ".join(actions)
            + ", but was: '"
            + action
            + "'."
        )

    if not isinstance(strength, (float, int)):
        raise PyAudacityException(
            "strength argument must be float or int, not " + str(type(strength))
        )
    if not isinstance(low_transition, (float, int)):
        raise PyAudacityException(
            "low_transition argument must be float or int, not "
            + str(type(low_transition))
        )
    if not isinstance(high_transition, (float, int)):
        raise PyAudacityException(
            "high_transition argument must be float or int, not "
            + str(type(high_transition))
        )

    return do(
        'VocalReductionAndIsolation: strength="{}" low_transition="{}" high_transition="{}"'.format(
            strength, low_transition, high_transition
        )
    )


def vocoder(
    dst=0.0,
    mst="BothChannels",
    bands=0,
    track_vl=0.0,
    noise_vl=0.0,
    radar_vl=0.0,
    radar_f=0.0,
):
    # type: (float, str, int, float, float, float, float) -> str
    """TODO

    Audacity Documentation: Synthesizes audio (usually a voice) in the left channel of a stereo track with a carrier wave (typically white noise) in the right channel to produce a modified version of the left channel. Vocoding a normal voice with white noise will produce a robot-like voice for special effects.
    """

    if not isinstance(dst, (float, int)):
        raise PyAudacityException(
            "dst argument must be float or int, not " + str(type(dst))
        )

    msts = "BothChannels RightOnly".split()


    if mst not in msts:
        raise PyAudacityException(
            "mst must be one of "
            + ", ".join(msts)
            + ", but was: '"
            + mst
            + "'."
        )

    if not isinstance(bands, int):
        raise PyAudacityException("bands argument must be int, not " + str(type(bands)))
    if not isinstance(track_vl, (float, int)):
        raise PyAudacityException(
            "track_vl argument must be float or int, not " + str(type(track_vl))
        )
    if not isinstance(noise_vl, (float, int)):
        raise PyAudacityException(
            "noise_vl argument must be float or int, not " + str(type(noise_vl))
        )
    if not isinstance(radar_vl, (float, int)):
        raise PyAudacityException(
            "radar_vl argument must be float or int, not " + str(type(radar_vl))
        )
    if not isinstance(radar_f, (float, int)):
        raise PyAudacityException(
            "radar_f argument must be float or int, not " + str(type(radar_f))
        )

    return do(
        'Vocoder: dst="{}" mst="{}" bands="{}" track-vl="{}" noise-vl="{}" radar-vl="{}" radar-f="{}"'.format(
            dst, mst, bands, track_vl, noise_vl, radar_vl, radar_f
        )
    )


# NOTE THE SPELLING OF "ANALYZERS"
def manage_analyzers():
    # type: () -> str
    """TODO

    Audacity Documentation: Selecting this option from the Effect Menu (or the Generate Menu or Analyze Menu) takes you to a dialog where you can enable or disable particular Effects, Generators and Analyzers in Audacity. Even if you do not add any third-party plugins, you can use this to make the Effect menu shorter or longer as required. For details see Plugin Manager.
    """
    return do("ManageAnalyzers")


# NOTE THE SPELLING OF "ANALYSER"
def contrast_analyser():
    # type: () -> str
    """TODO

    Audacity Documentation: Analyzes a single mono or stereo speech track to determine the average RMS difference in volume (contrast) between foreground speech and background music, audience noise or similar. The purpose is to determine if the speech will be intelligible to the hard of hearing.
    """
    return do("ConrastAnalyser")


def plot_spectrum():
    # type: () -> str
    """TODO

    Audacity Documentation: Takes the selected audio (which is a set of sound pressure values at points in time) and converts it to a graph of frequencies against amplitudes.
    """
    return do("PlotSpectrum")


def find_clipping(duty_cycle_start=3, duty_cycle_end=3):
    # type: (int, int) -> str
    """TODO

    Audacity Documentation: Displays runs of clipped samples in a Label Track, as a screen-reader accessible alternative to View > Show Clipping. A run must include at least one clipped sample, but may include unclipped samples too.
    """

    # TODO Parameter names in documentation have spaces, double check

    if not isinstance(duty_cycle_start, int):
        raise PyAudacityException(
            "duty_cycle_start argument must be int, not " + str(type(duty_cycle_start))
        )
    if not isinstance(duty_cycle_end, int):
        raise PyAudacityException(
            "duty_cycle_end argument must be int, not " + str(type(duty_cycle_end))
        )

    return do(
        'FindClipping: DutyCycleStart="{}" DutyCycleEnd="{}"'.format(
            duty_cycle_start, duty_cycle_end
        )
    )


def beat_finder(thresval=0):
    # type: (int) -> str
    """TODO

    Audacity Documentation: Attempts to place labels at beats which are much louder than the surrounding audio. It's a fairly rough and ready tool, and will not necessarily work well on a typical modern pop music track with compressed dynamic range. If you do not get enough beats detected, try reducing the "Threshold Percentage" setting.
    """

    if not isinstance(thresval, int):
        raise PyAudacityException(
            "thresval argument must be int, not " + str(type(thresval))
        )

    return do('BeatFinder: thresval="{}"'.format(thresval))


def label_sounds(
    thershold_level=-30,
    threshold_measurement="Peak level",
    min_silence_duration=0,
    min_label_interval=0,
    label_type="Point before sound",
    max_leading_silence=0,
    max_trailing_silence=0,
    label_text="Sound ##1",
):
    # type: (float, str, float, float, str, float, float, str) -> str
    """TODO

    Audacity Documentation: Divides up a track by placing labels for areas of sound that are separated by silence.
    """

    return do(
        'LabelSounds: threshold="{}" measurement="{}" sil-dur="{}" snd-dur="{}" type="{}" pre-offset="{}" post-offset="{}" text="{}"'.format(
            thershold_level,
            threshold_measurement,
            min_silence_duration,
            min_label_interval,
            label_type,
            max_leading_silence,
            max_trailing_silence,
            label_text,
        )
    )


def manage_tools():
    # type: () -> str
    """TODO

    Audacity Documentation: Selecting this option from the Effect Menu (or the Generate Menu or Analyze Menu) takes you to a dialog where you can enable or disable particular Effects, Generators and Analyzers in Audacity. Even if you do not add any third-party plugins, you can use this to make the Effect menu shorter or longer as required. For details see Plugin Manager.
    """

    return do("ManageTools")


def manage_macros():
    # type: () -> str
    """TODO

    Audacity Documentation: Creates a new macro or edits an existing macro."""

    return do("ManageMacros")


def apply_macro():
    # type: () -> str
    """TODO

    Audacity Documentation: Displays a menu with list of all your Macros. Selecting any of these Macros by clicking on it will cause that Macro to be applied to the current project.
    """

    # TODO - documentation shows "Apply Macro" as the name, with a space. I assume this is wrong and remove the space:
    return do("ApplyMacro")


def screenshot(
    save_images_to_folder=Path.home(),
    capture="Window Only",
    background="None",
    to_top=True,
):
    """TODO

    Audacity Documentation: A tool, mainly used in documentation, to capture screenshots of Audacity.
    """

    # TODO - find out what "ToTop" parameter is for. The docs don't say and it doesn't appear in the UI.
    raise NotImplementedError


def benchmark():
    """Opens the Tools > Run Benchmark dialog.

    Audacity Documentation: A tool for measuring the performance of one part of Audacity.
    """

    return do("Benchmark")


def nyquist_prompt(command="", version=3):
    # type: (str, int) -> str
    """TODO

    Audacity Documentation: Brings up a dialog where you can enter Nyquist commands. Nyquist is a programming language for generating, processing and analyzing audio. For more information see Nyquist Plugins Reference.
    """

    if not isinstance(command, str):
        raise PyAudacityException(
            "command argument must be str, not " + str(type(command))
        )
    if not isinstance(version, int):
        raise PyAudacityException(
            "version argument must be int, not " + str(type(version))
        )

    return do('NyquistPrompt: Command="{}" Version="{}"'.format(command, version))


def nyquist_plugin_installer(files="", overwrite="Disallow"):
    """TODO

    Audacity Documentation: A Nyquist plugin that simplifies the installation of other Nyquist plugins.
    """
    raise NotImplementedError


def regular_interval_labels(
    mode="Both",
    total_num=0,
    interval=0.0,
    region=0.0,
    adjust="No",
    label_text="",
    zeros="TextOnly",
    first_number=0,
    verbose="Details",
):
    # type: (str, int, float, float, str, str, str, int, str) -> str
    """TODO

    Audacity Documentation: Places labels in a long track so as to divide it into smaller, equally sized segments.
    """

    # TODO check mode, adjust, label_text, zeros, verbose
    if not isinstance(total_num, int):
        raise PyAudacityException(
            "total_num argument must be int, not " + str(type(total_num))
        )
    if not isinstance(interval, (float, int)):
        raise PyAudacityException(
            "interval argument must be float or int, not " + str(type(interval))
        )
    if not isinstance(region, (float, int)):
        raise PyAudacityException(
            "region argument must be float or int, not " + str(type(region))
        )
    if not isinstance(first_number, int):
        raise PyAudacityException(
            "first_number argument must be int, not " + str(type(first_number))
        )

    return do(
        'RegularIntervalLabels: mode="{}" totalnum="{}" interval="{}" region="{}" adjust="{}" labeltext="{}" zeros="{}" firstnum="{}" verbose="{}"'.format(
            mode,
            total_num,
            interval,
            region,
            adjust,
            label_text,
            zeros,
            first_number,
            verbose,
        )
    )


def sample_data_export(
    export_filename,
    limit_output_to_first=100,
    measurement_scale="dB",
    index_format="None",
    include_header_information="None",
    optional_header_text="",
    channel_layout_for_stereo="L-R on Same Line",
    show_messages="Yes",
):
    # type: (Union[Path, str], int, str, str, str, str, str, str) -> str
    """TODO

    Audacity Documentation: Reads the values of successive samples from the selected audio and prints this data to a plain text, CSV or HTML file.
    """

    # TODO - check params

    return do(
        'SampleDataExport: number="{}" units="{}" filename="{}" fileformat="{}" header="{}" optext="{}" channel-layout="{}" messages="{}"'.format(
            limit_output_to_first,
            measurement_scale,
            export_filename,
            index_format,
            include_header_information,
            optional_header_text,
            channel_layout_for_stereo,
            show_messages,
        )
    )


def sample_data_import(import_filename, invalid_data_handling="Throw Error"):
    # type: (Union[Path, str], str) -> str
    """TODO

    Audacity Documentation: Reads numeric values from a plain ASCII text file and creates a PCM sample for each numeric value read.
    """
    raise NotImplementedError


def apply_macros_palette():
    # type: () -> str
    """TODO

    Audacity Documentation: Displays a menu with list of all your Macros which can be applied to the current project or to audio files.
    """
    return do("ApplyMacrosPalette")


def macro_fade_ends():
    # type: () -> str
    """TODO

    Audacity Documentation: Fades in the first second and fades out the last second of a track.
    """
    return do("Macro_FadeEnds")


def macro_mp3_conversion():
    # type: () -> str
    """TODO

    Audacity Documentation: Converts MP3."""
    return do("Macro_MP3Conversion")


def full_screen_on_off():
    # type: () -> str
    """TODO

    Audacity Documentation: Toggle full screen mode with no title bar."""
    return do("FullScreenOnOff")


def play():
    # type: () -> str
    """TODO

    Audacity Documentation: Play (or stop) audio."""
    return do("Play")


def stop():
    # type: () -> str
    """TODO

    Audacity Documentation: Stop audio."""
    return do("Stop")


def play_one_sec():
    # type: () -> str
    """TODO

    Audacity Documentation: Plays for one second centered on the current mouse pointer position (not from the current cursor position). See this page for an example.
    """
    return do("PlayOneSec")


def play_to_selection():
    # type: () -> str
    """TODO

    Audacity Documentation: Plays to or from the current mouse pointer position to or from the start or end of the selection, depending on the pointer position. See this page for more details.
    """
    return do("PlayToSelection")


def play_before_selection_start():
    # type: () -> str
    """TODO

    Audacity Documentation: Plays a short period before the start of the selected audio, the period before shares the setting of the cut preview.
    """
    return do("PlayBeforeSelectionStart")


def play_after_selection_start():
    # type: () -> str
    """TODO

    Audacity Documentation: Plays a short period after the start of the selected audio, the period after shares the setting of the cut preview.
    """
    return do("PlayAfterSelectionStart")


def play_before_selection_end():
    # type: () -> str
    """TODO

    Audacity Documentation: Plays a short period before the end of the selected audio, the period before shares the setting of the cut preview.
    """
    return do("PlayBeforeSelectionEnd")


def play_after_selection_end():
    # type: () -> str
    """TODO

    Audacity Documentation: Plays a short period after the end of the selected audio, the period after shares the setting of the cut preview.
    """
    return do("PlayAfterSelectionEnd")


def play_before_and_after_selection_start():
    # type: () -> str
    """TODO

    Audacity Documentation: Plays a short period before and after the start of the selected audio, the periods before and after share the setting of the cut preview.
    """
    return do("PlayBeforeAndAfterSelectionStart")


def play_before_and_after_selection_end():
    # type: () -> str
    """TODO

    Audacity Documentation: Plays a short period before and after the end of the selected audio, the periods before and after share the setting of the cut preview.
    """
    return do("PlayBeforeAndAfterSelectionEnd")


def play_cut_preview():
    # type: () -> str
    """TODO

    Audacity Documentation: Plays audio excluding the selection."""
    return do("PlayCutPreview")


def select_tool():
    # type: () -> str
    """TODO

    Audacity Documentation: Chooses Selection tool."""
    return do("SelectTool")


def envelope_tool():
    # type: () -> str
    """TODO

    Audacity Documentation: Chooses Envelope tool."""
    return do("EnvelopeTool")


def draw_tool():
    # type: () -> str
    """TODO

    Audacity Documentation: Chooses Draw tool."""
    return do("DrawTool")


def zoom_tool():
    # type: () -> str
    """TODO

    Audacity Documentation: Chooses Zoom tool."""
    return do("ZoomTool")


def multi_tool():
    # type: () -> str
    """TODO

    Audacity Documentation: Chooses the Multi-Tool."""
    return do("MultiTool")


def prev_tool():
    # type: () -> str
    """TODO

    Audacity Documentation: Cycles backwards through the tools, starting from the currently selected tool:  # type: () -> str starting from Selection, it would navigate to Multi-tool to Time Shift to Zoom to Draw to Envelope to Selection.
    """
    return do("PrevTool")


def next_tool():
    # type: () -> str
    """TODO

    Audacity Documentation: Cycles forwards through the tools, starting from the currently selected tool:  # type: () -> str starting from Selection, it would navigate to Envelope to Draw to Zoom to Time Shift to Multi-tool to Selection.
    """
    return do("NextTool")


def output_gain():
    # type: () -> str
    """TODO

    Audacity Documentation: Displays the Playback Volume dialog. You can type a new value for the playback volume (between 0 and 1), or press Tab, then use the left and right arrow keys to adjust the slider.
    """
    return do("OutputGain")


def output_gain_inc():
    # type: () -> str
    """TODO

    Audacity Documentation: Each key press will increase the playback volume by 0.1."""
    return do("OutputGainInc")


def output_gain_dec():
    # type: () -> str
    """TODO

    Audacity Documentation: Each key press will decrease the playback volume by 0.1."""
    return do("OutputGainDec")


def input_gain():
    # type: () -> str
    """TODO

    Audacity Documentation: Displays the Recording Volume dialog. You can type a new value for the recording volume (between 0 and 1), or press Tab, then use the left and right arrow keys to adjust the slider.
    """
    return do("InputGain")


def input_gain_inc():
    # type: () -> str
    """TODO

    Audacity Documentation: Each key press will increase the recording volume by 0.1."""
    return do("InputGainInc")


def input_gain_dec():
    # type: () -> str
    """TODO

    Audacity Documentation: Each key press will decrease the recording volume by 0.1."""
    return do("InputGainDec")


def delete_key():
    # type: () -> str
    """TODO

    Audacity Documentation: Deletes the selection. When focus is in Selection Toolbar, BACKSPACE is not a shortcut but navigates back to the previous digit and sets it to zero.
    """
    return do("DeleteKey")


def delete_key2():
    # type: () -> str
    """TODO

    Audacity Documentation: Deletes the selection."""
    return do("DeleteKey2")


def play_at_speed():
    # type: () -> str
    """TODO

    Audacity Documentation: Play audio at a faster or slower speed."""
    return do("PlayAtSpeed")


def play_at_speed_looped():
    # type: () -> str
    """TODO

    Audacity Documentation: Combines looped play and play at speed."""
    return do("PlayAtSpeedLooped")


def play_at_speed_cut_preview():
    # type: () -> str
    """TODO

    Audacity Documentation: Combines cut preview and play at speed."""
    return do("PlayAtSpeedCutPreview")


def set_play_speed():
    # type: () -> str
    """TODO

    Audacity Documentation: Displays the Playback Speed dialog. You can type a new value for the playback volume (between 0 and 1), or press Tab, then use the left and right arrow keys to adjust the slider.
    """
    return do("SetPlaySpeed")


def play_speed_inc():
    # type: () -> str
    """TODO

    Audacity Documentation: Each key press will increase the playback speed by 0.1."""
    return do("PlaySpeedInc")


def play_speed_dec():
    # type: () -> str
    """TODO

    Audacity Documentation: Each key press will decrease the playback speed by 0.1."""
    return do("PlaySpeedDec")


def move_to_prev_label():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves selection to the previous label."""
    return do("MoveToPrevLabel")


def move_to_next_label():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves selection to the next label."""
    return do("MoveToNextLabel")


def seek_left_short():
    # type: () -> str
    """TODO

    Audacity Documentation: Skips the playback cursor back one second by default."""
    return do("SeekLeftShort")


def seek_right_short():
    # type: () -> str
    """TODO

    Audacity Documentation: Skips the playback cursor forward one second by default."""
    return do("SeekRightShort")


def seek_left_long():
    # type: () -> str
    """TODO

    Audacity Documentation: Skips the playback cursor back 15 seconds by default."""
    return do("SeekLeftLong")


def seek_right_long():
    # type: () -> str
    """TODO

    Audacity Documentation: Skips the playback cursor forward 15 seconds by default."""
    return do("SeekRightLong")


def input_device():
    # type: () -> str
    """TODO

    Audacity Documentation: Displays the Select recording Device dialog for choosing the recording device, but only if the "Recording Device" dropdown menu in Device Toolbar has entries for devices. Otherwise, an recording error message will be displayed.
    """
    return do("InputDevice")


def output_device():
    # type: () -> str
    """TODO

    Audacity Documentation: Displays the Select Playback Device dialog for choosing the playback device, but only if the "Playback Device" dropdown menu in Device Toolbar has entries for devices. Otherwise, an error message will be displayed.
    """
    return do("OutputDevice")


def audio_host():
    # type: () -> str
    """TODO

    Audacity Documentation: Displays the Select Audio Host dialog for choosing the particular interface with which Audacity communicates with your chosen playback and recording devices.
    """
    return do("AudioHost")


def input_channels():
    # type: () -> str
    """TODO

    Audacity Documentation: Displays the Select Recording Channels dialog for choosing the number of channels to be recorded by the chosen recording device.
    """
    return do("InputChannels")


def snap_to_off():
    # type: () -> str
    """TODO

    Audacity Documentation: Equivalent to setting the Snap To control in Selection Toolbar to "Off".
    """
    return do("SnapToOff")


def snap_to_nearest():
    # type: () -> str
    """TODO

    Audacity Documentation: Equivalent to setting the Snap To control in Selection Toolbar to "Nearest".
    """
    return do("SnapToNearest")


def snap_to_prior():
    # type: () -> str
    """TODO

    Audacity Documentation: Equivalent to setting the Snap To control in Selection Toolbar to "Prior".
    """
    return do("SnapToPrior")


def sel_start():
    # type: () -> str
    """TODO

    Audacity Documentation: Select from cursor to start of track."""
    return do("SelStart")


def sel_end():
    # type: () -> str
    """TODO

    Audacity Documentation: Select from cursor to end of track."""
    return do("SelEnd")


def sel_ext_left():
    # type: () -> str
    """TODO

    Audacity Documentation: Increases the size of the selection by extending it to the left. The amount of increase is dependent on the zoom level. If there is no selection one is created starting at the cursor position.
    """
    return do("SelExtLeft")


def sel_ext_right():
    # type: () -> str
    """TODO

    Audacity Documentation: Increases the size of the selection by extending it to the right. The amount of increase is dependent on the zoom level. If there is no selection one is created starting at the cursor position.
    """
    return do("SelExtRight")


def sel_set_ext_left():
    # type: () -> str
    """TODO

    Audacity Documentation: Extend selection left a little (is this a duplicate?)."""
    return do("SelSetExtLeft")


def sel_set_ext_right():
    # type: () -> str
    """TODO

    Audacity Documentation: Extend selection right a litlle (is this a duplicate?)."""
    return do("SelSetExtRight")


def sel_cntr_left():
    # type: () -> str
    """TODO

    Audacity Documentation: Decreases the size of the selection by contracting it from the right. The amount of decrease is dependent on the zoom level. If there is no selection no action is taken.
    """
    return do("SelCntrLeft")


def sel_cntr_right():
    # type: () -> str
    """TODO

    Audacity Documentation: Decreases the size of the selection by contracting it from the left. The amount of decrease is dependent on the zoom level. If there is no selection no action is taken.
    """
    return do("SelCntrRight")


def prev_frame():
    # type: () -> str
    """TODO

    Audacity Documentation: Move backward through currently focused toolbar in Upper Toolbar dock area, Track View and currently focused toolbar in Lower Toolbar dock area. Each use moves the keyboard focus as indicated.
    """
    return do("PrevFrame")


def next_frame():
    # type: () -> str
    """TODO

    Audacity Documentation: Move forward through currently focused toolbar in Upper Toolbar dock area, Track View and currently focused toolbar in Lower Toolbar dock area. Each use moves the keyboard focus as indicated.
    """
    return do("NextFrame")


def prev_track():
    # type: () -> str
    """TODO

    Audacity Documentation: Focus one track up."""
    return do("PrevTrack")


def next_track():
    # type: () -> str
    """TODO

    Audacity Documentation: Focus one track down."""
    return do("NextTrack")


def first_track():
    # type: () -> str
    """TODO

    Audacity Documentation: Focus on first track."""
    return do("FirstTrack")


def last_track():
    # type: () -> str
    """TODO

    Audacity Documentation: Focus on last track."""
    return do("LastTrack")


def shift_up():
    # type: () -> str
    """TODO

    Audacity Documentation: Focus one track up and select it."""
    return do("ShiftUp")


def shift_down():
    # type: () -> str
    """TODO

    Audacity Documentation: Focus one track down and select it."""
    return do("ShiftDown")


def toggle():
    # type: () -> str
    """TODO

    Audacity Documentation: Toggle focus on current track."""
    return do("Toggle")


def toggle_alt():
    # type: () -> str
    """TODO

    Audacity Documentation: Toggle focus on current track."""
    return do("ToggleAlt")


def cursor_left():
    # type: () -> str
    """TODO

    Audacity Documentation: When not playing audio, moves the editing cursor one screen pixel to left. When a Snap To option is chosen, moves the cursor to the preceding unit of time as determined by the current selection format. If the key is held down, the cursor speed depends on the length of the tracks. When playing audio, moves the playback cursor as described at "Cursor Short Jump Left".
    """
    return do("CursorLeft")


def cursor_right():
    # type: () -> str
    """TODO

    Audacity Documentation: When not playing audio, moves the editing cursor one screen pixel to right. When a Snap To option is chosen, moves the cursor to the following unit of time as determined by the current selection format. If the key is held down, the cursor speed depends on the length of the tracks. When playing audio, moves the playback cursor as described at "Cursor Short Jump Right".
    """
    return do("CursorRight")


def cursor_short_jump_left():
    # type: () -> str
    """TODO

    Audacity Documentation: When not playing audio, moves the editing cursor one second left by default. When playing audio, moves the playback cursor one second left by default. The default value can be changed by adjusting the "Short Period" under "Seek Time when playing" in Playback Preferences.
    """
    return do("CursorShortJumpLeft")


def cursor_short_jump_right():
    # type: () -> str
    """TODO

    Audacity Documentation: When not playing audio, moves the editing cursor one second right by default. When playing audio, moves the playback cursor one second right by default. The default value can be changed by adjusting the "Short Period" under "Seek Time when playing" in Playback Preferences.
    """
    return do("CursorShortJumpRight")


def cursor_long_jump_left():
    # type: () -> str
    """TODO

    Audacity Documentation: When not playing audio, moves the editing cursor 15 seconds left by default. When playing audio, moves the playback cursor 15 seconds left by default. The default value can be changed by adjusting the "Long Period" under "Seek Time when playing" in Playback Preferences.
    """
    return do("CursorLongJumpLeft")


def cursor_long_jump_right():
    # type: () -> str
    """TODO

    Audacity Documentation: When not playing audio, moves the editing cursor 15 seconds right by default. When playing audio, moves the playback cursor 15 seconds right by default. The default value can be changed by adjusting the "Long Period" under "Seek Time when playing" in Playback Preferences.
    """
    return do("CursorLongJumpRight")


def clip_left():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the currently focused audio track (or a separate clip in that track which contains the editing cursor or selection region) one screen pixel to left.
    """
    return do("ClipLeft")


def clip_right():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the currently focused audio track (or a separate clip in that track which contains the editing cursor or selection region) one screen pixel to right.
    """
    return do("ClipRight")


def track_pan():
    # type: () -> str
    """TODO

    Audacity Documentation: Brings up the Pan dialog for the focused track where you can enter a pan value, or use the slider for finer control of panning than is available when using the track pan slider.
    """
    return do("TrackPan")


def track_pan_left():
    # type: () -> str
    """TODO

    Audacity Documentation: Controls the pan slider on the focused track. Each keypress changes the pan value by 10% left.
    """
    return do("TrackPanLeft")


def track_pan_right():
    # type: () -> str
    """TODO

    Audacity Documentation: Controls the pan slider on the focused track. Each keypress changes the pan value by 10% right.
    """
    return do("TrackPanRight")


def track_gain():
    # type: () -> str
    """TODO

    Audacity Documentation: Brings up the Gain dialog for the focused track where you can enter a gain value, or use the slider for finer control of gain than is available when using the track pan slider.
    """
    return do("TrackGain")


def track_gain_inc():
    # type: () -> str
    """TODO

    Audacity Documentation: Controls the gain slider on the focused track. Each keypress increases the gain value by 1 dB.
    """
    return do("TrackGainInc")


def track_gain_dec():
    # type: () -> str
    """TODO

    Audacity Documentation: Controls the gain slider on the focused track. Each keypress decreases the gain value by 1 dB.
    """
    return do("TrackGainDec")


def track_menu():
    # type: () -> str
    """TODO

    Audacity Documentation: Opens the Audio Track Dropdown Menu on the focused audio track or other track type. In the audio track dropdown, use Up, and Down, arrow keys to navigate the menu and Enter, to select a menu item. Use Right, arrow to open the "Set Sample Format" and "Set Rate" choices or Left, arrow to leave those choices.
    """
    return do("TrackMenu")


def track_mute():
    # type: () -> str
    """TODO

    Audacity Documentation: Toggles the Mute button on the focused track."""
    return do("TrackMute")


def track_solo():
    # type: () -> str
    """TODO

    Audacity Documentation: Toggles the Solo button on the focused track."""
    return do("TrackSolo")


def track_close():
    # type: () -> str
    """TODO

    Audacity Documentation: Close (remove) the focused track only."""
    return do("TrackClose")


def track_move_up():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the focused track up by one track and moves the focus there.
    """
    return do("TrackMoveUp")


def track_move_down():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the focused track down by one track and moves the focus there.
    """
    return do("TrackMoveDown")


def track_move_top():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the focused track up to the top of the track table and moves the focus there.
    """
    return do("TrackMoveTop")


def track_move_bottom():
    # type: () -> str
    """TODO

    Audacity Documentation: Moves the focused track down to the bottom of the track table and moves the focus there.
    """
    return do("TrackMoveBottom")


def select_time(start=None, end=None, relative_to=None):
    # type: (Optional[float], Optional[float], Optional[str]) -> str
    """TODO

    Audacity Documentation: Modifies the temporal selection. Start and End are time. FromEnd allows selection from the end, which is handy to fade in and fade out a track.
    """

    if not isinstance(start, (type(None), float, int)):
        raise PyAudacityException(
            "start argument must be float or int, not " + str(type(start))
        )
    if not isinstance(end, (type(None), float, int)):
        raise PyAudacityException(
            "end argument must be float or int, not " + str(type(end))
        )
    if not isinstance(relative_to, (type(None), str)):
        raise PyAudacityException(
            "relative_to argument must be str, not " + str(type(relative_to))
        )

    # TODO check relative_to argument

    # Only include arguments if they are not None. (If they are none, then the selection is "unchanged" according to the documentation.)
    macro_arguments = []
    if start is not None:
        macro_arguments.append('Start="{}"'.format(start))
    if end is not None:
        macro_arguments.append('End="{}"'.format(end))
    if relative_to is not None:
        macro_arguments.append('RelativeTo="{}"'.format(relative_to))

    return do("SelectTime: " + " ".join(macro_arguments))


def select_frequencies(high=None, low=None):
    # type: (Optional[float], Optional[float]) -> str
    """TODO

    Audacity Documentation: Modifies what frequencies are selected. High and Low are for spectral selection.
    """

    if not isinstance(high, (type(None), float, int)):
        raise PyAudacityException(
            "high argument must be float or int, not " + str(type(high))
        )
    if not isinstance(low, (type(None), float, int)):
        raise PyAudacityException(
            "low argument must be float or int, not " + str(type(low))
        )

    # Only include arguments if they are not None. (If they are none, then the selection is "unchanged" according to the documentation.)
    macro_arguments = []
    if high is not None:
        macro_arguments.append('High="{}"'.format(high))
    if low is not None:
        macro_arguments.append('Low="{}"'.format(low))

    return do("SelectFrequencies: " + " ".join(macro_arguments))


def select_tracks():
    """TODO

    Audacity Documentation: Modifies which tracks are selected. First and Last are track numbers. High and Low are for spectral selection. The Mode parameter allows complex selections, e.g adding or removing tracks from the current selection.
    """
    raise NotImplementedError


def set_track_status():
    """TODO

    Audacity Documentation: Sets properties for a track or channel (or both).Name is used to set the name. It is not used in choosing the track.
    """
    raise NotImplementedError


def set_track_audio():
    """TODO

    Audacity Documentation: Sets properties for a track or channel (or both). Can set pan, gain, mute and solo.
    """
    raise NotImplementedError


def set_track_visuals():
    """TODO

    Audacity Documentation: Sets visual properties for a track or channel (or both). SpectralPrefs=1 sets the track to use general preferences, SpectralPrefs=1 per track prefs. When using general preferences, SetPreferences can be used to change a preference and so affect display of the track.
    """
    raise NotImplementedError


def get_preference():
    """TODO

    Audacity Documentation: Gets a single preference setting."""
    raise NotImplementedError


def set_preference():
    """TODO

    Audacity Documentation: Sets a single preference setting. Some settings such as them changes require a reload (use Reload=1), but this takes time and slows down a script.
    """
    raise NotImplementedError


def set_clip():
    """TODO

    Audacity Documentation: Modify a clip by stating the track or channel a time within it. Color and start position can be set. Try to avoid overlapping clips, as Audacity will allow it, but does not like them.
    """
    raise NotImplementedError


def set_envelope():
    """TODO

    Audacity Documentation: Modify an envelope by specifying a track or channel and a time within it. You cannot yet delete individual envelope points, but can delete the whole envelope using Delete=1.
    """
    raise NotImplementedError


def set_label():
    """TODO

    Audacity Documentation: Modifies an existing label. You must give it the label number.
    """
    raise NotImplementedError


def set_project():
    """TODO

    Audacity Documentation: Sets the project window to a particular location and size. Can also change the caption - but that is cosmetic and may be overwritten again later by Audacity.
    """
    raise NotImplementedError


def select():
    """TODO

    Audacity Documentation: Selects audio. Start and End are time. First and Last are track numbers. High and Low are for spectral selection. FromEnd allows selection from the end, which is handy to fade in and fade out a track. The Mode parameter allows complex selections, e.g adding or removing tracks from the current selection.
    """
    raise NotImplementedError


def set_track():
    """TODO

    Audacity Documentation: Selects audio. Start and End are time. First and Last are track numbers. High and Low are for spectral selection. FromEnd allows selection from the end, which is handy to fade in and fade out a track. The Mode parameter allows complex selections, e.g adding or removing tracks from the current selection.
    """
    raise NotImplementedError


def get_info(info_type="Commands", format="JSON"):
    # type: (str, str) -> str
    """TODO

    Audacity Documentation: Gets information in a list in one of three formats."""

    if info_type.title() not in (
        "Commands",
        "Menus",
        "Preferences",
        "Tracks",
        "Clips",
        "Envelopes",
        "Labels",
        "Boxes",
    ):
        raise PyAudacityException(
            'info_type argument must be one of "Commands", "Menus", "Preferences", "Tracks", "Clips", "Envelopes", "Labels", or "Boxes"'
        )
    formats = "JSON LISP Brief".split()
    if format not in formats:
        raise PyAudacityException(
            "format argument must be one of"
            + ", ".join(['"' + f + '"' for f in formats[:-1]])
            + ', and "'
            + formats[-1]
            + '"'
        )

    return do('GetInfo: Type="{}" Format="{}"'.format(info_type, format))


def message(text="Some message"):
    # type: (str) -> str
    """TODO

    Audacity Documentation: Used in testing. Sends the Text string back to you."""

    if not isinstance(text, str):
        raise PyAudacityException(
            "message argument must be str, not " + str(type(text))
        )

    return do('Message: Text="{}"'.format(text))


def help():
    """TODO

    Audacity Documentation: This is an extract from GetInfo Commands, with just one command.
    """
    raise NotImplementedError


# The Import2 macro is used in import().
# def import2():
#    """Audacity Documentation: Imports from a file. The automation command uses a text box to get the file name rather than a normal file-open dialog."""
#    pass # TODO

# The Export2 macro is used in export().
# def export2():
#    """Audacity Documentation: Exports selected audio to a named file. This version of export has the full set of export options. However, a current limitation is that the detailed option settings are always stored to and taken from saved preferences. The net effect is that for a given format, the most recently used options for that format will be used. In the current implementation, NumChannels should be 1 (mono) or 2 (stereo)."""
#    pass # TODO

# The OpenProject2 macro is used in open().
# def open_project2():
#    """Audacity Documentation: Opens a project."""
#    pass # TODO

# The SaveProject2 macro is used in save().
# def save_project2():
#    """Audacity Documentation: Saves a project."""
#    pass # TODO


def drag():
    """TODO

    Audacity Documentation: Experimental command (called Drag in scripting) that moves the mouse. An Id can be used to move the mouse into a button to get the hover effect. Window names can be used instead. If To is specified, the command does a drag, otherwise just a hover.
    """
    raise NotImplementedError


def compare_audio():
    """TODO

    Audacity Documentation: Compares selected range on two tracks. Reports on the differences and similarities.
    """
    raise NotImplementedError


def quick_help():
    # type: () -> str
    """TODO

    Audacity Documentation: A brief version of help with some of the most essential information.
    """
    return do("QuickHelp")


def manual():
    # type: () -> str
    """TODO

    Audacity Documentation: Opens the manual in the default browser."""
    return do("Manual")


def updates():
    # type: () -> str
    """TODO

    Audacity Documentation: Checks online to see if this is the latest version of Audacity.
    """
    return do("Updates")


def about():
    # type: () -> str
    """TODO

    Audacity Documentation: Brings a dialog with information about Audacity, such as who wrote it, what features are enabled and the GNU GPL v2 license.
    """
    return do("About")


def device_info():
    # type: () -> str
    """TODO

    Audacity Documentation: Shows technical information about your detected audio device(s).
    """
    return do("DeviceInfo")


def midi_device_info():
    # type: () -> str
    """TODO

    Audacity Documentation: Shows technical information about your detected MIDI device(s).
    """
    return do("MidiDeviceInfo")


def log():
    # type: () -> str
    """TODO

    Audacity Documentation: Launches the "Audacity Log" window, the log is largely a debugging aid, having timestamps for each entry.
    """
    return do("Log")


def crash_report():
    # type: () -> str
    """TODO

    Audacity Documentation: Selecting this will generate a Debug report which could be useful in aiding the developers to identify bugs in Audacity or in third-party plugins.
    """
    return do("CrashReport")


def check_deps():
    # type: () -> str
    """TODO

    Audacity Documentation: Lists any WAV or AIFF audio files that your project depends on, and allows you to copy these files into the project.
    """
    return do("CheckDeps")


def prev_window():
    # type: () -> str
    """TODO

    Audacity Documentation: Navigates to the previous window."""
    return do("PrevWindow")


def next_window():
    # type: () -> str
    """TODO

    Audacity Documentation: Navigates to the next window."""
    return do("NextWindow")
