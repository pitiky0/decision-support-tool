from flask import render_template, redirect, url_for, send_file
from flask_login import login_required

from app.main import bp


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    return render_template('main/index.html')

@bp.route('/requests')
@login_required
def requests():
    return 'requests'

# @bp.route('/check-sap-availability')
@login_required
def sap():
    return 'check_sap_availability'

@bp.route('/change-engineer-formation')
@login_required
def formation():
    return render_template('formation.html', title='Change Engineer Formation')

@bp.route('/history')
@login_required
def history():
    return 'history'


@bp.route('/logo')
def logo():
       filename = "C:\\Users\\Ayoub\\Desktop\\microblog\\OAD-CP\\app\\static\\assets\\logo.png"
       return send_file(filename, mimetype='image/png')