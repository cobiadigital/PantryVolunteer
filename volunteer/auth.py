import functools

from flask import(
    current_app, Blueprint, flash, g, redirect, render_template, request, session, url_for
)
# from volunteer.db import get_db
from .models import User, TimeSheet
from volunteer import db
import datetime as dt
from datetime import timezone
import pytz
import os
import urllib
utc = pytz.utc
loc = pytz.timezone('US/Central')


bp = Blueprint('auth',__name__, url_prefix='/')

@bp.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        which_form = request.form['which_form']
        if which_form == 'login':
            phonenumber = request.form['phonenumber']
            error = None
            user = db.session.execute(db.select(User).filter_by(phonenumber=phonenumber)).scalar_one()
            if user is None:
                # error = 'Incorrect phonenumber.'
                session.clear()
                return redirect(url_for('auth.register', phonenumber=phonenumber))
            if error is None:
                session.clear()
                session['user_id'] = user.id
                user_id = user.id
                if user.check_in_state == 0:
                    user.check_in_state = 1
                    user.last_time_in = dt.datetime.now(tz=utc)
                    db.session.commit()
                    time_sheet = TimeSheet()
                    time_sheet.user_id = user.id
                    time_sheet.time_in = dt.datetime.now(tz=utc)
                    time_sheet.check_in_state = user.check_in_state
                    db.session.add(time_sheet)
                    db.session.commit()

                    # db.session.add(user)
                    # db.session.commit()
                    # db.execute(
                    #     "UPDATE user SET check_in_state = ?, last_time_in = current_timestamp WHERE ID = ?",
                    #     (1, user_id),
                    # )
                    # db.execute(
                    #     "INSERT INTO time_sheet (user_id, check_in_state, time_in) VALUES (?, ?, current_timestamp)",
                    #     (user_id, 1),
                    # )
                    # db.commit()
                    return redirect(url_for('auth.index'))

            flash(error)
        elif which_form == 'update_time':
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
            user = User()
            user.id = user_id
            last_time_in = time_in_utc_st
            last_time_out = time_out_utc_st
            db.sessions.update(user)
            time_sheet = TimeSheet()
            time_sheet.time_in = time_in_utc_st
            time_sheet.time_out = time_out_utc_st
            time_sheet.time_modified = dt.datetime.now(tz=utc)
            db.session.update(time_sheet).filter_by(user_id=user_id).order_by(TimeSheet.id.desc()).first()
            db.session.commit()
            return redirect(url_for('auth.index', time_in_loc=time_in_loc, time_out_loc=time_out_loc))

    if g.user:
        if g.user.check_in_state == 1:
            #time_in_utc = utc.localize(dt.datetime.strptime(g.user.last_time_in, '%Y-%m-%d %H:%M:%S'))
            time_in_utc = utc.localize(g.user.last_time_in)
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
                user = User()
                user.phonenumber = phonenumber
                user.honorific_prefix = honorific_prefix
                user.given_name = given_name
                user.family_name = family_name
                user.honorific_suffix = honorific_suffix
                user.pronouns = pronouns
                user.nickname = nickname
                user.email = email
                user.street_address = street_address
                user.postal_code = postal_code
                user.organization = organization
                user.check_in_state = 1
                user.last_time_in = dt.datetime.now(tz=utc)
                db.session.add(user)
                db.session.commit()

            except db.IntegrityError:
                error = f"Phone number {phonenumber} is already registered."
            else:
                user = db.session.execute(db.select(User).filter_by(phonenumber=phonenumber)).scalar_one()
                session['user_id'] = user['id']
                user_id = user['id']
                time_sheet = TimeSheet()
                time_sheet.user_id = user['id']
                time_sheet.check_in_state = 1
                time_sheet.time_in = dt.datetime.now(tz=utc)
                db.session.add(time_sheet)
                return redirect(url_for('auth.register'))
        flash(error)

    return render_template('auth/register.html')

