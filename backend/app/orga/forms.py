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
from wtforms.validators import DataRequired, Length, Optional, Regexp

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
    ("utc", "UTC"),
    ("utc+1", "UTC+1 (fixe, sans heure d'été)"),
    ("legale", "Heure légale française (Europe/Paris)"),
]


class MareeReleveForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired()])
    heure = TimeField("Heure", validators=[DataRequired()])
    hauteur_m = FloatField("Hauteur (m)", validators=[DataRequired()])
    type = SelectField("Type", choices=[("pm", "Pleine mer"), ("bm", "Basse mer")])
    fuseau_source = SelectField("Fuseau de la table source", choices=FUSEAU_CHOICES)


class MareeCsvForm(FlaskForm):
    fichier = FileField(
        "Fichier CSV (datetime;hauteur_m)",
        validators=[FileRequired(), FileAllowed(["csv"], "Fichier .csv attendu.")],
    )
    fuseau_source = SelectField("Fuseau de la table source", choices=FUSEAU_CHOICES)


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
