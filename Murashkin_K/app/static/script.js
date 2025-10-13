class ContactManager {
async showNotes(contactId) {
        console.log('Showing notes for contact:', contactId);

        const notesSection = document.getElementById(`notes-${contactId}`);
        if (!notesSection) {
            console.error('Notes section not found');
            return;
        }

        if (notesSection.classList.contains('hidden')) {
            try {
                const response = await fetch(`/api/contacts/${contactId}/notes`, {
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const notes = await response.json();

                notesSection.innerHTML = `
                    <div class="notes-header">
                        <h4>Notes (${notes.length})</h4>
                        <button class="btn btn-success add-note-btn" data-contact-id="${contactId}">
                            + Add Note
                        </button>
                    </div>
                    <div class="notes-list" id="notes-list-${contactId}"></div>
                `;

                this.displayNotes(contactId, notes);
                notesSection.classList.remove('hidden');

                // Добавляем обработчик для кнопки добавления заметки
                const addButton = notesSection.querySelector('.add-note-btn');
                addButton.addEventListener('click', () => {
                    this.showAddNoteModal(contactId);
                });

            } catch (error) {
                console.error('Error loading notes:', error);
                this.showNotification('Error loading notes: ' + error.message, 'error');
            }
        } else {
            notesSection.classList.add('hidden');
        }
    }

    displayNotes(contactId, notes) {
        const container = document.getElementById(`notes-list-${contactId}`);
        if (!container) return;

        container.innerHTML = '';

        if (notes.length === 0) {
            container.innerHTML = `
                <div class="no-notes">
                    <p>No notes yet. Add your first note!</p>
                </div>
            `;
            return;
        }

        notes.forEach(note => {
            const noteElement = this.createNoteElement(note, contactId);
            container.appendChild(noteElement);
        });
    }

    createNoteElement(note, contactId) {
        const noteElement = document.createElement('div');
        noteElement.className = 'note-item';
        noteElement.innerHTML = `
            <div class="note-content">
                <div class="note-text">${this.escapeHtml(note.content)}</div>
                <div class="note-meta">
                    Created: ${new Date(note.created_at).toLocaleString()}
                    ${note.updated_at ? ` | Updated: ${new Date(note.updated_at).toLocaleString()}` : ''}
                </div>
            </div>
            <div class="note-actions">
                <button class="btn btn-primary btn-sm edit-note-btn"
                        data-note-id="${note.id}"
                        data-contact-id="${contactId}">
                    Edit
                </button>
                <button class="btn btn-danger btn-sm delete-note-btn"
                        data-note-id="${note.id}"
                        data-contact-id="${contactId}">
                    Delete
                </button>
            </div>
        `;

        // Добавляем обработчики
        const editButton = noteElement.querySelector('.edit-note-btn');
        const deleteButton = noteElement.querySelector('.delete-note-btn');

        editButton.addEventListener('click', () => {
            this.showEditNoteModal(note, contactId);
        });

        deleteButton.addEventListener('click', () => {
            this.deleteNote(note.id, contactId);
        });

        return noteElement;
    }

    showAddNoteModal(contactId) {
        const modal = document.getElementById('noteModal');
        if (!modal) {
            console.error('Note modal not found');
            return;
        }

        // Обновляем заголовок
        const modalTitle = modal.querySelector('.modal-title');
        if (modalTitle) {
            modalTitle.textContent = 'Add New Note';
        }

        // Очищаем текстовую область
        const noteTextarea = document.getElementById('noteContent');
        if (noteTextarea) {
            noteTextarea.value = '';
        }

        // Устанавливаем обработчик формы
        const noteForm = document.getElementById('noteForm');
        if (noteForm) {
            // Удаляем старый обработчик
            noteForm.onsubmit = null;
            // Добавляем новый
            noteForm.onsubmit = (e) => this.handleAddNote(e, contactId);
        }

        modal.classList.remove('hidden');
    }

    showEditNoteModal(note, contactId) {
        const modal = document.getElementById('noteModal');
        if (!modal) {
            console.error('Note modal not found');
            return;
        }

        // Обновляем заголовок
        const modalTitle = modal.querySelector('.modal-title');
        if (modalTitle) {
            modalTitle.textContent = 'Edit Note';
        }

        // Заполняем текстовую область
        const noteTextarea = document.getElementById('noteContent');
        if (noteTextarea) {
            noteTextarea.value = note.content;
        }

        // Устанавливаем обработчик формы
        const noteForm = document.getElementById('noteForm');
        if (noteForm) {
            // Удаляем старый обработчик
            noteForm.onsubmit = null;
            // Добавляем новый для редактирования
            noteForm.onsubmit = (e) => this.handleEditNote(e, note.id, contactId);
        }

        modal.classList.remove('hidden');
    }

    async handleAddNote(e, contactId) {
        e.preventDefault();

        const noteTextarea = document.getElementById('noteContent');
        if (!noteTextarea) return;

        const content = noteTextarea.value.trim();

        if (!content) {
            alert('Please enter note content');
            return;
        }

        try {
            const response = await fetch(`/api/contacts/${contactId}/notes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({ content })
            });

            if (response.ok) {
                this.hideModals();
                this.showNotification('Note added successfully!', 'success');
                // Перезагружаем заметки
                await this.showNotes(contactId);
            } else {
                const errorData = await response.json();
                this.showNotification('Failed to add note: ' + (errorData.detail || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Error adding note:', error);
            this.showNotification('Error adding note: ' + error.message, 'error');
        }
    }

    async handleEditNote(e, noteId, contactId) {
        e.preventDefault();

        const noteTextarea = document.getElementById('noteContent');
        if (!noteTextarea) return;

        const content = noteTextarea.value.trim();

        if (!content) {
            alert('Please enter note content');
            return;
        }

        try {
            const response = await fetch(`/api/notes/${noteId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({ content })
            });

            if (response.ok) {
                this.hideModals();
                this.showNotification('Note updated successfully!', 'success');
                // Перезагружаем заметки
                await this.showNotes(contactId);
            } else {
                const errorData = await response.json();
                this.showNotification('Failed to update note: ' + (errorData.detail || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Error updating note:', error);
            this.showNotification('Error updating note: ' + error.message, 'error');
        }
    }

    async deleteNote(noteId, contactId) {
        if (!confirm('Are you sure you want to delete this note?')) {
            return;
        }

        try {
            const response = await fetch(`/api/notes/${noteId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                this.showNotification('Note deleted successfully!', 'success');
                // Перезагружаем заметки
                await this.showNotes(contactId);
            } else {
                const errorData = await response.json();
                this.showNotification('Failed to delete note: ' + (errorData.detail || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Error deleting note:', error);
            this.showNotification('Error deleting note: ' + error.message, 'error');
        }
    }

    // Вспомогательная функция для экранирования HTML
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    constructor() {
        this.token = localStorage.getItem('token');
        this.isSaving = false;
        this.eventListeners = new Map(); // Для отслеживания обработчиков
        this.init();
    }

    init() {
        console.log('Initializing ContactManager...');
        this.bindEvents();
        this.checkAuth();
    }

    bindEvents() {
        console.log('Binding events...');

        // Очищаем все предыдущие обработчики
        this.unbindAllEvents();

        // Обработчики для статических элементов
        this.addEventListener('loginBtn', 'click', () => this.showLogin());
        this.addEventListener('registerBtn', 'click', () => this.showRegister());
        this.addEventListener('logoutBtn', 'click', () => this.logout());
        this.addEventListener('randomUsersTab', 'click', () => this.showTab('randomUsers'));
        this.addEventListener('contactsTab', 'click', () => this.showTab('contacts'));
        this.addEventListener('exportCsvBtn', 'click', () => this.exportContacts());

        // Обработчики для форм
        this.addEventListener('loginForm', 'submit', (e) => this.handleLogin(e));
        this.addEventListener('registerForm', 'submit', (e) => this.handleRegister(e));

        // Обработчики для модальных окон
        document.querySelectorAll('.close').forEach((closeBtn, index) => {
            this.addEventListener(`close-${index}`, 'click', () => this.hideModals(), closeBtn);
        });

        document.querySelectorAll('.modal').forEach((modal, index) => {
            this.addEventListener(`modal-${index}`, 'click', (e) => {
                if (e.target === modal) this.hideModals();
            }, modal);
        });

        console.log('Events bound successfully');
    }

    addEventListener(key, event, handler, element = null) {
        const targetElement = element || document.getElementById(key);
        if (!targetElement) {
            console.warn(`Element not found: ${key}`);
            return;
        }

        // Удаляем предыдущий обработчик если есть
        if (this.eventListeners.has(key)) {
            const oldHandler = this.eventListeners.get(key);
            targetElement.removeEventListener(event, oldHandler);
        }

        // Сохраняем ссылку на обработчик
        this.eventListeners.set(key, handler);

        // Добавляем новый обработчик
        targetElement.addEventListener(event, handler);
    }

    unbindAllEvents() {
        // Удаляем все обработчики из DOM
        this.eventListeners.forEach((handler, key) => {
            const element = document.getElementById(key);
            if (element) {
                // Пытаемся удалить обработчик, но не беспокоимся если элемент не найден
                element.removeEventListener('click', handler);
            }
        });
        this.eventListeners.clear();
    }

    displayRandomUsers(users) {
        const container = document.getElementById('randomUsersGrid');
        if (!container) return;

        // Полностью очищаем контейнер
        container.innerHTML = '';

        users.forEach((user, index) => {
            const card = this.createUserCard(user, index);
            container.appendChild(card);
        });

        console.log(`Displayed ${users.length} users with unique handlers`);
    }

    createUserCard(user, index) {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <img src="${user.picture}" alt="${user.first_name} ${user.last_name}"
                 onerror="this.src='https://via.placeholder.com/80x80?text=No+Image'">
            <h3>${user.first_name} ${user.last_name}</h3>
            <p>📧 ${user.email}</p>
            <p>📞 ${user.phone}</p>
            <button class="btn btn-primary save-contact-btn" id="save-btn-${index}">
                Save Contact
            </button>
        `;

        // Добавляем обработчик напрямую к кнопке с уникальным ID
        const saveButton = card.querySelector('.save-contact-btn');
        this.addEventListener(`save-btn-${index}`, 'click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.handleSaveContact(user, `save-btn-${index}`);
        }, saveButton);

        return card;
    }

    async handleSaveContact(userData, buttonId) {
        console.log(`Save contact called for button: ${buttonId}`);

        // Защита от множественных нажатий
        if (this.isSaving) {
            console.log('Save operation already in progress, skipping...');
            return;
        }

        if (!this.token) {
            alert('Please login to save contacts');
            return;
        }

        this.isSaving = true;

        // Блокируем конкретную кнопку
        const button = document.getElementById(buttonId);
        if (button) {
            button.disabled = true;
            button.textContent = 'Saving...';
            button.style.opacity = '0.6';
        }

        try {
            console.log('Saving contact:', userData);

            const response = await fetch('/api/contacts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify(userData)
            });

            if (response.ok) {
                console.log('Contact saved successfully');

                if (button) {
                    button.textContent = '✓ Saved';
                    button.classList.remove('btn-primary');
                    button.classList.add('btn-success');
                }

                this.showNotification('Contact saved successfully!', 'success');

            } else {
                const errorData = await response.json();
                console.error('Save failed:', errorData);

                if (button) {
                    button.textContent = 'Save Contact';
                    button.disabled = false;
                    button.style.opacity = '1';
                }

                this.showNotification(
                    errorData.detail || 'Failed to save contact',
                    'error'
                );
            }
        } catch (error) {
            console.error('Error saving contact:', error);

            if (button) {
                button.textContent = 'Save Contact';
                button.disabled = false;
                button.style.opacity = '1';
            }

            this.showNotification('Error saving contact: ' + error.message, 'error');
        } finally {
            // Снимаем блокировку через 1 секунду
            setTimeout(() => {
                this.isSaving = false;
            }, 1000);
        }
    }

    showNotification(message, type = 'info') {
        // Создаем уведомление
        const notification = document.createElement('div');
        const bgColor = type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8';

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${bgColor};
            color: white;
            padding: 12px 24px;
            border-radius: 5px;
            z-index: 10000;
            font-weight: bold;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        `;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 3000);
    }

    // Остальные методы остаются без изменений
    showLogin() {
        console.log('Show login called');
        document.getElementById('loginModal').classList.remove('hidden');
    }

    showRegister() {
        console.log('Show register called');
        document.getElementById('registerModal').classList.remove('hidden');
    }

    hideModals() {
        document.getElementById('loginModal').classList.add('hidden');
        document.getElementById('registerModal').classList.add('hidden');
        document.getElementById('noteModal').classList.add('hidden');
    }

    async handleLogin(e) {
        e.preventDefault();
        console.log('Login form submitted');

        const formData = new FormData(e.target);
        const data = {
            username: formData.get('username'),
            password: formData.get('password')
        };

        try {
            const response = await fetch('/api/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `username=${encodeURIComponent(data.username)}&password=${encodeURIComponent(data.password)}`
            });

            if (response.ok) {
                const result = await response.json();
                this.token = result.access_token;
                localStorage.setItem('token', this.token);
                this.hideModals();
                await this.checkAuth();
            } else {
                const errorData = await response.json();
                alert('Login failed: ' + (errorData.detail || 'Unknown error'));
            }
        } catch (error) {
            alert('Login error: ' + error.message);
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        console.log('Register form submitted');

        const formData = new FormData(e.target);
        const data = {
            username: formData.get('username').trim(),
            email: formData.get('email').trim(),
            password: formData.get('password')
        };

        if (data.username.length < 3) {
            alert('Username must be at least 3 characters long');
            return;
        }

        if (data.password.length < 6) {
            alert('Password must be at least 6 characters long');
            return;
        }

        if (!data.email.includes('@')) {
            alert('Please enter a valid email address');
            return;
        }

        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                alert('Registration successful! Please login.');
                this.hideModals();
                this.showLogin();
            } else {
                const errorData = await response.json();
                alert('Registration failed: ' + (errorData.detail || 'Unknown error'));
            }
        } catch (error) {
            alert('Registration error: ' + error.message);
        }
    }

    logout() {
        this.token = null;
        localStorage.removeItem('token');
        this.showUnauthenticated();
    }

    showAuthenticated() {
        document.getElementById('authSection').classList.add('hidden');
        document.getElementById('userSection').classList.remove('hidden');
        document.getElementById('tabs').classList.remove('hidden');
        this.showTab('randomUsers');
    }

    showUnauthenticated() {
        document.getElementById('authSection').classList.remove('hidden');
        document.getElementById('userSection').classList.add('hidden');
        document.getElementById('tabs').classList.add('hidden');
        document.getElementById('randomUsersContent').classList.add('hidden');
        document.getElementById('contactsContent').classList.add('hidden');
    }

    async checkAuth() {
        if (this.token) {
            try {
                await this.loadRandomUsers();
                this.showAuthenticated();
            } catch (error) {
                console.error('Auth check failed:', error);
                this.logout();
            }
        } else {
            this.showUnauthenticated();
        }
    }

    showTab(tabName) {
        console.log('Showing tab:', tabName);

        document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
        document.getElementById(`${tabName}Tab`).classList.add('active');

        document.getElementById('randomUsersContent').classList.add('hidden');
        document.getElementById('contactsContent').classList.add('hidden');
        document.getElementById(`${tabName}Content`).classList.remove('hidden');

        if (tabName === 'randomUsers') {
            this.loadRandomUsers();
        } else if (tabName === 'contacts') {
            this.loadContacts();
        }
    }

    async loadRandomUsers() {
        try {
            console.log('Loading random users...');
            const response = await fetch('/api/random-users');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const users = await response.json();
            this.displayRandomUsers(users);
        } catch (error) {
            console.error('Error loading random users:', error);
            document.getElementById('randomUsersGrid').innerHTML = '<p>Error loading users. Please try again.</p>';
        }
    }

    async loadContacts() {
        if (!this.token) return;

        try {
            const response = await fetch('/api/contacts', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.logout();
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const contacts = await response.json();
            this.displayContacts(contacts);
        } catch (error) {
            console.error('Error loading contacts:', error);
            document.getElementById('contactsList').innerHTML = '<p>Error loading contacts. Please try again.</p>';
        }
    }

    displayContacts(contacts) {
        const container = document.getElementById('contactsList');
        if (!container) return;

        container.innerHTML = '';

        if (contacts.length === 0) {
            container.innerHTML = '<p>No contacts saved yet. Start by saving some random users!</p>';
            return;
        }

        contacts.forEach((contact, index) => {
            const contactElement = document.createElement('div');
            contactElement.className = 'contact-item';
            contactElement.innerHTML = `
                <div class="contact-info">
                    <img src="${contact.picture}" alt="${contact.first_name} ${contact.last_name}">
                    <div>
                        <h4>${contact.first_name} ${contact.last_name}</h4>
                        <p>📧 ${contact.email}</p>
                        <p>📞 ${contact.phone}</p>
                    </div>
                </div>
                <div class="contact-actions">
                    <button class="btn btn-danger delete-contact" id="delete-contact-${index}">Delete</button>
                    <button class="btn btn-primary show-notes" id="show-notes-${index}">Notes</button>
                </div>
                <div id="notes-${contact.id}" class="notes-section hidden"></div>
            `;
            container.appendChild(contactElement);

            // Добавляем обработчики для кнопок контактов
            this.addEventListener(`delete-contact-${index}`, 'click', () => {
                this.deleteContact(contact.id);
            });

            this.addEventListener(`show-notes-${index}`, 'click', () => {
                this.showNotes(contact.id);
            });
        });
    }

    async deleteContact(contactId) {
        if (confirm('Are you sure you want to delete this contact?')) {
            try {
                const response = await fetch(`/api/contacts/${contactId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                });

                if (response.ok) {
                    this.loadContacts();
                } else {
                    alert('Failed to delete contact');
                }
            } catch (error) {
                alert('Error deleting contact: ' + error.message);
            }
        }
    }

    async exportContacts() {
        if (!this.token) {
            alert('Please login to export contacts');
            return;
        }

        try {
            const response = await fetch('/api/contacts/export/csv', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'contacts.csv';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                alert('Failed to export contacts');
            }
        } catch (error) {
            alert('Error exporting contacts: ' + error.message);
        }
    }
}

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded, initializing app...');
    window.app = new ContactManager();
});

// Резервная инициализация
setTimeout(() => {
    if (!window.app) {
        console.log('Fallback initialization');
        window.app = new ContactManager();
    }
}, 1000);