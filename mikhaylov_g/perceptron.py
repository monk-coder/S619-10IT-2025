#!/usr/bin/env python3
"""
Реализация однослойного перцептрона для бинарной классификации.
Обучается логической функции AND.
Без использования NumPy.
"""

import random


class Perceptron:
    """Однослойный перцептрон для бинарной классификации."""
    
    def __init__(self, num_inputs=2, learning_rate=0.1, epochs=20):  # Исправлено: __init__
        """
        Инициализация перцептрона.
        
        Параметры:
            num_inputs (int): количество входных признаков
            learning_rate (float): коэффициент обучения
            epochs (int): количество эпох обучения
        """
        # Инициализация небольшими случайными весами
        self.weights = [random.uniform(-0.1, 0.1) for _ in range(num_inputs)]
        self.bias = 0.0  # начальное смещение
        self.learning_rate = learning_rate
        self.epochs = epochs
        
    def activation(self, weighted_sum):
        """
        Ступенчатая функция активации.
        
        Параметры:
            weighted_sum (float): взвешенная сумма входов
            
        Возвращает:
            int: 1 если weighted_sum >= 0, иначе 0
        """
        return 1 if weighted_sum >= 0 else 0
    
    def predict(self, inputs):
        """
        Предсказание выхода для заданных входов.
        
        Параметры:
            inputs (list): входные значения
            
        Возвращает:
            int: предсказанный класс (0 или 1)
        """
        # Вычисляем взвешенную сумму: w1*x1 + w2*x2 + ... + b
        weighted_sum = 0
        for i in range(len(inputs)):
            weighted_sum += self.weights[i] * inputs[i]
        weighted_sum += self.bias
        
        return self.activation(weighted_sum)
    
    def train(self, training_inputs, labels):
        """
        Обучение перцептрона.
        
        Параметры:
            training_inputs (list): обучающие примеры
            labels (list): целевые значения
        """
        print("Начало обучения перцептрона...")
        print(f"Начальные веса: [{self.weights[0]:.4f}, {self.weights[1]:.4f}], "
              f"смещение: {self.bias:.4f}\n")
        
        for epoch in range(self.epochs):
            total_error = 0
            
            for i in range(len(training_inputs)):
                inputs = training_inputs[i]
                label = labels[i]
                
                # Предсказание
                prediction = self.predict(inputs)
                
                # Вычисление ошибки
                error = label - prediction
                total_error += abs(error)
                
                # Обновление весов и смещения
                for j in range(len(self.weights)):
                    self.weights[j] += self.learning_rate * error * inputs[j]
                self.bias += self.learning_rate * error
            
            # Вывод информации о текущей эпохе
            print(f"Эпоха {epoch + 1}/{self.epochs}, "
                  f"Суммарная ошибка: {total_error}, "
                  f"Веса: [{self.weights[0]:.4f}, {self.weights[1]:.4f}], "
                  f"Смещение: {self.bias:.4f}")
            
            # Если ошибка равна 0, обучение можно завершить досрочно
            if total_error == 0:
                print(f"\nОбучение завершено досрочно на эпохе {epoch + 1}")
                break


def main():
    """Основная функция для демонстрации работы перцептрона."""
    
    # 1. Создание набора данных для логической функции AND
    print("=" * 60)
    print("Логическая функция AND (без использования NumPy)")
    print("=" * 60)
    
    # Входные данные: все возможные комбинации для 2 битов
    training_inputs = [
        [0, 0],
        [0, 1],
        [1, 0],
        [1, 1]
    ]
    
    # Целевые значения для функции AND
    labels = [0, 0, 0, 1]
    
    # Вывод информации о данных
    print("\nОбучающие данные:")
    print("Входы\t\tМетка")
    print("-" * 20)
    for i in range(len(training_inputs)):
        print(f"{training_inputs[i]}\t\t{labels[i]}")
    
    # 2. Инициализация перцептрона
    perceptron = Perceptron(
        num_inputs=2,
        learning_rate=0.1,
        epochs=20
    )
    
    # 3. Обучение перцептрона
    perceptron.train(training_inputs, labels)
    
    # 4. Тестирование и вывод результатов
    print("\n" + "=" * 60)
    print("Результаты после обучения")
    print("=" * 60)
    
    print(f"\nФинальные параметры:")
    print(f"Веса: [{perceptron.weights[0]:.4f}, {perceptron.weights[1]:.4f}]")
    print(f"Смещение: {perceptron.bias:.4f}")
    
    print("\nТестирование на всех примерах:")
    print("Входы\t\tОжидаемый\tПредсказанный\tРезультат")
    print("-" * 55)
    
    all_correct = True
    for i in range(len(training_inputs)):
        inputs = training_inputs[i]
        expected = labels[i]
        prediction = perceptron.predict(inputs)
        correct = "✓" if prediction == expected else "✗"
        if prediction != expected:
            all_correct = False
        
        print(f"{inputs}\t\t{expected}\t\t{prediction}\t\t{correct}")
    
    print("\n" + "=" * 60)
    if all_correct:
        print("✅ Перцептрон успешно выучил функцию AND!")
    else:
        print("❌ Перцептрон не смог выучить функцию AND")
    print("=" * 60)
    
    # Демонстрация работы с функцией OR
    print("\n\n" + "=" * 60)
    print("Демонстрация: функция OR")
    print("=" * 60)
    
    # Целевые значения для функции OR
    or_labels = [0, 1, 1, 1]
    
    # Новый перцептрон для функции OR
    perceptron_or = Perceptron(
        num_inputs=2,
        learning_rate=0.1,
        epochs=20
    )
    
    # Обучение для OR
    perceptron_or.train(training_inputs, or_labels)
    
    # Тестирование
    print("\nТестирование функции OR:")
    all_correct_or = True
    for i in range(len(training_inputs)):
        inputs = training_inputs[i]
        expected = or_labels[i]
        prediction = perceptron_or.predict(inputs)
        correct = "✓" if prediction == expected else "✗"
        if prediction != expected:
            all_correct_or = False
        
        print(f"{inputs} -> ожидалось: {expected}, предсказано: {prediction} {correct}")
    
    if all_correct_or:
        print("\n✅ Перцептрон успешно выучил функцию OR!")
    else:
        print("\n❌ Перцептрон не смог выучить функцию OR")


if __name__ == "__main__":  # Исправлено: __name__ == "__main__"
    main()
