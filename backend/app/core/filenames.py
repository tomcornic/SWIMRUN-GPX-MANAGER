import re
import unicodedata
from dataclasses import dataclass

FILENAME_PATTERN = re.compile(
    r"^Course(?P<course>\d+)_Tron(?:c|ç)on(?P<troncon>\d+)_(?P<type>[A-Za-z]+)\.gpx$",
    re.IGNORECASE,
)

VALID_TYPES = {"run", "swim"}


class InvalidFilenameError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedFilename:
    course: int
    troncon: int
    type: str  # "run" ou "swim"


def parse_gpx_filename(filename: str) -> ParsedFilename:
    """Parse un nom de fichier `Course{N}_Tronçon{M}_{Run|Swim}.gpx`.

    Insensible à la casse, accepte `Tronçon` et `Troncon`. Le nom est normalisé
    en NFC avant le parsing car macOS encode parfois `ç` en NFD (c + cédille
    combinante), ce qui casse une regex naïve.
    """
    normalized = unicodedata.normalize("NFC", filename)
    match = FILENAME_PATTERN.match(normalized)
    if not match:
        raise InvalidFilenameError(
            f"Nom de fichier invalide : « {filename} ». "
            "Format attendu : Course{N}_Tronçon{M}_{Run|Swim}.gpx"
        )

    raw_type = match.group("type")
    type_ = raw_type.lower()
    if type_ not in VALID_TYPES:
        raise InvalidFilenameError(
            f"Type de tronçon inconnu dans « {filename} » : « {raw_type} » (attendu Run ou Swim)."
        )

    return ParsedFilename(
        course=int(match.group("course")),
        troncon=int(match.group("troncon")),
        type=type_,
    )
