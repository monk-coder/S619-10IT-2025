import random


class Perceptron:
    def __init__(self, inputs_num, rate=0.1):
        self.w = [random.uniform(-0.5, 0.5) for _ in range(inputs_num)]
        self.b = random.uniform(-0.5, 0.5)
        self.rate = rate
    
    def activate(self, value):
        return 1 if value >= 0 else 0
    
    def process(self, data):
        total = self.b
        for i in range(len(data)):
            total += data[i] * self.w[i]
        return self.activate(total)
    
    def train(self, data_list, target_list, epochs=20):
        for epoch in range(epochs):
            errors = 0
            updates = []
            
            for data, target in zip(data_list, target_list):
                output = self.process(data)
                error = target - output
                
                if error != 0:
                    errors += 1
                    updates.append((error, data))
            
            if errors == 0:
                print(f"Эпоха {epoch+1}: обучение завершено")
                return True
            
            for error, data in updates:
                for i in range(len(self.w)):
                    self.w[i] += self.rate * error * data[i]
                self.b += self.rate * error
            
            print(f"Эпоха {epoch+1}: ошибок {errors}")
        
        return False
    
    def test(self, data_list, target_list):
        correct = 0
        print("\nТестирование:")
        for data, target in zip(data_list, target_list):
            result = self.process(data)
            correct += 1 if result == target else 0
            print(f"{data} -> ожидание: {target}, результат: {result}")
        print(f"Правильно: {correct}/{len(data_list)}")


def main():
    # Данные для AND
    X = [[0,0], [0,1], [1,0], [1,1]]
    y = [0, 0, 0, 1]
    
    print("Логическая функция AND")
    print("Входы -> Выход")
    for i in range(4):
        print(f"{X[i]} -> {y[i]}")
    
    print("\nИнициализация перцептрона...")
    p = Perceptron(inputs_num=2, rate=0.1)
    print(f"Начальные веса: {[round(w, 3) for w in p.w]}")
    print(f"Начальный bias: {round(p.b, 3)}")
    
    print("\nОбучение:")
    success = p.train(X, y, epochs=20)
    
    if success:
        print("\nОбучение успешно!")
    else:
        print("\nОбучение не завершено за заданное число эпох")
    
    print(f"\nФинальные веса: {[round(w, 3) for w in p.w]}")
    print(f"Финальный bias: {round(p.b, 3)}")
    
    p.test(X, y)
    
    # Дополнительно: покажем как работает внутри
    print("\n" + "="*40)
    print("Детальная работа для каждого входа:")
    for data in X:
        total = p.b + data[0]*p.w[0] + data[1]*p.w[1]
        result = p.process(data)
        print(f"{data}: {p.b:.3f} + {data[0]}*{p.w[0]:.3f} + {data[1]}*{p.w[1]:.3f} = {total:.3f} -> {result}")


if __name__ == "__main__":
    main()
