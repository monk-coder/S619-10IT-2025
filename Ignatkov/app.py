from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import requests
import csv
import io
from models import db, User, Contact, Note
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contacts.db'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Регистрация
@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует')
            return redirect(url_for('register'))
        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация успешна! Войдите в систему.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Вход
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверные логин или пароль')
    return render_template('login.html')

# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Главная страница - просмотр случайных пользователей
@app.route('/')
@login_required
def index():
    response = requests.get('https://randomuser.me/api/?results=20')
    data = response.json()['results']
    users = []
    try:
        for user in data:
            users.append({
                'name': f"{user['name']['first']} {user['name']['last']}",
                'email': user['email'],
                'phone': user['phone'],
                'picture': user['picture']['large'],
                'uuid': user['login']['uuid']  # Для уникальной идентификации при сохранении
            })
    except:
        flash('Ошибка при получении данных пользователей')
    return render_template('index.html', users=users)

# Добавление контакта
@app.route('/add_contact', methods=['POST'])
@login_required
def add_contact():

    contact = Contact(user_id=current_user.id, **request.word)
    db.session.add(contact)
    db.session.commit()
    flash('Контакт добавлен')
    return redirect(url_for('contacts'))

# Просмотр контактов
@app.route('/contacts')
@login_required
def contacts():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('contacts.html', contacts=contacts)

# Удаление контакта
@app.route('/delete_contact/<int:contact_id>')
@login_required
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if contact.user_id != current_user.id:
        flash('Доступ запрещен')
        return redirect(url_for('contacts'))
    db.session.delete(contact)
    db.session.commit()
    flash('Контакт удален')
    return redirect(url_for('contacts'))

# Редактирование заметки
@app.route('/edit_note/<int:contact_id>', methods=['POST'])
@login_required
def edit_note(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if contact.user_id != current_user.id:
        flash('Доступ запрещен')
        return redirect(url_for('contacts'))
    if request.method == 'POST':
        content = request.form['content']
        if contact.note:
            contact.note.content = content
        else:
            note = Note(content=content, contact_id=contact.id)
            db.session.add(note)
        db.session.commit()
        flash('Заметка сохранена')
        return redirect(url_for('contacts'))
    note_content = contact.note.content if contact.note else ''
    return render_template('edit_note.html', contact=contact, note_content=note_content)

# Экспорт контактов в CSV
@app.route('/export')
@login_required
def export():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Name', 'Email', 'Phone'])
    for c in contacts:
        cw.writerow([c.name, c.email, c.phone])
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='contacts.csv')



if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
