from flask import Flask, redirect, url_for, jsonify, request
from flask_login import LoginManager, current_user
from models import db, User
from auth import auth_bp
from contacts import contacts_bp
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'  # Blueprint-qualified endpoint

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(contacts_bp)

# Global error handler for API routes (returns JSON instead of HTML for 500s)
@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler: Return JSON for API routes, HTML for others."""
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': str(error)}), 500
    return f"Internal Server Error: {str(error)}", 500

# Create tables and default user
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='test').first():
        user = User(username='test')
        user.set_password('test')
        db.session.add(user)
        db.session.commit()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('contacts.random_users'))
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)
