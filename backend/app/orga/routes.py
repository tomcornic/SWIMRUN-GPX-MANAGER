import json
import shutil
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.core.gpx_import import (
    CourseAssemblyResult,
    TronconImportResult,
    assemble_course,
    import_troncon_file,
)
from app.core.pace import format_mmss, parse_mmss
from app.core.tides import (
    CsvMareeInvalideError,
    PointMaree,
    convertir_vers_utc,
    echantillonner,
    parser_csv,
)
from app.extensions import db
from app.models import Course, Event, MareeReleve, Troncon, User
from app.orga import bp
from app.orga.forms import CourseForm, EventForm, LoginForm, MareeCsvForm, MareeReleveForm

MAX_COURSES_PER_EVENT = 3

PACE_FIELDS = (
    ("premier_allure_course", "premier_allure_course_s"),
    ("premier_allure_nage", "premier_allure_nage_s"),
    ("dernier_allure_course", "dernier_allure_course_s"),
    ("dernier_allure_nage", "dernier_allure_nage_s"),
)


def _fill_pace_fields(form: CourseForm, course: Course) -> None:
    for form_field_name, model_field_name in PACE_FIELDS:
        seconds = getattr(course, model_field_name)
        if seconds is not None:
            getattr(form, form_field_name).data = format_mmss(seconds)


