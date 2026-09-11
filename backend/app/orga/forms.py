from flask_wtf import FlaskForm
from wtforms import DateField, EmailField, PasswordField, StringField, TimeField
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
