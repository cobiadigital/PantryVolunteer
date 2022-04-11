import functools

from flask import(
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash,generate_password_hash
from volunteer.db import get_db

bp = Blueprint('admin', __name__, url_prefix='/admin_items')

@bp.route('/', methods=('GET', 'POST'))
def index():
    user_id = session.get('user_id')
    if request.method == 'POST':
        username = request.form['username']
        # password = request.form['password']
        release = request.form['release']
        db = get_db()
        error = None
        db = get_db()
        db.execute(
            'UPDATE admin SET username = ?, release = ?, time_modified = current_timestamp'
            ' WHERE id = ?',
            (username, release, user_id,)
        )
        db.commit()
        return redirect(url_for('admin.index'))
    db = get_db()
    user_id = session.get('user_id')
    admin = db.execute(
        'SELECT * FROM admin WHERE id = ?', (user_id,)
    ).fetchone()

    return render_template('admin/index.html', admin=admin)


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    'INSERT INTO admin (username, password) VALUES (?, ?)',
                    (username, generate_password_hash(password),),
                )
                db.commit()
            except db.IntegrityError:
                error = f'User {username} is already registered.'
            else:
                error = redirect(url_for('admin.login'))

        flash(error)
    return render_template('admin/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM admin WHERE USERNAME = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('admin.index'))

        flash(error)

    return render_template('admin/login.html')

@bp.before_app_request
def load_logged_in_admin():
    admin_id = session.get('user_id')

    if admin_id is None:
        g.admin = None
    else:
        g.admin = get_db().execute(
            'SELECT * FROM admin WHERE id = ?', (admin_id,)
       ).fetchone()

