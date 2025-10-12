// Load random users from API
async function loadRandomUsers() {
    const container = document.getElementById('users-container');
    if (!container) {
        console.error('Users container not found');
        return;
    }
    container.innerHTML = '<p>Loading...</p>';
    try {
        const response = await fetch('https://randomuser.me/api/?results=5');
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        const data = await response.json();
        container.innerHTML = '';  // Clear loading message

        data.results.forEach(user => {
            // Create card element
            const card = document.createElement('div');
            card.className = 'user-card';
            card.innerHTML = `
                <img src="${user.picture.large}" alt="Profile Picture">
                <h3>${user.name.first} ${user.name.last}</h3>
                <p>Email: ${user.email}</p>
                <p>Phone: ${user.phone}</p>
                <button class="save-btn">Save to Contacts</button>
            `;
            container.appendChild(card);

            // Attach event listener AFTER adding to DOM
            const saveButton = card.querySelector('.save-btn');
            if (saveButton) {
                saveButton.addEventListener('click', () => {
                    saveContact(user, saveButton);
                });
            }
        });
        console.log('Users loaded successfully');
    } catch (error) {
        container.innerHTML = '<p>Error loading users. Please try again.</p>';
        console.error('API Error:', error);
    }
}

// Save contact to backend
async function saveContact(user, button) {
    if (!button) {
        button = event ? event.target : null;
    }
    if (button) {
        button.disabled = true;
        button.textContent = 'Saving...';
    }
    try {
        const response = await fetch('/api/save_contact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(user)
        });
        let result;
        try {
            result = await response.json();
        } catch (parseErr) {
            throw new Error(`Invalid response: ${await response.text()}`);
        }
        if (response.ok && result.success) {
            alert(`Saved to contacts! ID: ${result.id}`);
            if (button) {
                button.textContent = 'Saved!';
                button.style.background = '#ccc';
                button.disabled = true;
            }
            loadRandomUsers();  // Reload fresh users
        } else {
            if (button) {
                button.disabled = false;
                button.textContent = 'Save to Contacts';
            }
            console.error('Backend Response:', result);
            alert(`Error saving: ${result.error || 'Unknown error. Check console.'}`);
        }
    } catch (error) {
        if (button) {
            button.disabled = false;
            button.textContent = 'Save to Contacts';
        }
        console.error('Save Error:', error);
        alert(`Error saving contact: ${error.message}. Check network tab.`);
    }
}

// Delete contact
async function deleteContact(contactId) {
    if (!confirm('Are you sure you want to delete this contact?')) return;
    try {
        const response = await fetch(`/api/delete_contact/${contactId}`, {
            method: 'DELETE'
        });
        let result;
        try {
            result = await response.json();
        } catch (parseErr) {
            throw new Error(`Invalid response: ${await response.text()}`);
        }
        if (result.success) {
            alert('Contact deleted!');
            location.reload();  // Reload contacts page
        } else {
            alert(`Error deleting: ${result.error}`);
        }
    } catch (error) {
        console.error('Delete Error:', error);
        alert('Error deleting contact.');
    }
}

// Add note to contact
async function addNote(contactId) {
    const input = document.getElementById(`note-${contactId}`);
    if (!input) {
        alert('Note input not found.');
        return;
    }
    const content = input.value.trim();
    if (!content) {
        alert('Please enter note content.');
        input.focus();
        return;
    }
    try {
        const response = await fetch(`/api/add_note/${contactId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        });
        let result;
        try {
            result = await response.json();
        } catch (parseErr) {
            throw new Error(`Invalid response: ${await response.text()}`);
        }
        if (result.success) {
            alert('Note added!');
            input.value = '';  // Clear input
            location.reload();  // Reload to show new note
        } else {
            alert(`Error adding note: ${result.error}`);
        }
    } catch (error) {
        console.error('Add Note Error:', error);
        alert('Error adding note.');
    }
}

// Update (edit) a note
async function updateNote(noteId) {
    const newContent = prompt('Enter new note content:');
    if (!newContent || newContent.trim() === '') {
        alert('Note content cannot be empty.');
        return;
    }
    try {
        const response = await fetch(`/api/update_note/${noteId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: newContent.trim() })
        });
        let result;
        try {
            result = await response.json();
        } catch (parseErr) {
            throw new Error(`Invalid response: ${await response.text()}`);
        }
        if (result.success) {
            alert('Note updated!');
            location.reload();  // Reload to show changes
        } else {
            alert(`Error updating note: ${result.error}`);
        }
    } catch (error) {
        console.error('Update Note Error:', error);
        alert('Error updating note.');
    }
}

// Delete a note
async function deleteNote(noteId) {
    if (!confirm('Are you sure you want to delete this note?')) return;
    try {
        const response = await fetch(`/api/delete_note/${noteId}`, {
            method: 'DELETE'
        });
        let result;
        try {
            result = await response.json();
        } catch (parseErr) {
            throw new Error(`Invalid response: ${await response.text()}`);
        }
        if (result.success) {
            alert('Note deleted!');
            location.reload();  // Reload to remove from list
        } else {
            alert(`Error deleting note: ${result.error}`);
        }
    } catch (error) {
        console.error('Delete Note Error:', error);
        alert('Error deleting note.');
    }
}

// Optional: Auto-load users on page load (uncomment if desired)
// window.addEventListener('DOMContentLoaded', () => {
//     if (document.getElementById('users-container')) {
//         loadRandomUsers();
//     }
// });

// Debug: Log when script loads
console.log('Script.js loaded successfully - All functions defined');
