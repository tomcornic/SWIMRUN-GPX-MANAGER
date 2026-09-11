import click
from flask import Flask

from app.extensions import db
from app.models import User


def register_cli(app: Flask) -> None:
    @app.cli.command("create-user")
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_user(email: str, password: str) -> None:
        """Crée un compte orga (pas d'inscription en ligne, voir §5 du cahier des charges)."""
        if User.query.filter_by(email=email).first() is not None:
            click.echo(f"Un compte existe déjà pour {email}.")
            return

        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Compte créé pour {email}.")
