const API_BASE_URL = '/api/';
const PAGE_SIZE = 10;

const state = {
    user: null,
    statuses: [],
    entries: [],
    pagination: {
        page: 1,
        count: 0,
        next: null,
        previous: null,
    },
    filters: {
        search: '',
        status: '',
        tag: '',
    },
};

const dom = {};

document.addEventListener('DOMContentLoaded', () => {
    cacheDom();
    setupEventListeners();
    initialize();
});

function cacheDom() {
    dom.messages = document.getElementById('messages');
    dom.userInfo = document.getElementById('user-info');
    dom.authSection = document.getElementById('auth-section');
    dom.loginForm = document.getElementById('login-form');
    dom.registerForm = document.getElementById('register-form');
    dom.authHeading = document.getElementById('auth-heading-text');
    dom.logoutButton = document.getElementById('logout-button');
    dom.searchForm = document.getElementById('search-form');
    dom.searchQuery = document.getElementById('search-query');
    dom.searchResults = document.getElementById('search-results');
    dom.entriesList = document.getElementById('entries-list');
    dom.entrySearch = document.getElementById('entry-search');
    dom.statusFilter = document.getElementById('status-filter');
    dom.tagFilter = document.getElementById('tag-filter');
    dom.applyFilters = document.getElementById('apply-filters');
    dom.prevPage = document.getElementById('prev-page');
    dom.nextPage = document.getElementById('next-page');
    dom.paginationInfo = document.getElementById('pagination-info');
    dom.entryTemplate = document.getElementById('entry-template');
    dom.searchResultTemplate = document.getElementById('search-result-template');
}

function setupEventListeners() {
    if (dom.loginForm) {
        dom.loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const formData = new FormData(dom.loginForm);
            await handleLogin({
                username: formData.get('username'),
                password: formData.get('password'),
            });
        });
    }

    if (dom.registerForm) {
        dom.registerForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const formData = new FormData(dom.registerForm);
            await handleRegister({
                username: formData.get('username'),
                email: formData.get('email'),
                password: formData.get('password'),
            });
        });
    }

    if (dom.logoutButton) {
        dom.logoutButton.addEventListener('click', async () => {
            await handleLogout();
        });
    }

    if (dom.searchForm) {
        dom.searchForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const query = dom.searchQuery.value.trim();
            if (query) {
                await searchBooks(query);
            }
        });
    }

    if (dom.applyFilters) {
        dom.applyFilters.addEventListener('click', () => {
            state.filters.search = dom.entrySearch.value.trim();
            state.filters.status = dom.statusFilter.value;
            state.filters.tag = dom.tagFilter.value.trim();
            loadEntries(1);
        });
    }

    if (dom.prevPage) {
        dom.prevPage.addEventListener('click', () => {
            if (state.pagination.previous) {
                loadEntries(state.pagination.page - 1);
            }
        });
    }

    if (dom.nextPage) {
        dom.nextPage.addEventListener('click', () => {
            if (state.pagination.next) {
                loadEntries(state.pagination.page + 1);
            }
        });
    }

    if (dom.entriesList) {
        dom.entriesList.addEventListener('click', async (event) => {
            const entryElement = event.target.closest('.entry');
            if (!entryElement) {
                return;
            }

            const entryId = entryElement.dataset.entryId;

            if (event.target.matches('.save-entry')) {
                await saveEntry(entryElement, entryId);
            }

            if (event.target.matches('.add-note')) {
                await addNote(entryElement, entryId);
            }

            if (event.target.matches('.delete-note')) {
                const noteId = event.target.dataset.noteId;
                await deleteNote(noteId);
            }
        });
    }

    if (dom.searchResults) {
        dom.searchResults.addEventListener('click', async (event) => {
            if (!event.target.matches('.add-to-library')) {
                return;
            }
            if (!state.user) {
                showMessage('Необходимо войти, чтобы добавлять книги.', 'warning');
                return;
            }
            const container = event.target.closest('.book-result');
            const statusSelect = container.querySelector('.book-status');
            const bookPayload = JSON.parse(event.target.dataset.bookPayload);
            const status = statusSelect.value;
            await createEntry(bookPayload, status);
        });
    }
}

async function initialize() {
    await loadStatuses();
    await refreshAuthState();
}

async function refreshAuthState() {
    try {
        const user = await apiFetch(`${API_BASE_URL}auth/me/`);
        state.user = user;
    } catch (error) {
        state.user = null;
    }
    updateAuthUI();
    if (state.user) {
        await Promise.all([loadEntries(1), loadTags()]);
    } else {
        dom.entriesList.innerHTML = '<p class="muted">Войдите, чтобы увидеть свою библиотеку.</p>';
    }
}

