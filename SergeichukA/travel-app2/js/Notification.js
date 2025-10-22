class Notification {
    static show(message, type = 'success') {
        const notification = document.getElementById('notification');
        const text = document.getElementById('notification-text');
        text.textContent = message;
        notification.className = 'notification';
        notification.style.background = type === 'error' 
            ? 'linear-gradient(135deg, #FF6584 0%, #FC466B 100%)' 
            : 'var(--gradient)';
        notification.classList.add('show');
        setTimeout(() => notification.classList.remove('show'), 3000);
    }
}