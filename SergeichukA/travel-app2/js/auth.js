class AuthService {
    static baseURL = 'http://localhost:8000/api';

    static async register(username, email, password) {
        const response = await fetch(`${this.baseURL}/register`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username, email, password })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Ошибка регистрации');
        this.setCurrentUser(data.user);
        return data.user;
    }

    static async login(username, password) {
        const response = await fetch(`${this.baseURL}/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Ошибка входа');
        this.setCurrentUser(data.user);
        return data.user;
    }

    static logout() {
        this.setCurrentUser(null);
        Wishlist.clearCache();
    }

    static getCurrentUser() {
        return JSON.parse(localStorage.getItem('current_user'));
    }

    static setCurrentUser(user) {
        user ? localStorage.setItem('current_user', JSON.stringify(user)) : localStorage.removeItem('current_user');
    }

    static isLoggedIn() { return !!this.getCurrentUser(); }
    static getApiKey() { return this.getCurrentUser()?.api_key; }
    static getUserId() { return this.getCurrentUser()?.id; }
}