function updateAuthUI() {
    if (!dom.authSection) {
        return;
    }
    const authenticated = Boolean(state.user);
    dom.authSection.classList.toggle('authenticated', authenticated);
    if (dom.logoutButton) {
        dom.logoutButton.classList.toggle('hidden', !authenticated);
    }
    if (dom.loginForm) {
        dom.loginForm.classList.toggle('hidden', authenticated);
    }
    if (dom.registerForm) {
        dom.registerForm.classList.toggle('hidden', authenticated);
    }
    if (dom.userInfo) {
        dom.userInfo.dataset.authenticated = authenticated ? 'true' : 'false';
    }
    if (dom.authHeading) {
        const headingValue = authenticated ? (state.user.email || state.user.username || '') : 'Аутентификация';
        dom.authHeading.textContent = headingValue || 'Аутентификация';
    }

    if (!dom.userInfo) {
        return;
    }

    if (authenticated) {
        const displayName = state.user?.username || 'читатель';
        const infoParts = [
            `<span>Здравствуйте, ${displayName}!</span>`,
            state.user?.email ? `<p class="user-email">${state.user.email}</p>` : null,
            '<p class="user-subtitle muted">Продолжайте пополнять коллекцию и делиться заметками.</p>',
        ].filter(Boolean);
        dom.userInfo.innerHTML = infoParts.join('');
    } else {
        dom.userInfo.innerHTML = [
            '<span>Войдите или зарегистрируйтесь, чтобы вести библиотеку.</span>',
            '<p class="user-subtitle muted">Сохраняйте прогресс чтения и заметки в одном месте.</p>',
        ].join('');
    }

    const addButtons = dom.searchResults.querySelectorAll('.add-to-library');
    addButtons.forEach((button) => {
        button.disabled = !authenticated;
    });
}

async function handleLogin(payload) {
    try {
        await apiFetch(`${API_BASE_URL}auth/login/`, {
            method: 'POST',
            body: payload,
        });
        showMessage('Вход выполнен.');
        dom.loginForm.reset();
        await refreshAuthState();
    } catch (error) {
        showMessage(error.message || 'Не удалось войти.', 'error');
    }
}

async function handleRegister(payload) {
    try {
        await apiFetch(`${API_BASE_URL}auth/register/`, {
            method: 'POST',
            body: payload,
        });
        showMessage('Регистрация завершена. Вы автоматически вошли в систему.');
        dom.registerForm.reset();
        await refreshAuthState();
    } catch (error) {
        showMessage(error.message || 'Не удалось зарегистрироваться.', 'error');
    }
}

async function handleLogout() {
    try {
        await apiFetch(`${API_BASE_URL}auth/logout/`, {
            method: 'POST',
        });
    } catch (error) {
        console.warn(error);
    }
    showMessage('Вы вышли из системы.');
    state.user = null;
    updateAuthUI();
    dom.entriesList.innerHTML = '<p class="muted">Войдите, чтобы увидеть свою библиотеку.</p>';
}

async function loadStatuses() {
    try {
        const data = await apiFetch(`${API_BASE_URL}statuses/`);
        state.statuses = data;
        populateStatusFilter();
    } catch (error) {
        console.error('Не удалось загрузить статусы.', error);
    }
}

async function loadEntries(page = 1) {
    if (!state.user) {
        return;
    }
    try {
        const params = new URLSearchParams();
        params.set('page', page);
        if (state.filters.search) {
            params.set('search', state.filters.search);
        }
        if (state.filters.status) {
            params.set('status', state.filters.status);
        }
        if (state.filters.tag) {
            params.set('tag', state.filters.tag);
        }
        const data = await apiFetch(`${API_BASE_URL}entries/?${params.toString()}`);
        state.entries = data.results;
        state.pagination.page = page;
        state.pagination.count = data.count;
        state.pagination.next = data.next;
        state.pagination.previous = data.previous;
        renderEntries();
        updatePagination();
    } catch (error) {
        showMessage(error.message || 'Не удалось загрузить книги.', 'error');
    }
}

async function loadTags() {
    if (!state.user) {
        return;
    }
    try {
        const data = await apiFetch(`${API_BASE_URL}tags/`);
        state.availableTags = data;
    } catch (error) {
        console.warn('Не удалось загрузить теги.', error);
    }
}

async function searchBooks(query) {
    showMessage('Выполняю поиск в Open Library...');
    dom.searchResults.innerHTML = '';
    try {
        const url = new URL('https://openlibrary.org/search.json');
        url.searchParams.set('q', query);
        url.searchParams.set('limit', '15');
        url.searchParams.set('fields', 'key,title,author_name,isbn,first_publish_year,number_of_pages_median,cover_i');
        const response = await fetch(url);
        const data = await response.json();
        renderSearchResults(data.docs || []);
        showMessage(`Результатов: ${data.numFound ?? data.docs.length}`);
    } catch (error) {
        console.error(error);
        showMessage('Не удалось выполнить поиск.', 'error');
    }
}

