import math

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    DateField,
    EmailField,
    FloatField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    TimeField,
)
from wtforms.validators import DataRequired, InputRequired, Length, Optional, Regexp

from app.core.pace import parse_mmss


class LoginForm(FlaskForm):
    email = EmailField("E-mail", validators=[DataRequired()])
    password = PasswordField("Mot de passe", validators=[DataRequired()])


class EventForm(FlaskForm):
    name = StringField("Nom de l'événement", validators=[DataRequired(), Length(max=200)])
    date = DateField("Date", validators=[DataRequired()])


MMSS_VALIDATOR = Regexp(r"^\d{1,2}:[0-5]\d$", message="Format attendu : mm:ss (ex. 5:00).")


class CourseForm(FlaskForm):
    name = StringField("Nom de la course", validators=[DataRequired(), Length(max=100)])
    color = StringField(
        "Couleur",
        validators=[
            DataRequired(),
            Regexp(r"^#[0-9a-fA-F]{6}$", message="Couleur hexadécimale attendue, ex. #1d4ed8."),
        ],
        default="#1d4ed8",
    )
    start_time = TimeField("Heure de départ", validators=[DataRequired()])

    # Allures (§5) : facultatives à la création, requises pour lancer une simulation (P3).
    premier_allure_course = StringField(
        "Premier — allure course à pied (mm:ss / km)", validators=[Optional(), MMSS_VALIDATOR]
    )
    premier_allure_nage = StringField(
        "Premier — allure natation (mm:ss / 100 m)", validators=[Optional(), MMSS_VALIDATOR]
    )
    dernier_allure_course = StringField(
        "Dernier — allure course à pied (mm:ss / km)", validators=[Optional(), MMSS_VALIDATOR]
    )
    dernier_allure_nage = StringField(
        "Dernier — allure natation (mm:ss / 100 m)", validators=[Optional(), MMSS_VALIDATOR]
    )

    def validate(self, extra_validators=None) -> bool:
        if not super().validate(extra_validators=extra_validators):
            return False

        valid = True
        for discipline, premier_field, dernier_field in (
            ("course à pied", self.premier_allure_course, self.dernier_allure_course),
            ("natation", self.premier_allure_nage, self.dernier_allure_nage),
        ):
            if not premier_field.data or not dernier_field.data:
                continue
            if parse_mmss(premier_field.data) >= parse_mmss(dernier_field.data):
                premier_field.errors.append(
                    f"Le premier doit être plus rapide que le dernier ({discipline})."
                )
                valid = False

        return valid


FUSEAU_CHOICES = [
    ("legale", "Heure légale française (Europe/Paris)"),
    ("utc+1", "UTC+1 (fixe, sans heure d'été)"),
    ("utc", "UTC"),
]
# Défaut = heure légale, le fuseau de l'événement et de tout le reste de l'appli : avec UTC par
# défaut, une heure recopiée telle quelle sans toucher au champ était décalée de 2 h en été.
FUSEAU_DEFAUT = "legale"


class HauteurField(FloatField):
    """Hauteur d'eau en mètres. Accepte la virgule décimale (« 5,80 »), saisie naturelle en
    français et notation des tables SHOM — un FloatField brut la rejette."""

    MESSAGE_INVALIDE = "Hauteur invalide : un nombre en mètres est attendu (ex. 5,80)."

    def process_formdata(self, valuelist):
        if not valuelist:
            return
        self.data = None
        try:
            valeur = float(valuelist[0].strip().replace(",", "."))
        except ValueError as exc:
            raise ValueError(self.MESSAGE_INVALIDE) from exc
        if not math.isfinite(valeur):
            raise ValueError(self.MESSAGE_INVALIDE)
        self.data = valeur


class MareeReleveForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired(message="La date est requise.")])
    heure = TimeField("Heure", validators=[DataRequired(message="L'heure est requise.")])
    # InputRequired et non DataRequired : ce dernier rejette 0 (valeur « fausse » en Python),
    # alors qu'une basse mer à 0,00 m est une hauteur valide.
    hauteur_m = HauteurField(
        "Hauteur (m)", validators=[InputRequired(message="La hauteur est requise.")]
    )
    type = SelectField("Type", choices=[("pm", "Pleine mer"), ("bm", "Basse mer")])
    fuseau_source = SelectField(
        "Fuseau de la table source", choices=FUSEAU_CHOICES, default=FUSEAU_DEFAUT
    )


class MareeCsvForm(FlaskForm):
    fichier = FileField(
        "Fichier CSV (datetime;hauteur_m)",
        validators=[FileRequired(), FileAllowed(["csv"], "Fichier .csv attendu.")],
    )
    fuseau_source = SelectField(
        "Fuseau de la table source", choices=FUSEAU_CHOICES, default=FUSEAU_DEFAUT
    )


POI_TYPE_CHOICES = [
    ("ravitaillement", "Ravitaillement"),
    ("entree_eau", "Entrée dans l'eau"),
    ("sortie_eau", "Sortie de l'eau"),
    ("bouee", "Bouée directionnelle"),
]

COTE_PASSAGE_CHOICES = [
    ("", "—"),
    ("gauche", "À laisser à gauche"),
    ("droite", "À laisser à droite"),
]


class PoiForm(FlaskForm):
    type = SelectField("Type", choices=POI_TYPE_CHOICES)
    nom = StringField("Nom", validators=[DataRequired(), Length(max=100)])
    description = StringField("Description", validators=[Optional(), Length(max=300)])
    lat = FloatField("Latitude", validators=[DataRequired()])
    lon = FloatField("Longitude", validators=[DataRequired()])
    cote_passage = SelectField(
        "Côté de passage (bouées uniquement)", choices=COTE_PASSAGE_CHOICES, validators=[Optional()]
    )
    # Le choices réel (courses de l'événement) est fixé dans la route, avant validation.
    courses = SelectMultipleField("Course(s) concernée(s)", coerce=int, validators=[DataRequired()])

    def validate(self, extra_validators=None) -> bool:
        if not super().validate(extra_validators=extra_validators):
            return False
        if self.type.data == "bouee" and not self.cote_passage.data:
            self.cote_passage.errors.append("Le côté de passage est requis pour une bouée.")
            return False
        return True
