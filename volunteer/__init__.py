import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(test_config=None):
    #create and configure the app
    app = Flask(__name__, instance_relative_config=True) #creates Flask instance using __name__(name of current Python module)
    app.config.from_mapping(
        SECRET_KEY='dev',
        # DATABASE=os.path.join(app.instance_path, 'volunteer.sqlite'),
    )

    if test_config is None:
        #Load the instance config, if it exists when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        #Load the test config if passed in
        app.config.from_mapping(test_config)

    #Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.instance_path, "volunteer.sqlite")}'
    db.init_app(app)


    #a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    from . import auth
    app.register_blueprint(auth.bp)

    # from . import export
    # app.register_blueprint(export.bp)

    return app