from flask import Blueprint, render_template, jsonify, request, send_file, flash
from flask_login import login_required, current_user
from models import db, Contact, Note
from io import StringIO
import csv
from datetime import datetime  # Required for update_note timestamp

contacts_bp = Blueprint('contacts', __name__)


@contacts_bp.route('/random_users')
@login_required
def random_users():
    return render_template('random_users.html')


@contacts_bp.route('/contacts')
@login_required
def contacts():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('contacts.html', contacts=contacts)


@contacts_bp.route('/api/save_contact', methods=['POST'])
@login_required
def save_contact():
    data = request.json
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    # Check for duplicate by email
    existing = Contact.query.filter_by(
        user_id=current_user.id,
        email=data['email']
    ).first()
    if existing:
        return jsonify({
            'success': False,
            'error': f'Contact "{data["name"]["first"]} {data["name"]["last"]}" already exists (email: {data["email"]})'
        }), 409

    # Create new contact (direct access to API fields)
    contact = Contact(
        user_id=current_user.id,
        name=f"{data['name']['first']} {data['name']['last']}",
        email=data['email'],
        phone=data['phone'],
        picture=data['picture']['large'],
        location=f"{data['location']['street']['number']} {data['location']['street']['name']}, {data['location']['city']}"
    )
    db.session.add(contact)
    db.session.commit()
    return jsonify({'id': contact.id, 'success': True})


@contacts_bp.route('/api/delete_contact/<int:contact_id>', methods=['DELETE'])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
    if not contact:
        return jsonify({'success': False, 'error': 'Contact not found'}), 404
    db.session.delete(contact)
    db.session.commit()
    return jsonify({'success': True})


@contacts_bp.route('/api/add_note/<int:contact_id>', methods=['POST'])
@login_required
def add_note(contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
    if not contact:
        return jsonify({'success': False, 'error': 'Contact not found'}), 404
    content = request.json.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'Note content is required'}), 400
    note = Note(contact_id=contact_id, content=content)
    db.session.add(note)
    db.session.commit()
    return jsonify({'id': note.id, 'content': note.content, 'created_at': note.created_at.isoformat(), 'success': True})


@contacts_bp.route('/api/update_note/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'success': False, 'error': 'Note not found'}), 404
    contact = Contact.query.get(note.contact_id)
    if not contact or contact.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    content = request.json.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'Note content is required'}), 400
    note.content = content
    note.created_at = datetime.utcnow()  # Update timestamp on edit
    db.session.commit()
    return jsonify({'id': note.id, 'content': note.content, 'created_at': note.created_at.isoformat(), 'success': True})


@contacts_bp.route('/api/delete_note/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'success': False, 'error': 'Note not found'}), 404
    contact = Contact.query.get(note.contact_id)
    if not contact or contact.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    db.session.delete(note)
    db.session.commit()
    return jsonify({'success': True})


@contacts_bp.route('/export_csv')
@login_required
def export_csv():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Email', 'Phone', 'Location'])
    for contact in contacts:
        writer.writerow([contact.name, contact.email, contact.phone, contact.location])
    output.seek(0)
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'contacts_{current_user.username}.csv'
    )
