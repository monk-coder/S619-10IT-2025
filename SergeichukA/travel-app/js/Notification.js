class Notification {
    static show(message, type = 'success') {
        const notification = document.getElementById('notification');
        const text = document.getElementById('notification-text');
        
        text.textContent = message;
        notification.className = 'notification';
        
        if (type === 'error') {
            notification.style.background = 'linear-gradient(135deg, #FF6584 0%, #FC466B 100%)';
        } else {
            notification.style.background = 'var(--gradient)';
        }
        
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
}