function renderSearchResults(results) {
    dom.searchResults.innerHTML = '';
    if (!results.length) {
        dom.searchResults.innerHTML = '<p class="muted">Ничего не найдено.</p>';
        return;
    }
    results.slice(0, 15).forEach((doc) => {
        const element = dom.searchResultTemplate.content.firstElementChild.cloneNode(true);
        const titleEl = element.querySelector('.book-title');
        const authorsEl = element.querySelector('.book-authors');
        const isbnEl = element.querySelector('.book-isbn');
        const statusSelect = element.querySelector('.book-status');
        const addButton = element.querySelector('.add-to-library');

        const bookPayload = formatBookPayload(doc);
        titleEl.textContent = bookPayload.title || 'Без названия';
        authorsEl.textContent = bookPayload.authors ? `Авторы: ${bookPayload.authors}` : 'Автор неизвестен';
        isbnEl.textContent = bookPayload.isbn ? `ISBN: ${bookPayload.isbn}` : '';

        populateStatusOptions(statusSelect);
        addButton.dataset.bookPayload = JSON.stringify(bookPayload);
        addButton.disabled = !state.user;

        dom.searchResults.appendChild(element);
    });
}

function formatBookPayload(doc) {
    const coverUrl = doc.cover_i ? `https://covers.openlibrary.org/b/id/${doc.cover_i}-M.jpg` : '';
    const isbn = Array.isArray(doc.isbn) ? doc.isbn[0] : doc.isbn;
    const authors = Array.isArray(doc.author_name) ? doc.author_name.join(', ') : (doc.author_name || '');
    return {
        external_id: doc.key,
        source: 'open_library',
        title: doc.title || 'Без названия',
        authors,
        isbn: isbn || '',
        description: '',
        cover_url: coverUrl,
        page_count: doc.number_of_pages_median || null,
        published_date: doc.first_publish_year ? String(doc.first_publish_year) : '',
    };
}

async function createEntry(bookPayload, status) {
    try {
        await apiFetch(`${API_BASE_URL}entries/`, {
            method: 'POST',
            body: {
                book_data: bookPayload,
                status,
                rating: null,
                review: '',
                tag_names: [],
            },
        });
        showMessage('Книга добавлена в библиотеку.');
        await loadEntries(1);
        await loadTags();
    } catch (error) {
        showMessage(error.message || 'Не удалось добавить книгу.', 'error');
    }
}

async function saveEntry(entryElement, entryId) {
    const statusSelect = entryElement.querySelector('.entry-status');
    const ratingInput = entryElement.querySelector('.entry-rating');
    const reviewField = entryElement.querySelector('.entry-review');
    const tagsField = entryElement.querySelector('.entry-tags');

    const ratingValue = ratingInput.value ? Number(ratingInput.value) : null;
    const payload = {
        status: statusSelect.value,
        rating: ratingValue,
        review: reviewField.value.trim(),
        tag_names: tagsField.value
            .split(',')
            .map((tag) => tag.trim())
            .filter(Boolean),
    };

    try {
        await apiFetch(`${API_BASE_URL}entries/${entryId}/`, {
            method: 'PATCH',
            body: payload,
        });
        showMessage('Запись обновлена.');
        await loadEntries(state.pagination.page);
        await loadTags();
    } catch (error) {
        showMessage(error.message || 'Не удалось обновить запись.', 'error');
    }
}

async function addNote(entryElement, entryId) {
    const noteField = entryElement.querySelector('.note-content');
    const content = noteField.value.trim();
    if (!content) {
        showMessage('Введите текст заметки.', 'warning');
        return;
    }
    try {
        await apiFetch(`${API_BASE_URL}notes/`, {
            method: 'POST',
            body: {
                entry_id: entryId,
                content,
            },
        });
        noteField.value = '';
        showMessage('Заметка добавлена.');
        await loadEntries(state.pagination.page);
    } catch (error) {
        showMessage(error.message || 'Не удалось добавить заметку.', 'error');
    }
}

async function deleteNote(noteId) {
    try {
        await apiFetch(`${API_BASE_URL}notes/${noteId}/`, {
            method: 'DELETE',
        });
        showMessage('Заметка удалена.');
        await loadEntries(state.pagination.page);
    } catch (error) {
        showMessage(error.message || 'Не удалось удалить заметку.', 'error');
    }
}

