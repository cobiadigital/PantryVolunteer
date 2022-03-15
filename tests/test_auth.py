import pytest
from flask import g, session
from volunteer.db import get_db

def test_register(client, app):
    assert client.get('/register').status_code == 200
    response = client.post(
        '/register', data={'phonenumber': '2515558888', 'firstname': 'user5', 'lastname': 'last5', 'email': 'user5@email.com'}
    )
    assert 'http://127.0.0.1:5000/' == response.header['Location']

    with app.app_context():
        assert get_db().execute(
            "SELECT * FROM user WHERE phonenumber = '2515558888'",
            ).fetchone() is not None

@pytest.mark.parametrize(('phonenumber', 'firstname', 'lastname', 'email', 'message'), (
        ('','','','', b'Phone number is required.'),
        ('2515558888', '', '', '', b'First name is required.'),
        ('2515558888', 'user9', '', '', b'Last name is require'),
        ('2515558888', 'user9', 'last9', '', b'Email address is require'),
        ('2515556666', 'user9', 'last9', 'user9@email.com', b'Phone number is already used.'),
))
def test_register_validate_input(client, phonenumber, firstname, lastname, email, message):
    response = client.post(
        '/register',
        data={'phonenumber': phonenumber, 'firstname': firstname, 'lastname': lastname, 'email': email}
    )
    assert message in response.data


# def test_login(client, auth):
#     assert client.get('/').status_code == 200
#     response = auth.login()
#     assert response.header['Loation'] == 'http://127.0.0.1:5000/'
#
#     with client:
#         client.get('/')
#         assert session['user_id'] == 1
#         assert g.user['phonenumber'] == '2515556666'
#
#     @pytest.mark.parametrize(('phonenumber', 'firstname', 'lastname', 'email', 'message'),(
#
#     ))

def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert 'userid' not in session