def _save_pace_fields(course: Course, form: CourseForm) -> None:
    for form_field_name, model_field_name in PACE_FIELDS:
        value = getattr(form, form_field_name).data
        setattr(course, model_field_name, parse_mmss(value) if value else None)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("orga.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user)
            return redirect(request.args.get("next") or url_for("orga.index"))
        flash("E-mail ou mot de passe incorrect.", "error")

    return render_template("orga/login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("orga.login"))


@bp.route("/")
@login_required
def index():
    event = Event.query.first()
    courses = event.courses if event else []
    courses_json = json.dumps([{"id": c.id, "name": c.name, "color": c.color} for c in courses])
    return render_template(
        "orga/index.html", event=event, courses=courses, courses_json=courses_json
    )


@bp.route("/evenement", methods=["GET", "POST"])
@login_required
def evenement():
    event = Event.query.first()
    form = EventForm(obj=event)
    if form.validate_on_submit():
        if event is None:
            event = Event(name=form.name.data, date=form.date.data)
            db.session.add(event)
        else:
            event.name = form.name.data
            event.date = form.date.data
        db.session.commit()
        flash("Événement enregistré.", "success")
        return redirect(url_for("orga.evenement"))
    return render_template("orga/evenement.html", form=form, event=event)


@bp.route("/courses")
@login_required
def courses_liste():
    event = Event.query.first()
    courses = event.courses if event else []
    return render_template(
        "orga/courses_liste.html", courses=courses, event=event, max_courses=MAX_COURSES_PER_EVENT
    )


@bp.route("/courses/nouvelle", methods=["GET", "POST"])
@login_required
def course_nouvelle():
    event = Event.query.first()
    if event is None:
        flash("Configurez d'abord l'événement avant de créer une course.", "error")
        return redirect(url_for("orga.evenement"))

    if len(event.courses) >= MAX_COURSES_PER_EVENT:
        flash(f"Maximum {MAX_COURSES_PER_EVENT} courses simultanées.", "error")
        return redirect(url_for("orga.courses_liste"))

    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            event_id=event.id,
            name=form.name.data,
            color=form.color.data,
            start_time=form.start_time.data,
        )
        _save_pace_fields(course, form)
        db.session.add(course)
        db.session.commit()
        flash(f"Course « {course.name} » créée.", "success")
        return redirect(url_for("orga.courses_liste"))

    return render_template("orga/course_form.html", form=form, course=None)


@bp.route("/courses/<int:course_id>/modifier", methods=["GET", "POST"])
@login_required
def course_modifier(course_id: int):
    course = db.get_or_404(Course, course_id)
    form = CourseForm(obj=course)
    if request.method == "GET":
        _fill_pace_fields(form, course)
    if form.validate_on_submit():
        course.name = form.name.data
        course.color = form.color.data
        course.start_time = form.start_time.data
        _save_pace_fields(course, form)
        db.session.commit()
        flash(f"Course « {course.name} » mise à jour.", "success")
        return redirect(url_for("orga.courses_liste"))
    return render_template("orga/course_form.html", form=form, course=course)


@bp.route("/courses/<int:course_id>/supprimer", methods=["POST"])
@login_required
def course_supprimer(course_id: int):
    course = db.get_or_404(Course, course_id)
    name = course.name
    db.session.delete(course)
    db.session.commit()
    flash(f"Course « {name} » supprimée.", "success")
    return redirect(url_for("orga.courses_liste"))


def _upload_dir(course_id: int) -> Path:
    return Path(current_app.config["UPLOADS_DIR"]) / f"course_{course_id}"


def _run_import_preview(course_id: int) -> tuple[list[TronconImportResult], CourseAssemblyResult]:
    """Importe tous les GPX en attente pour cette course et les assemble.

    Le numéro de course dans le nom de fichier (`Course{N}_...`) ne sert qu'à
    documenter d'où vient le fichier côté organisateur : l'appartenance réelle
    à une course est déterminée par le dossier d'upload (scopé par course_id),
    donc on force `result.course` avant l'assemblage. Sans ça, un fichier au
    nom invalide (course non extraite, donc `None`) serait silencieusement
    exclu du contrôle d'assemble_course au lieu de faire échouer l'import.
    """
    upload_dir = _upload_dir(course_id)
    results = []
    for path in sorted(upload_dir.glob("*.gpx")):
        result = import_troncon_file(path.name, path.read_text())
        result.course = course_id
        results.append(result)
    return results, assemble_course(course_id, results)


@bp.route("/courses/<int:course_id>/import", methods=["GET", "POST"])
@login_required
def course_import(course_id: int):
    course = db.get_or_404(Course, course_id)

    if request.method == "POST":
        files = [f for f in request.files.getlist("fichiers") if f.filename]
        if not files:
            flash("Sélectionnez au moins un fichier GPX.", "error")
            return redirect(url_for("orga.course_import", course_id=course.id))

        upload_dir = _upload_dir(course.id)
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
        upload_dir.mkdir(parents=True)
        for f in files:
            f.save(upload_dir / f.filename)

        return redirect(url_for("orga.course_import_apercu", course_id=course.id))

    return render_template("orga/import.html", course=course)


@bp.route("/courses/<int:course_id>/import/apercu")
@login_required
def course_import_apercu(course_id: int):
    course = db.get_or_404(Course, course_id)
    upload_dir = _upload_dir(course.id)
    if not upload_dir.exists() or not any(upload_dir.glob("*.gpx")):
        flash("Aucun fichier en attente : importez d'abord des GPX.", "error")
        return redirect(url_for("orga.course_import", course_id=course.id))

    troncon_results, assembly = _run_import_preview(course.id)
    return render_template(
        "orga/import_apercu.html",
        course=course,
        troncon_results=troncon_results,
        assembly=assembly,
    )


@bp.route("/courses/<int:course_id>/import/valider", methods=["POST"])
@login_required
def course_import_valider(course_id: int):
    course = db.get_or_404(Course, course_id)
    upload_dir = _upload_dir(course.id)
    if not upload_dir.exists():
        flash("Aucun import en attente pour cette course.", "error")
        return redirect(url_for("orga.course_import", course_id=course.id))

    troncon_results, assembly = _run_import_preview(course.id)
    if assembly.status == "erreur":
        flash("Import refusé : des erreurs restent à corriger.", "error")
        return redirect(url_for("orga.course_import_apercu", course_id=course.id))

    Troncon.query.filter_by(course_id=course.id).delete()
    by_number = {
        result.troncon: result
        for result in troncon_results
        if result.status != "erreur" and result.troncon is not None
    }
    for number, result in by_number.items():
        troncon = Troncon(
            course_id=course.id,
            number=number,
            type=result.type,
            filename=result.filename,
            length_m=result.length_m,
        )
        troncon.points = result.points
        db.session.add(troncon)
    db.session.commit()

    shutil.rmtree(upload_dir)
    flash(f"{len(by_number)} tronçon(s) importé(s) pour « {course.name} ».", "success")
    return redirect(url_for("orga.index"))


@bp.route("/courses/<int:course_id>/trace.geojson")
@login_required
def course_trace_geojson(course_id: int):
    course = db.get_or_404(Course, course_id)
    coordinates: list[list[float]] = []
    for troncon in course.troncons:
        coordinates.extend([lon, lat] for lat, lon in troncon.points)

    return jsonify(
        {
            "type": "Feature",
            "properties": {"course_id": course.id, "name": course.name, "color": course.color},
            "geometry": {"type": "LineString", "coordinates": coordinates},
        }
    )


@bp.route("/courses/<int:course_id>/simulation.json")
@login_required
def course_simulation_json(course_id: int):
    course = db.get_or_404(Course, course_id)

    coordinates: list[list[float]] = []
    for troncon in course.troncons:
        coordinates.extend([lon, lat] for lat, lon in troncon.points)

    allures = None
    paces = (
        course.premier_allure_course_s,
        course.premier_allure_nage_s,
        course.dernier_allure_course_s,
        course.dernier_allure_nage_s,
    )
    if all(p is not None for p in paces):
        allures = {
            "premier": {"course_s_par_km": paces[0], "nage_s_par_100m": paces[1]},
            "dernier": {"course_s_par_km": paces[2], "nage_s_par_100m": paces[3]},
        }

    return jsonify(
        {
            "id": course.id,
            "nom": course.name,
            "couleur": course.color,
            "heure_depart": course.start_time.isoformat(),
            "troncons": [
                {"numero": t.number, "type": t.type, "longueur_m": t.length_m}
                for t in course.troncons
            ],
            "allures": allures,
            "trace": {"type": "LineString", "coordinates": coordinates},
        }
    )


def _flash_form_errors(form) -> None:
    for field_errors in form.errors.values():
        for error in field_errors:
            flash(error, "error")


@bp.route("/maree")
@login_required
def maree():
    event = Event.query.first()
    releves = event.releves_maree if event else []
    return render_template(
        "orga/maree.html",
        event=event,
        releves=releves,
        releve_form=MareeReleveForm(),
        csv_form=MareeCsvForm(),
    )


@bp.route("/maree/ajouter", methods=["POST"])
@login_required
def maree_ajouter():
    event = Event.query.first()
    if event is None:
        flash("Configurez d'abord l'événement.", "error")
        return redirect(url_for("orga.evenement"))

    form = MareeReleveForm()
    if form.validate_on_submit():
        moment_naif = datetime.combine(form.date.data, form.heure.data)
        moment_utc = convertir_vers_utc(moment_naif, form.fuseau_source.data)
        releve = MareeReleve(
            event_id=event.id,
            moment_utc=moment_utc,
            hauteur_m=form.hauteur_m.data,
            type=form.type.data,
        )
        db.session.add(releve)
        db.session.commit()
        flash("Point de marée ajouté.", "success")
    else:
        _flash_form_errors(form)

    return redirect(url_for("orga.maree"))


@bp.route("/maree/importer-csv", methods=["POST"])
@login_required
def maree_importer_csv():
    event = Event.query.first()
    if event is None:
        flash("Configurez d'abord l'événement.", "error")
        return redirect(url_for("orga.evenement"))

    form = MareeCsvForm()
    if not form.validate_on_submit():
        _flash_form_errors(form)
        return redirect(url_for("orga.maree"))

    contenu = form.fichier.data.read().decode("utf-8")
    try:
        lignes = parser_csv(contenu)
    except CsvMareeInvalideError as exc:
        flash(str(exc), "error")
        return redirect(url_for("orga.maree"))

    MareeReleve.query.filter_by(event_id=event.id, type="mesure").delete()
    for moment_naif, hauteur in lignes:
        moment_utc = convertir_vers_utc(moment_naif, form.fuseau_source.data)
        db.session.add(
            MareeReleve(event_id=event.id, moment_utc=moment_utc, hauteur_m=hauteur, type="mesure")
        )
    db.session.commit()
    flash(f"{len(lignes)} mesure(s) importée(s).", "success")
    return redirect(url_for("orga.maree"))


@bp.route("/maree/<int:releve_id>/supprimer", methods=["POST"])
@login_required
def maree_supprimer(releve_id: int):
    releve = db.get_or_404(MareeReleve, releve_id)
    db.session.delete(releve)
    db.session.commit()
    flash("Point de marée supprimé.", "success")
    return redirect(url_for("orga.maree"))


def _seconds_since_local_midnight(event_date, moment_utc: datetime) -> float:
    moment_local = moment_utc.astimezone(ZoneInfo("Europe/Paris"))
    minuit_local = datetime.combine(event_date, time.min, tzinfo=ZoneInfo("Europe/Paris"))
    return (moment_local - minuit_local).total_seconds()


@bp.route("/maree/serie.json")
@login_required
def maree_serie_json():
    event = Event.query.first()
    if event is None:
        return jsonify({"serie": [], "extremes": []})

    try:
        debut_s = int(request.args.get("debut_s", "0"))
        fin_s = int(request.args.get("fin_s", "0"))
    except ValueError:
        return jsonify({"error": "debut_s et fin_s doivent être des entiers."}), 400

    minuit_naif = datetime.combine(event.date, time.min)
    debut_utc = convertir_vers_utc(minuit_naif + timedelta(seconds=debut_s), "legale")
    fin_utc = convertir_vers_utc(minuit_naif + timedelta(seconds=fin_s), "legale")

    points = [
        PointMaree(moment=r.moment_utc.replace(tzinfo=timezone.utc), hauteur_m=r.hauteur_m)
        for r in event.releves_maree
    ]
    serie = echantillonner(points, debut_utc, fin_utc)
    extremes = [r for r in event.releves_maree if r.type in ("pm", "bm")]

    return jsonify(
        {
            "serie": [
                {
                    "secondes": _seconds_since_local_midnight(event.date, p.moment),
                    "hauteur_m": p.hauteur_m,
                }
                for p in serie
            ],
            "extremes": [
                {
                    "secondes": _seconds_since_local_midnight(
                        event.date, r.moment_utc.replace(tzinfo=timezone.utc)
                    ),
                    "hauteur_m": r.hauteur_m,
                    "type": r.type,
                }
                for r in extremes
            ],
        }
    )
