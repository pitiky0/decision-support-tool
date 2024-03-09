from flask_login import login_required

from app import db
import sqlalchemy as sa
from app.dictionary import bp
from app.models import Dictionary
from app.dictionary.forms import SearchForm, AddTerm, EditTerm
from flask import request, render_template, url_for, flash, redirect


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = SearchForm()
    if form.validate_on_submit():
        term = form.search.data
        active_terms = Dictionary.search(term=term)
    else:
        active_terms = Dictionary.get_all_active()
    return render_template('dictionary/index.html', title='dictionary', form=form, terms=active_terms)


@bp.route('/show-term/<string:term_id>')
@login_required
def show_term(term_id):
    term = Dictionary.query.filter_by(id=term_id).first()
    if term and not term.is_deleted:
        return render_template('dictionary/show_term.html', term=term)
    else:
        flash("Term not found!", "error")
        return redirect(url_for('dictionary.index'))

@bp.route('/add-term', methods=['GET', 'POST'])
# @login_required
def add_term():
    form = AddTerm()
    if form.validate_on_submit():
        term = form.term.data
        definition = form.definition.data

        # Use SQLAlchemy's query methods for efficient and secure database interactions
        existing_term = Dictionary.query.filter_by(term=term).first()

        if existing_term:
            if existing_term.is_deleted:
                existing_term.is_deleted = False
                existing_term.definition = definition
            else:
                flash('Term "' + term + '" already exists.', 'error')
                return render_template("dictionary/add_term.html", form=form, term=existing_term)
        else:
            # Create a new Dictionary object and add it to the database
            new_term = Dictionary(term=term, definition=definition)
            db.session.add(new_term)
        try:
            db.session.commit()
            flash('Term "' + term + '" added successfully.', 'success')
            return redirect(url_for('dictionary.index'))
        except Exception:
            db.session.rollback()
            flash('An error occurred while adding the term', 'error')
            return redirect(url_for('dictionary.add_term'))

    # Display the add term form on GET requests
    return render_template("dictionary/add_term.html", form=form)

@bp.route('/edit-term/<string:term_id>', methods = ['GET', 'POST'])
@login_required
def edit_term(term_id):
    form = EditTerm()
    term_to_edit = Dictionary.query.get(term_id)
    if form.validate_on_submit():
        try:
            term = form.term.data
            definition = form.definition.data

            existing_term = Dictionary.query.filter_by(term=term).first()

            if existing_term:
                if existing_term.is_deleted:
                    existing_term.is_deleted = False
                    existing_term.definition = definition
                else:
                    flash('Term "' + term + '" already exists.', 'error')
                    return redirect(url_for('dictionary.edit_term', term_id=term_id))

            # Use SQLAlchemy's session for safe updates
            term_to_edit.term = term
            term_to_edit.definition = definition
            db.session.commit()

            flash('Term "' + term + '" Updated', 'success')
            return redirect(url_for("dictionary.index"))  # Use the correct route name
        except Exception as e:
            flash('An error occurred: ' + str(e), 'error')
            return redirect(url_for("dictionary.edit_term", term_id=term_id))  # Redirect to the same edit page

    if term_to_edit is None or term_to_edit.is_deleted:
        flash('Term not found', 'error')
        return redirect(url_for("dictionary.index"))  # Use the correct route name

    return render_template("dictionary/edit_term.html", term=term_to_edit, form=form)


@bp.route("/delete-term/<string:term_id>", methods=['POST'])
@login_required
def delete_term(term_id):
    term = Dictionary.query.get(term_id)  # Fetch the term using SQLAlchemy

    if term and not term.is_deleted:
        term.is_deleted = True  # Set the 'is_deleted' flag to True
        db.session.commit()
        flash(f'Term "{term.term}" Deleted', 'warning')  # Use f-string for formatting
    else:
        flash('Unknown Term', 'error')

    return redirect(url_for("dictionary.index"))

