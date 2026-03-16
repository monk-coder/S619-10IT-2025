# utils.py
import numpy as np
import pickle
import matplotlib.pyplot as plt


# ==================== ФУНКЦИИ ПОТЕРЬ ====================

def cross_entropy_loss(logits, targets):
    """
    Вычисляет cross-entropy loss

    Args:
        logits: (batch_size, seq_len, vocab_size)
        targets: (batch_size, seq_len)

    Returns:
        loss: скаляр
    """
    B, T, V = logits.shape

    # Стабильный log_softmax
    logits_max = np.max(logits, axis=-1, keepdims=True)
    log_probs = logits - logits_max
    log_probs = log_probs - np.log(np.sum(np.exp(log_probs), axis=-1, keepdims=True))

    # Выбираем вероятности целевых токенов
    log_probs = log_probs.reshape(-1, V)
    targets = targets.reshape(-1)

    loss = -np.mean(log_probs[np.arange(len(targets)), targets])
    return loss


def cross_entropy_gradient(logits, targets):
    """
    Вычисляет градиент cross-entropy loss по logits

    Args:
        logits: (batch_size, seq_len, vocab_size)
        targets: (batch_size, seq_len)

    Returns:
        dlogits: (batch_size, seq_len, vocab_size)
    """
    B, T, V = logits.shape

    # Softmax
    exp_logits = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
    probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

    # Градиент
    dlogits = probs.copy()
    dlogits.reshape(-1, V)[np.arange(B * T), targets.reshape(-1)] -= 1
    dlogits /= (B * T)

    return dlogits


# ==================== ОПТИМИЗАТОР ====================

class Adam:
    """
    Adam оптимизатор
    """

    def __init__(self, params, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-8):
        """
        Args:
            params: список кортежей (param, grad)
            lr: learning rate
            beta1: коэффициент для момента первого порядка
            beta2: коэффициент для момента второго порядка
            eps: стабилизатор деления
        """
        self.params = params
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.t = 0

        # Инициализация моментов
        self.m = []  # первый момент (среднее градиентов)
        self.v = []  # второй момент (нецентрированная дисперсия)

        for param, _ in params:
            self.m.append(np.zeros_like(param))
            self.v.append(np.zeros_like(param))

    def step(self):
        """Обновляет параметры модели"""
        self.t += 1

        for i, (param, grad) in enumerate(self.params):
            # Обновляем моменты
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * grad
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (grad ** 2)

            # Коррекция смещения
            m_hat = self.m[i] / (1 - self.beta1 ** self.t)
            v_hat = self.v[i] / (1 - self.beta2 ** self.t)

            # Обновляем параметры
            param -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

    def zero_grad(self):
        """Обнуляет градиенты"""
        for _, grad in self.params:
            grad.fill(0)


# ==================== DATALOADER ====================

class DataLoader:
    """
    DataLoader для обучения на тексте
    """

    def __init__(self, data, batch_size, seq_len):
        """
        Args:
            data: 1D массив индексов токенов
            batch_size: размер батча
            seq_len: длина последовательности
        """
        self.data = data
        self.batch_size = batch_size
        self.seq_len = seq_len
        self.n_samples = len(data) - seq_len - 1

    def __iter__(self):
        """Возвращает итератор по батчам"""
        self.indices = np.random.permutation(self.n_samples)
        self.current = 0
        return self

    def __next__(self):
        """Возвращает следующий батч"""
        if self.current >= len(self.indices):
            raise StopIteration

        batch_indices = self.indices[self.current:self.current + self.batch_size]
        self.current += self.batch_size

        x_batch = []
        y_batch = []

        for idx in batch_indices:
            x_batch.append(self.data[idx:idx + self.seq_len])
            y_batch.append(self.data[idx + 1:idx + self.seq_len + 1])

        return np.array(x_batch), np.array(y_batch)

    def __len__(self):
        """Возвращает количество батчей"""
        return (self.n_samples + self.batch_size - 1) // self.batch_size


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def load_text(file_path='data.txt'):
    """
    Загружает текст из файла

    Args:
        file_path: путь к файлу с текстом

    Returns:
        text: строка с текстом
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return text


def create_vocab(text):
    """
    Создает словарь символов из текста

    Args:
        text: входной текст

    Returns:
        char_to_idx: словарь символ -> индекс
        idx_to_char: словарь индекс -> символ
        vocab_size: размер словаря
    """
    chars = sorted(list(set(text)))
    char_to_idx = {ch: i for i, ch in enumerate(chars)}
    idx_to_char = {i: ch for i, ch in enumerate(chars)}
    return char_to_idx, idx_to_char, len(chars)


def text_to_indices(text, char_to_idx):
    """
    Преобразует текст в индексы

    Args:
        text: входной текст
        char_to_idx: словарь символ -> индекс

    Returns:
        indices: массив индексов
    """
    return np.array([char_to_idx[ch] for ch in text])


def save_checkpoint(model, char_to_idx, idx_to_char, losses, filename='checkpoint.pkl'):
    """
    Сохраняет чекпоинт модели
    """
    checkpoint = {
        'model': model,
        'char_to_idx': char_to_idx,
        'idx_to_char': idx_to_char,
        'losses': losses
    }
    with open(filename, 'wb') as f:
        pickle.dump(checkpoint, f)
    print(f"Чекпоинт сохранен в {filename}")


def load_checkpoint(filename='checkpoint.pkl'):
    """
    Загружает чекпоинт модели
    """
    with open(filename, 'rb') as f:
        checkpoint = pickle.load(f)
    return checkpoint['model'], checkpoint['char_to_idx'], checkpoint['idx_to_char'], checkpoint['losses']


def plot_losses(losses, save_path='loss.png'):
    """
    Рисует график потерь
    """
    plt.figure(figsize=(10, 5))
    plt.plot(losses)
    plt.title('Training Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.grid(True)
    plt.savefig(save_path)
    plt.show()