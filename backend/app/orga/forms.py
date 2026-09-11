from flask_wtf import FlaskForm
from wtforms import DateField, EmailField, PasswordField, StringField, TimeField
from wtforms.validators import DataRequired, Length, Regexp


class LoginForm(FlaskForm):
    email = EmailField("E-mail", validators=[DataRequired()])
    password = PasswordField("Mot de passe", validators=[DataRequired()])


class EventForm(FlaskForm):
    name = StringField("Nom de l'événement", validators=[DataRequired(), Length(max=200)])
    date = DateField("Date", validators=[DataRequired()])


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
