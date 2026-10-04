import os
from flask import Flask
from flask_login import LoginManager

from config import Config
from models import db, User

from routes.auth_routes import auth_bp
from routes.booking_routes import booking_bp
from routes.service_routes import service_bp
from routes.review_routes import review_bp
from routes.quiz_routes import quiz_bp
from routes.attendance_routes import attendance_bp
from routes.admin_routes import admin_bp
from routes.housekeeping_routes import housekeeping_bp
from routes.advanced_routes import advanced_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(service_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(housekeeping_bp)
    app.register_blueprint(advanced_bp)

    @app.route("/")
    def home():
        from flask import redirect, url_for
        return redirect(url_for("auth.login"))

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
