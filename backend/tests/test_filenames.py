import unicodedata

import pytest

from app.core.filenames import InvalidFilenameError, ParsedFilename, parse_gpx_filename


def test_parses_standard_name_with_cedilla():
    assert parse_gpx_filename("Course1_Tronçon1_Run.gpx") == ParsedFilename(
        course=1, troncon=1, type="run"
    )


def test_parses_ascii_troncon_spelling():
    assert parse_gpx_filename("Course2_Troncon3_Swim.gpx") == ParsedFilename(
        course=2, troncon=3, type="swim"
    )


def test_is_case_insensitive():
    assert parse_gpx_filename("course1_troncon1_SWIM.GPX") == ParsedFilename(
        course=1, troncon=1, type="swim"
    )


def test_handles_nfd_normalized_cedilla_from_macos():
    nfd_name = unicodedata.normalize("NFD", "Course1_Tronçon2_Run.gpx")
    # Confirme que le NFD change bien la représentation binaire du nom.
    assert nfd_name != "Course1_Tronçon2_Run.gpx"
    assert parse_gpx_filename(nfd_name) == ParsedFilename(course=1, troncon=2, type="run")


def test_rejects_malformed_name():
    with pytest.raises(InvalidFilenameError, match="invalide"):
        parse_gpx_filename("parcours_final.gpx")


def test_rejects_wrong_extension():
    with pytest.raises(InvalidFilenameError):
        parse_gpx_filename("Course1_Tronçon1_Run.txt")


def test_rejects_unknown_type():
    with pytest.raises(InvalidFilenameError, match="inconnu"):
        parse_gpx_filename("Course1_Tronçon1_Bike.gpx")
