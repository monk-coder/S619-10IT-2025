
class AuthService {
    static usersKey = 'travel_app_users';
    static currentUserKey = 'travel_app_current_user';

    static init() {
        // Создаем тестового пользователя для демонстрации
        const users = this.getUsers();
        if (users.length === 0) {
            const demoUser = {
                id: this.generateId(),
                username: 'demo',
                email: 'demo@example.com',
                password: this.hashPassword('demo123'),
                createdAt: new Date().toISOString()
            };
            users.push(demoUser);
            this.saveUsers(users);
        }
    }

    static getUsers() {
        try {
            return JSON.parse(localStorage.getItem(this.usersKey)) || [];
        } catch (error) {
            console.error('Ошибка загрузки пользователей:', error);
            return [];
        }
    }

    static saveUsers(users) {
        localStorage.setItem(this.usersKey, JSON.stringify(users));
    }

    static getCurrentUser() {
        try {
            return JSON.parse(localStorage.getItem(this.currentUserKey));
        } catch (error) {
            return null;
        }
    }

    static setCurrentUser(user) {
        if (user) {
            localStorage.setItem(this.currentUserKey, JSON.stringify(user));
        } else {
            localStorage.removeItem(this.currentUserKey);
        }
    }

    static isLoggedIn() {
        return !!this.getCurrentUser();
    }

    static register(username, email, password) {
        const users = this.getUsers();
        
        // Проверяем, существует ли пользователь
        if (users.find(u => u.username === username)) {
            throw new Error('Пользователь с таким именем уже существует');
        }
        
        if (users.find(u => u.email === email)) {
            throw new Error('Пользователь с таким email уже существует');
        }

        // Создаем нового пользователя
        const newUser = {
            id: this.generateId(),
            username,
            email,
            password: this.hashPassword(password),
            createdAt: new Date().toISOString()
        };

        users.push(newUser);
        this.saveUsers(users);
        
        // Автоматически логиним пользователя после регистрации
        this.setCurrentUser(newUser);
        
        return newUser;
    }

    static login(username, password) {
        const users = this.getUsers();
        const user = users.find(u => u.username === username);
        
        if (!user) {
            throw new Error('Пользователь не найден');
        }

        if (user.password !== this.hashPassword(password)) {
            throw new Error('Неверный пароль');
        }

        this.setCurrentUser(user);
        return user;
    }

    static logout() {
        this.setCurrentUser(null);
        Wishlist.clearCache(); // Очищаем кэш вишлиста
    }

    static hashPassword(password) {
        // Простое хеширование для демонстрации
        // В реальном приложении используйте более безопасные методы
        let hash = 0;
        for (let i = 0; i < password.length; i++) {
            const char = password.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return hash.toString();
    }

    static generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    static getUserId() {
        const user = this.getCurrentUser();
        return user ? user.id : null;
    }

    static getUserWishlistKey() {
        const userId = this.getUserId();
        return userId ? `wishlist_${userId}` : null;
    }
}
