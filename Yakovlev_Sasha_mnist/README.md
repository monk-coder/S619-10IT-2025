# Нейросеть для классификации рукописных цифр MNIST (реализация с нуля)

Автор: Яковлев Александр 10 ИТ

## Описание
Данный проект реализует двухслойную нейронную сеть **с нуля** (без использования TensorFlow/PyTorch) для классификации изображений из датасета MNIST (цифры 0–9).  
Реализованы:
- Прямое распространение (forward propagation)
- Обратное распространение (backpropagation)
- Градиентный спуск
- Оценка точности и визуализация обучения

## Требования
- Python 3.8 или выше

## Установка и запуск

1. Клонируйте репозиторий и перейдите в папку проекта:
   ```bash
   cd Yakovlev_Sasha_MNIST
   
# Neural Network for Handwritten Digit and Letter Classification (from scratch)

This project implements a **two-layer neural network from scratch** (without TensorFlow/PyTorch) for classifying:
- **Digits 0–9** (MNIST dataset)
- **Uppercase letters A–Z** (EMNIST Letters dataset)
- download (EMNIST LETTERS DATASET): https://disk.yandex.ru/d/D2eN-a55F7lh4A

The network includes:
- Forward and backward propagation
- Gradient descent optimization
- ReLU activation (hidden layer) + Softmax (output)
- He weight initialization
- Training loss and accuracy plots

---

## 📦 Requirements

- Python 3.8+
- Dependencies (see `requirements.txt`):
  - `numpy`
  - `matplotlib`
  - `scikit-learn`
  - `pandas`
  - `scipy` (only for EMNIST Letters)

Install with:
```bash
pip install -r requirements.txt