@bp.route('/release', methods=('GET', 'POST'))
def release():
    user_id = g.user['id']
    if request.method == 'POST':
        #from POST png of signature canvas
        #signature = DataURI(request.form['signature'])
        signature_data = request.form['signature']

        # binary_data = a2b_base64(signature_data)
        sig_filename = "uploads/" + g.user['given_name'] + '_' + g.user['family_name'] + '_' + 'sig' + '_' + str(user_id) + '.svg'
        response = urllib.request.urlopen(signature_data)
        with open(os.path.join(current_app.instance_path, sig_filename), 'wb') as f:
            f.write(response.file.read())

        covid_immun = request.form['covid_immunization']
        error = None
        return render_template('auth/release_eval.html', signature=signature_data, covid_immun=covid_immun)
    else:
        return render_template('auth/release.html')


@bp.route('/checkout', methods=('GET', 'POST'))
def checkout():
    user_id = g.user.id
    time_now_loc = dt.datetime.now(tz=loc)

    if request.method == 'POST':
        checkout = request.form['checkout']
        user = db.session.execute(db.select(User).filter_by(id=user_id)).scalar_one()
        time_sheet = TimeSheet()
        if checkout == '0':
            user.check_in_state = checkout
            user.last_time_out = dt.datetime.now(tz=utc)
            db.session.update(user)
            time_sheet.check_in_state = checkout
            time_sheet.time_out = dt.datetime.now(tz=utc)
            db.session.update(time_sheet).filter_by(user_id=user_id).order_by(TimeSheet.id.desc()).first()
            db.session.commit()
            return redirect(url_for('auth.index'))
        elif checkout == '1':
            timeinsplittime = request.form['timeinsplittime']
            time_in_loc_st = request.form['time_in_loc']
            time_in_loc = loc.localize(
                dt.datetime.combine(dt.datetime.strptime(time_in_loc_st, '%Y-%m-%d').date(), dt.datetime.strptime(timeinsplittime, '%H:%M:%S').time()))
            time_in_utc = time_in_loc.astimezone(tz=utc)
            time_in_utc_st = dt.datetime.strftime(time_in_utc, '%Y-%m-%d %H:%M:%S')
            user.last_time_in = time_in_utc_st
            db.session.update(user)
            time_sheet.time_in = time_in_utc_st
            db.session.update(time_sheet).filter_by(user_id=user_id).order_by(TimeSheet.id.desc()).first()
            db.session.commit()
            return redirect(url_for('auth.checkout', time_in_loc=time_in_loc, time_now_loc=time_now_loc,))

    if g.user:
        time_in_utc = utc.localize(g.user.last_time_in)
        time_in_loc = time_in_utc.astimezone(tz=loc)
        return render_template('auth/checkout.html', time_in_loc=time_in_loc, time_now_loc=time_now_loc )
    return redirect(url_for('auth.index'))

@bp.route('/update_info', methods=('GET', 'POST'))
def update_info():
    if request.method == 'POST':
        user = User()
        user_id = g.user['id']
        user.phonenumber = request.form['tel-national']
        user.honorific_prefix = request.form['honorific-prefix']
        user.given_name = request.form['given-name']
        user.family_name = request.form['family-name']
        user.honorific_suffix = request.form['honorific-suffix']
        user.pronouns = request.form['pronouns']
        user.nickname = request.form['nickname']
        user.email = request.form['email']
        user.street_address = request.form['street-address']
        user.postal_code = request.form['postal-code']
        user.organization = request.form['organization']

        error = None
        if not user.phonenumber:
            error = 'Phone number is required.'
        elif not user.given_name:
            error = 'Your name is required.'
        elif not user.family_name:
            error = 'Your name is required.'
        elif not user.nickname:
            error = 'Your name is required.'
        elif error is not None:
            flash(error)
        else:
            db.session.update(user).filter_by(id=user_id)
            db.session.commit()
            return redirect(url_for('auth.index'))

    return render_template('auth/update_info.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        user = User()
        g.user = db.session.execute(db.select(User).filter_by(id=user_id)).scalar_one()

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