function renderEntries() {
    dom.entriesList.innerHTML = '';
    if (!state.entries.length) {
        dom.entriesList.innerHTML = '<p class="muted">Пока нет записей.</p>';
        return;
    }

    state.entries.forEach((entry) => {
        const element = dom.entryTemplate.content.firstElementChild.cloneNode(true);
        element.dataset.entryId = entry.id;
        element.querySelector('.entry-title').textContent = entry.book.title;
        element.querySelector('.entry-authors').textContent = entry.book.authors || 'Автор неизвестен';

        const statusSelect = element.querySelector('.entry-status');
        populateStatusOptions(statusSelect, entry.status);

        const ratingInput = element.querySelector('.entry-rating');
        ratingInput.value = entry.rating || '';

        const tagsField = element.querySelector('.entry-tags');
        tagsField.value = entry.tags.map((tag) => tag.name).join(', ');

        const reviewField = element.querySelector('.entry-review');
        reviewField.value = entry.review;

        renderNotes(element.querySelector('.notes-list'), entry.notes);

        dom.entriesList.appendChild(element);
    });
}

function renderNotes(listElement, notes) {
    listElement.innerHTML = '';
    if (!notes.length) {
        listElement.innerHTML = '<li class="muted">Пока нет заметок.</li>';
        return;
    }
    notes.forEach((note) => {
        const item = document.createElement('li');
        const date = new Date(note.created_at);
        const formattedDate = Number.isNaN(date.getTime()) ? '' : date.toLocaleString('ru-RU');
        const header = formattedDate ? `<span class="note-date">${formattedDate}</span>` : '';
        item.innerHTML = `
            ${header}
            <p>${escapeHtml(note.content)}</p>
            <button class="delete-note" data-note-id="${note.id}">Удалить</button>
        `;
        listElement.appendChild(item);
    });
}

function updatePagination() {
    const { page, count, next, previous } = state.pagination;
    const totalPages = Math.ceil(count / PAGE_SIZE) || 1;
    dom.prevPage.disabled = !previous;
    dom.nextPage.disabled = !next;
    const start = count === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
    const end = Math.min(page * PAGE_SIZE, count);
    dom.paginationInfo.textContent = count
        ? `${start}–${end} из ${count}`
        : 'Нет записей';
    dom.paginationInfo.title = `Страница ${page} из ${totalPages}`;
}

function populateStatusOptions(selectElement, selectedSlug = null) {
    if (!selectElement) {
        return;
    }
    selectElement.innerHTML = '';
    state.statuses.forEach((status) => {
        const option = document.createElement('option');
        option.value = status.slug;
        option.textContent = status.label;
        if (selectedSlug && status.slug === selectedSlug) {
            option.selected = true;
        }
        selectElement.appendChild(option);
    });
}

function populateStatusFilter() {
    if (!dom.statusFilter) {
        return;
    }
    const currentValue = dom.statusFilter.value;
    const defaultOption = dom.statusFilter.querySelector('option[value=""]');
    dom.statusFilter.innerHTML = '';
    if (defaultOption) {
        dom.statusFilter.appendChild(defaultOption);
    } else {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'Все статусы';
        dom.statusFilter.appendChild(option);
    }
    state.statuses.forEach((status) => {
        const option = document.createElement('option');
        option.value = status.slug;
        option.textContent = status.label;
        dom.statusFilter.appendChild(option);
    });
    dom.statusFilter.value = currentValue;
}

function showMessage(message, type = 'info') {
    if (!dom.messages) {
        return;
    }
    dom.messages.textContent = message;
    dom.messages.className = `messages ${type}`;
    if (message) {
        setTimeout(() => {
            dom.messages.textContent = '';
            dom.messages.className = 'messages';
        }, 5000);
    }
}

async function apiFetch(url, options = {}) {
    const config = {
        method: options.method || 'GET',
        credentials: 'same-origin',
        headers: {
            Accept: 'application/json',
            ...(options.headers || {}),
        },
    };

    if (options.body && typeof options.body === 'object') {
        config.body = JSON.stringify(options.body);
        config.headers['Content-Type'] = 'application/json';
    } else if (options.body) {
        config.body = options.body;
    }

    if (!['GET', 'HEAD', 'OPTIONS'].includes(config.method.toUpperCase())) {
        config.headers['X-CSRFToken'] = getCsrfToken();
    }

    const response = await fetch(url, config);
    let data = null;
    if (response.status !== 204) {
        try {
            data = await response.json();
        } catch (error) {
            data = null;
        }
    }

    if (!response.ok) {
        const message = extractErrorMessage(data) || response.statusText || 'Ошибка запроса.';
        const error = new Error(message);
        error.status = response.status;
        throw error;
    }

    return data;
}

function extractErrorMessage(payload) {
    if (!payload) {
        return null;
    }
    if (typeof payload === 'string') {
        return payload;
    }
    if (payload.detail) {
        return payload.detail;
    }
    if (Array.isArray(payload)) {
        return payload[0];
    }
    const firstValue = Object.values(payload)[0];
    if (Array.isArray(firstValue)) {
        return firstValue[0];
    }
    if (typeof firstValue === 'string') {
        return firstValue;
    }
    return null;
}

function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
}

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value;
    return div.innerHTML;
}
