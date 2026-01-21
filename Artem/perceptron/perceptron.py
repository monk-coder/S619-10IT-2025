import numpy as np

def step_function(x):
    """Ступенчатая активационная функция: возвращает 1, если x >= 0, иначе 0."""
    return 1 if x >= 0 else 0

def perceptron_train(X, y, learning_rate=0.1, epochs=20):
    """
    Обучение перцептрона по правилу Хебба (перцептронное правило).
    
    Параметры:
        X — входные данные (массив размера [n_samples, n_features])
        y — целевые метки (массив длины n_samples)
        learning_rate — скорость обучения
        epochs — количество эпох
    
    Возвращает:
        weights — обученные веса
        bias — обученный сдвиг (bias)
    """
    # Инициализация весов и смещения нулями
    n_features = X.shape[1]
    weights = np.zeros(n_features)
    bias = 0.0

    for epoch in range(epochs):
        total_errors = 0
        for i in range(len(X)):
            # Вычисление взвешенной суммы
            linear_output = np.dot(weights, X[i]) + bias
            # Применение активационной функции
            prediction = step_function(linear_output)
            # Ошибка = целевое значение - предсказание
            error = y[i] - prediction
            # Обновление весов и смещения
            weights += learning_rate * error * X[i]
            bias += learning_rate * error
            total_errors += abs(error)
        # Опционально: можно выводить прогресс обучения
        # print(f"Эпоха {epoch + 1}, ошибок: {total_errors}")
        # Ранняя остановка, если всё выучено
        if total_errors == 0:
            break
    return weights, bias

def predict(X, weights, bias):
    """Делает предсказания для набора входов X."""
    predictions = []
    for x in X:
        linear_output = np.dot(weights, x) + bias
        pred = step_function(linear_output)
        predictions.append(pred)
    return predictions

def main():
    # 1. Создание обучающего набора данных для логической функции AND
    X = np.array([[0, 0],
                  [0, 1],
                  [1, 0],
                  [1, 1]])
    y = np.array([0, 0, 0, 1])  # AND: только (1,1) → 1

    # 2. Обучение перцептрона
    weights, bias = perceptron_train(X, y, learning_rate=0.1, epochs=20)

    # 3. Вывод обученных параметров
    print("Обученные параметры:")
    print(f"Веса: w1 = {weights[0]:.2f}, w2 = {weights[1]:.2f}")
    print(f"Смещение (bias): b = {bias:.2f}\n")

    # 4. Тестирование на всех входах
    predictions = predict(X, weights, bias)
    print("Результаты предсказаний:")
    print("Вход\tОжидаемый\tПредсказание")
    for i in range(len(X)):
        print(f"{X[i]}\t{y[i]}\t\t{predictions[i]}")

if __name__ == "__main__":
    main()