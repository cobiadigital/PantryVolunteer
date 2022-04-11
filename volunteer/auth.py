import functools

from flask import(
    current_app, Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from volunteer.db import get_db
import datetime as dt
from datetime import timezone
import pytz
from xhtml2pdf import pisa
import os
import urllib
import svglib
utc = pytz.utc
loc = pytz.timezone('US/Central')


bp = Blueprint('auth',__name__, url_prefix='/')

@bp.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        which_form = request.form['which_form']
        if which_form == 'login':
            phonenumber = request.form['phonenumber']
            db = get_db()
            error = None
            user = db.execute(
                'SELECT * FROM user WHERE phonenumber = ?', (phonenumber,)
            ).fetchone()

            if user is None:
                # error = 'Incorrect phonenumber.'
                session.clear()
                return redirect(url_for('auth.register', phonenumber=phonenumber))

            if error is None:
                session.clear()
                session['user_id'] = user['id']
                user_id = user['id']
                if user['check_in_state'] == 0:
                    db.execute(
                        "UPDATE user SET check_in_state = ?, last_time_in = current_timestamp WHERE ID = ?",
                        (1, user_id),
                    )
                    db.execute(
                        "INSERT INTO time_sheet (user_id, check_in_state, time_in) VALUES (?, ?, current_timestamp)",
                        (user_id, 1),
                    )
                    db.commit()
                    return redirect(url_for('auth.index'))

            flash(error)
        elif which_form == 'update_time':
            db = get_db()
            user_id = g.user['id']

            timeinsplittime = request.form['timeinsplittime']
            time_in_loc_st = request.form['time_in_loc']
            time_in_loc = loc.localize(
                dt.datetime.combine(dt.datetime.strptime(time_in_loc_st, '%Y-%m-%d').date(),
                                    dt.datetime.strptime(timeinsplittime, '%H:%M:%S').time()))
            time_in_loc = loc.localize(
                dt.datetime.combine(dt.datetime.strptime(time_in_loc_st, '%Y-%m-%d').date(),
                                    dt.datetime.strptime(timeinsplittime, '%H:%M:%S').time()))
            time_in_utc = time_in_loc.astimezone(tz=utc)
            time_in_utc_st = dt.datetime.strftime(time_in_utc, '%Y-%m-%d %H:%M:%S')
            timeoutsplittime = request.form['timeoutsplittime']
            time_out_loc_st = request.form['time_out_loc']
            time_out_loc = loc.localize(
                 dt.datetime.combine(dt.datetime.strptime(time_out_loc_st, '%Y-%m-%d').date(),
                                dt.datetime.strptime(timeoutsplittime, '%H:%M:%S').time()))
            time_out_utc = time_out_loc.astimezone(tz=utc)
            time_out_utc_st = dt.datetime.strftime(time_out_utc, '%Y-%m-%d %H:%M:%S')
            db.execute(
                    "UPDATE user SET last_time_in = ?, last_time_out = ? WHERE id = ? ",
                    (time_in_utc_st, time_out_utc_st, user_id,),
                )
            db.execute(
                "UPDATE time_sheet SET time_in = ?, time_out = ?, time_modified = current_timestamp WHERE user_id = ? AND ID = (SELECT max(ID) FROM time_sheet) ",
                (time_in_utc_st, time_out_utc_st, user_id,),
            )
            db.commit()
            return redirect(url_for('auth.index', time_in_loc=time_in_loc, time_out_loc=time_out_loc))

    if g.user:
        if g.user['check_in_state']:
            time_in_utc = utc.localize(dt.datetime.strptime(g.user['last_time_in'], '%Y-%m-%d %H:%M:%S'))
            time_in_loc = time_in_utc.astimezone(tz=loc)
            return render_template('auth/index.html', time_in_loc=time_in_loc)
        else:
            time_in_utc = utc.localize(dt.datetime.strptime(g.user['last_time_in'], '%Y-%m-%d %H:%M:%S'))
            time_in_loc = time_in_utc.astimezone(tz=loc)
            time_out_utc = utc.localize(dt.datetime.strptime(g.user['last_time_out'], '%Y-%m-%d %H:%M:%S'))
            time_out_loc = time_out_utc.astimezone(tz=loc)
            return render_template('auth/index.html', time_in_loc=time_in_loc, time_out_loc=time_out_loc)

    else:
        return render_template('auth/index.html')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        phonenumber = request.form['tel-national']
        honorific_prefix = request.form['honorific-prefix']
        given_name = request.form['given-name']
        family_name = request.form['family-name']
        honorific_suffix = request.form['honorific-suffix']
        pronouns = request.form['pronouns']
        nickname = request.form['nickname']
        email = request.form['email']
        street_address = request.form['street-address']
        postal_code = request.form['postal-code']
        organization = request.form['organization']
        db = get_db()
        error = None

        if not phonenumber:
            error = 'Phone number is required.'
        elif not given_name:
            error = 'First Name is require.'
        elif not family_name:
            error = 'Last Name is required.'
        elif not nickname:
            error = 'Preferred Name is required.'

        if error is None:
            try:
                db.execute (
                    "INSERT INTO user (phonenumber, honorific_prefix, given_name, family_name, honorific_suffix, pronouns, nickname, email, street_address, postal_code, organization, check_in_state, last_time_in) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                    (phonenumber, honorific_prefix, given_name, family_name, honorific_suffix, pronouns, nickname, email, street_address, postal_code, organization, 1,)
                )
                db.commit()

            except db.IntegrityError:
                error = f"Phone number {phonenumber} is already registered."
            else:
                user = db.execute(
                    'SELECT * FROM user WHERE phonenumber = ?', (phonenumber,)
                ).fetchone()
                session['user_id'] = user['id']
                user_id = user['id']
                db.execute(
                    'INSERT INTO time_sheet (user_id, check_in_state, time_in) VALUES (?, ?, current_timestamp)',
                    (user_id, 1),
                )
                db.commit()

                return redirect(url_for('auth.release'))
        else:
            flash(error)

    return render_template('auth/register.html')

@bp.route('/release', methods=('GET', 'POST'))
def release():
    db = get_db()
    user_id = g.user['id']
    admin_items = db.execute(
        'SELECT release FROM admin WHERE id = ?', (1,)
    ).fetchone()
    if request.method == 'POST':
        signature_data = request.form['signature']
        covid_immun = request.form['covid_immunization']
        sign_date = request.form['date']
        sig_filename = "uploads/" + g.user['given_name'] + '_' + g.user['family_name'] + '_' + 'sig' + '_' + str(
            user_id) + '.svg'
        pdf_filename = "uploads/" + g.user['given_name'] + '_' + g.user['family_name'] + '_' + 'release' + '_' + str(
            user_id) + '.pdf'

        response = urllib.request.urlopen(signature_data)
        with open(os.path.join(current_app.instance_path, sig_filename), 'wb') as f:
            f.write(response.file.read())
        sig_location = os.path.join(current_app.instance_path, sig_filename)
        html = render_template('auth/release_print.html', admin_items=admin_items, signature=sig_location, date=sign_date)
        result_file = open(os.path.join(current_app.instance_path, pdf_filename), "w+b")
        pdf = pisa.CreatePDF(src=html, dest=result_file)
        result_file.close()
        if pdf.err:
            return pdf.err

        #from POST png of signature canvas
        #signature = DataURI(request.form['signature'])

        # binary_data = a2b_base64(signature_data)
        error = None
        return render_template('auth/release_eval.html', admin_items=admin_items, signature=signature_data, date=sign_date, covid_immun=covid_immun)
        # return render_template('auth/release_print.html',  admin_items=admin_items, signature=signature_data, date=sign_date, covid_immun=covid_immun)

    else:
        return render_template('auth/release.html', admin_items=admin_items)

@bp.route('/checkout', methods=('GET', 'POST'))
def checkout():
    user_id = g.user['id']
    time_now_loc = dt.datetime.now(tz=loc)

    if request.method == 'POST':
        checkout = request.form['checkout']
        db = get_db()
        if checkout == '0':
            db.execute(
                "UPDATE user SET check_in_state = ?, last_time_out = current_timestamp WHERE id = ? ",
                (checkout, user_id),
            )
            db.execute(
                "UPDATE time_sheet SET check_in_state = ?, time_out = current_timestamp WHERE user_id = ? AND ID = (SELECT max(ID) FROM time_sheet) ",
                (checkout, user_id,),
            )
            db.commit()
            return redirect(url_for('auth.index'))
        elif checkout == '1':
            timeinsplittime = request.form['timeinsplittime']
            time_in_loc_st = request.form['time_in_loc']
            time_in_loc = loc.localize(
                dt.datetime.combine(dt.datetime.strptime(time_in_loc_st, '%Y-%m-%d').date(), dt.datetime.strptime(timeinsplittime, '%H:%M:%S').time()))
            time_in_utc = time_in_loc.astimezone(tz=utc)
            time_in_utc_st = dt.datetime.strftime(time_in_utc, '%Y-%m-%d %H:%M:%S')
            db.execute(
                "UPDATE user SET last_time_in = ? WHERE id = ? ",
                (time_in_utc_st, user_id),
            )
            db.execute(
                "UPDATE time_sheet SET time_in = ? WHERE user_id = ? AND ID = (SELECT max(ID) FROM time_sheet) ",
                (time_in_utc_st, user_id,),
            )
            db.commit()

            return redirect(url_for('auth.checkout', time_in_loc=time_in_loc, time_now_loc=time_now_loc,))

    if g.user:
        time_in_utc = utc.localize(dt.datetime.strptime(g.user['last_time_in'], '%Y-%m-%d %H:%M:%S'))
        time_in_loc = time_in_utc.astimezone(tz=loc)
        return render_template('auth/checkout.html', time_in_loc=time_in_loc, time_now_loc=time_now_loc )
    return redirect(url_for('auth.index'))

@bp.route('/update_info', methods=('GET', 'POST'))
def update_info():
    if request.method == 'POST':
        user_id = g.user['id']
        phonenumber = request.form['tel-national']
        honorific_prefix = request.form['honorific-prefix']
        given_name = request.form['given-name']
        family_name = request.form['family-name']
        honorific_suffix = request.form['honorific-suffix']
        pronouns = request.form['pronouns']
        nickname = request.form['nickname']
        email = request.form['email']
        street_address = request.form['street-address']
        postal_code = request.form['postal-code']
        organization = request.form['organization']

        db = get_db()

        error = None
        if not phonenumber:
            error = 'Phone number is required.'
        elif not given_name:
            error = 'Your name is required.'
        elif not family_name:
            error = 'Your name is required.'
        elif not nickname:
            error = 'Your name is required.'
        elif error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE user SET phonenumber = ?, honorific_prefix = ?, given_name = ?, family_name = ?, honorific_suffix = ?, pronouns = ?, nickname = ?, email = ?, street_address = ?, postal_code = ?, organization = ?, account_updated = current_timestamp'
                ' WHERE id = ?',
                (phonenumber, honorific_prefix, given_name, family_name, honorific_suffix, pronouns, nickname, email, street_address, postal_code, organization, user_id,)
            )
            db.commit()
            return redirect(url_for('auth.index'))

    return render_template('auth/update_info.html')



@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.index'))

        return view(**kwargs)

    return wrapped_view