import functools

from flask import(
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from volunteer.db import get_db
import datetime as dt
from datetime import timezone
import pytz


utc = pytz.utc
loc = pytz.timezone('US/Central')


bp = Blueprint('auth',__name__, url_prefix='/')

@bp.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        phonenumber = request.form['phonenumber']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE phonenumber = ?', (phonenumber,)
        ).fetchone()

        if user is None:
            # error = 'Incorrect phonenumber.'
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

    if g.user:
        if g.user['check_in_state']:
            time_in_loc = utc.localize(dt.datetime.strptime(g.user['last_time_in'], '%Y-%m-%d %H:%M:%S')).astimezone(tz=loc)
            return render_template('auth/index.html', time_in_loc=time_in_loc)
        else:
            time_in_loc = utc.localize(dt.datetime.strptime(g.user['last_time_in'], '%Y-%m-%d %H:%M:%S')).astimezone(tz=loc)
            time_out_loc = utc.localize(dt.datetime.strptime(g.user['last_time_out'], '%Y-%m-%d %H:%M:%S')).astimezone(tz=loc)
            return render_template('auth/index.html', time_in_loc=time_in_loc, time_out_loc=time_out_loc)

    else:
        return render_template('auth/index.html')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        phonenumber = request.form['phonenumber']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        db = get_db()
        error = None

        if not phonenumber:
            error = 'Phone number is required.'
        elif not firstname:
            error = 'First name is require.'
        elif not lastname:
            error = 'Last name is required.'

        if error is None:
            try:
                db.execute (
                    "INSERT INTO user (phonenumber, firstname, lastname, email, check_in_state, last_time_in) VALUES (?,?,?,?,?, CURRENT_TIMESTAMP)",
                    (phonenumber, firstname, lastname, email, 1,)
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
                return redirect(url_for("auth.index"))
        flash(error)

    return render_template('auth/register.html')

@bp.route('/checkout', methods=('GET', 'POST'))
def checkout():
    user_id = g.user['id']
    if request.method == 'POST':
        checkout = request.form['checkout']
        db = get_db()
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
    if g.user:
        time_in_loc = utc.localize(dt.datetime.strptime(g.user['last_time_in'], '%Y-%m-%d %H:%M:%S')).astimezone(tz=loc)
        time_now_loc = dt.datetime.now(tz=loc)
        return render_template('auth/checkout.html', time_in_loc=time_in_loc, time_now_loc=time_now_loc )
    return redirect(url_for('auth.index'))

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()
        last_time_in = g.user['last_time_in']

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