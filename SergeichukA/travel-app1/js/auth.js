class AuthService {
    static baseURL = 'http://localhost:8000/api';

    static async register(username, email, password) {
        try {
            const response = await fetch(`${this.baseURL}/register`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ username, email, password })
            });

            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Ошибка регистрации');

            this.setCurrentUser(data.user);
            return data.user;

        } catch (error) { throw error; }
    }

    static async login(username, password) {
        try {
            const response = await fetch(`${this.baseURL}/login`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Ошибка входа');

            this.setCurrentUser(data.user);
            return data.user;

        } catch (error) { throw error; }
    }

    static logout() {
        this.setCurrentUser(null);
        Wishlist.clearCache();
    }

    static getCurrentUser() {
        try { return JSON.parse(localStorage.getItem('current_user')); }
        catch (error) { return null; }
    }

    static setCurrentUser(user) {
        if (user) localStorage.setItem('current_user', JSON.stringify(user));
        else localStorage.removeItem('current_user');
    }

    static isLoggedIn() { return !!this.getCurrentUser(); }

    static getApiKey() {
        const user = this.getCurrentUser();
        return user ? user.api_key : null;
    }

    static getUserId() {
        const user = this.getCurrentUser();
        return user ? user.id : null;
    }
}