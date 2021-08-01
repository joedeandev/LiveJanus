from os import environ

from flask import Flask

from livejanus import db, livejanus, livejanus_socketio

app = Flask(__name__)

app.register_blueprint(livejanus)


app.config["DEBUG"] = environ.get("DEBUG", False) is True
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["PREFERRED_URL_SCHEME"] = "https"
app.config["SECRET_KEY"] = environ.get("SECRET", "secretkey")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data/livejanus.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
app.app_context().push()
db.create_all()

livejanus_socketio.init_app(app)

if __name__ == "__main__":
    livejanus_socketio.run(app, host="127.0.0.1", port=8000)
