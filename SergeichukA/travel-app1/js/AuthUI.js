class AuthUI {
    static init() {
        this.createAuthSection();
        this.bindAuthEvents();
        this.updateAuthUI();
    }

    static createAuthSection() {
        const header = document.querySelector('header');
        const existingAuthSection = document.getElementById('auth-section');
        
        if (existingAuthSection) existingAuthSection.remove();

        const authSection = document.createElement('div');
        authSection.id = 'auth-section';
        authSection.className = 'auth-section';
        authSection.style.cssText = `
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        `;
        header.appendChild(authSection);
    }

    static bindAuthEvents() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('close')) this.hideAuthModal();
        });

        document.getElementById('authModal').addEventListener('click', (e) => {
            if (e.target.id === 'authModal') this.hideAuthModal();
        });

        document.querySelectorAll('.auth-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = tab.getAttribute('data-tab');
                this.switchAuthTab(tabName);
            });
        });

        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        document.getElementById('registerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister();
        });
    }

    static switchAuthTab(tabName) {
        document.querySelectorAll('.auth-tab').forEach(tab => {
            tab.classList.toggle('active', tab.getAttribute('data-tab') === tabName);
        });

        document.querySelectorAll('.auth-form').forEach(form => {
            form.classList.toggle('active', form.id === `${tabName}Form`);
        });

        document.getElementById('authModalTitle').textContent = 
            tabName === 'login' ? 'Вход в систему' : 'Регистрация';
    }

    static async handleLogin() {
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        if (!username || !password) {
            Notification.show('Заполните все поля', 'error');
            return;
        }

        try {
            const user = await AuthService.login(username, password);
            Notification.show(`Добро пожаловать, ${user.username}!`);
            this.hideAuthModal();
            this.updateAuthUI();
            Wishlist.render();
        } catch (error) { Notification.show(error.message, 'error'); }
    }

    static async handleRegister() {
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('registerConfirmPassword').value;

        if (!username || !email || !password || !confirmPassword) {
            Notification.show('Заполните все поля', 'error');
            return;
        }

        if (password !== confirmPassword) {
            Notification.show('Пароли не совпадают', 'error');
            return;
        }

        if (password.length < 6) {
            Notification.show('Пароль должен содержать минимум 6 символов', 'error');
            return;
        }

        try {
            const user = await AuthService.register(username, email, password);
            Notification.show(`Регистрация успешна! Добро пожаловать, ${username}!`);
            this.hideAuthModal();
            this.updateAuthUI();
            Wishlist.render();
        } catch (error) { Notification.show(error.message, 'error'); }
    }

    static showLoginModal() {
        this.switchAuthTab('login');
        document.getElementById('authModal').style.display = 'block';
    }

    static showRegisterModal() {
        this.switchAuthTab('register');
        document.getElementById('authModal').style.display = 'block';
    }

    static hideAuthModal() {
        document.getElementById('authModal').style.display = 'none';
        document.querySelectorAll('.auth-form').forEach(form => form.reset());
    }

    static updateAuthUI() {
        const authSection = document.getElementById('auth-section');
        if (!authSection) return;

        const user = AuthService.getCurrentUser();

        if (user) {
            authSection.innerHTML = `
                <div class="user-info" style="display: flex; align-items: center; gap: 10px; color: white;">
                    <i class="fas fa-user-circle" style="font-size: 1.5rem;"></i>
                    <span style="font-weight: 500;">${user.username}</span>
                    <button onclick="AuthUI.logout()" class="logout-btn" style="
                        background: rgba(255,255,255,0.2);
                        color: white;
                        border: 1px solid rgba(255,255,255,0.3);
                        padding: 8px 16px;
                        border-radius: 20px;
                        cursor: pointer;
                        transition: all 0.3s;
                    ">
                        <i class="fas fa-sign-out-alt"></i> Выйти
                    </button>
                </div>
            `;
        } else {
            authSection.innerHTML = `
                <div class="auth-buttons" style="display: flex; gap: 10px;">
                    <button onclick="AuthUI.showLoginModal()" class="auth-btn login-btn" style="
                        background: var(--primary);
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 20px;
                        cursor: pointer;
                        font-weight: 500;
                        transition: all 0.3s;
                    ">
                        <i class="fas fa-sign-in-alt"></i> Войти
                    </button>
                    <button onclick="AuthUI.showRegisterModal()" class="auth-btn register-btn" style="
                        background: rgba(255,255,255,0.2);
                        color: white;
                        border: 1px solid rgba(255,255,255,0.3);
                        padding: 10px 20px;
                        border-radius: 20px;
                        cursor: pointer;
                        font-weight: 500;
                        transition: all 0.3s;
                    ">
                        <i class="fas fa-user-plus"></i> Регистрация
                    </button>
                </div>
            `;
        }
    }

    static logout() {
        AuthService.logout();
        Notification.show('Вы вышли из системы');
        this.updateAuthUI();
        Wishlist.render();
    }
}

window.AuthUI = AuthUI;