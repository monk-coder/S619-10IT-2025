"""
perceptron_logic_gate.py
Однослойный перцептрон для обучения логическим функциям.
Оптимизированная версия с улучшенным выводом.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Union
from dataclasses import dataclass
from enum import Enum
import time


class ActivationFunction(Enum):
    STEP = "step"
    SIGMOID = "sigmoid"


class LogicGate(Enum):
    AND = "AND"
    OR = "OR"
    NAND = "NAND"
    XOR = "XOR"


@dataclass
class TrainingHistory:
    epochs: List[int]
    errors: List[float]
    weights_history: List[np.ndarray]
    
    def get_best_epoch(self) -> int:
        return int(np.argmin(self.errors)) + 1 if self.errors else 0


class Perceptron:
    def __init__(
        self,
        n_inputs: int,
        learning_rate: float = 0.1,
        activation: ActivationFunction = ActivationFunction.STEP,
        random_seed: Optional[int] = None
    ):
        if random_seed is not None:
            np.random.seed(random_seed)
            
        self.n_inputs = n_inputs
        self.learning_rate = learning_rate
        self.activation_type = activation
        
        limit = 1 / np.sqrt(n_inputs)
        self.weights = np.random.uniform(-limit, limit, n_inputs + 1)
        self.history: Optional[TrainingHistory] = None
        self.training_time: float = 0.0
        
        self.activation_functions = {
            ActivationFunction.STEP: self._step_activation,
            ActivationFunction.SIGMOID: self._sigmoid_activation,
        }

    def _step_activation(self, x: float) -> int:
        return 1 if x >= 0 else 0
    
    def _sigmoid_activation(self, x: float) -> float:
        return 1 / (1 + np.exp(-x))
    
    def activate(self, weighted_sum: float) -> Union[int, float]:
        func = self.activation_functions[self.activation_type]
        return func(weighted_sum)
    
    def forward(self, inputs: np.ndarray) -> Tuple[Union[int, float], float]:
        inputs_with_bias = np.append(inputs, 1.0)
        weighted_sum = np.dot(inputs_with_bias, self.weights)
        prediction = self.activate(weighted_sum)
        return prediction, weighted_sum
    
    def predict(self, inputs: np.ndarray) -> Union[int, float]:
        prediction, _ = self.forward(inputs)
        return prediction
    
    def train(
        self,
        training_data: List[np.ndarray],
        targets: List[int],
        epochs: int = 100,
        verbose: bool = True,
        early_stopping: bool = True,
        patience: int = 5
    ) -> TrainingHistory:
        
        if len(training_data) != len(targets):
            raise ValueError("Количество примеров и целей должно совпадать")
        
        start_time = time.time()
        history = TrainingHistory(epochs=[], errors=[], weights_history=[])
        
        if verbose:
            header_lines = [
                "=" * 70,
                "НАЧАЛО ОБУЧЕНИЯ ПЕРЦЕПТРОНА".center(70),
                "=" * 70,
                f"{'Параметр':<25} {'Значение':<25}",
                "-" * 70,
                f"{'Количество входов':<25} {self.n_inputs:<25}",
                f"{'Функция активации':<25} {self.activation_type.value:<25}",
                f"{'Коэффициент обучения':<25} {self.learning_rate:<25.4f}",
                f"{'Макс. количество эпох':<25} {epochs:<25}",
                f"{'Начальные веса':<25} [{self.weights[0]:.4f}, {self.weights[1]:.4f}]",
                f"{'Начальное смещение':<25} {self.weights[-1]:.4f}",
                "=" * 70,
                ""
            ]
            print("\n".join(header_lines))
        
        best_error = float('inf')
        patience_counter = 0
        epoch_info_lines = []
        
        for epoch in range(epochs):
            epoch_error = 0
            indices = np.random.permutation(len(training_data))
            
            for idx in indices:
                inputs = training_data[idx]
                target = targets[idx]
                prediction, _ = self.forward(inputs)
                error = target - prediction
                epoch_error += abs(error)
                
                if error != 0:
                    inputs_with_bias = np.append(inputs, 1.0)
                    self.weights += self.learning_rate * error * inputs_with_bias
            
            history.epochs.append(epoch + 1)
            history.errors.append(epoch_error)
            history.weights_history.append(self.weights.copy())
            
            if verbose:
                progress = (epoch / epochs) * 100
                epoch_line = (f"Эпоха {epoch + 1:3d}/{epochs} | "
                             f"Ошибка: {epoch_error:6.2f} | "
                             f"Прогресс: {progress:5.1f}% | "
                             f"Веса: [{self.weights[0]:7.4f}, {self.weights[1]:7.4f}] | "
                             f"Bias: {self.weights[-1]:7.4f}")
                epoch_info_lines.append(epoch_line)
            
            if verbose and ((epoch + 1) % max(1, epochs // 10) == 0 or epoch + 1 == epochs):
                print("\n".join(epoch_info_lines[-max(1, epochs // 20):]))
                epoch_info_lines.clear()
            
            if early_stopping:
                if epoch_error < best_error:
                    best_error = epoch_error
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if epoch_error == 0 or patience_counter >= patience:
                    if verbose and epoch_error == 0:
                        print(f"\n✓ Обучение завершено на эпохе {epoch + 1}! Достигнута нулевая ошибка.")
                    break
        
        self.training_time = time.time() - start_time
        self.history = history
        
        if verbose and self.history:
            summary_lines = [
                "\n" + "=" * 70,
                "ИТОГИ ОБУЧЕНИЯ".center(70),
                "=" * 70,
                f"{'Финальная ошибка':<30}: {self.history.errors[-1]:.4f}",
                f"{'Всего эпох':<30}: {len(self.history.epochs)}",
                f"{'Время обучения':<30}: {self.training_time:.3f} сек",
                f"{'Финальные веса':<30}: [{self.weights[0]:.6f}, {self.weights[1]:.6f}]",
                f"{'Финальный bias':<30}: {self.weights[-1]:.6f}",
                "=" * 70
            ]
            print("\n".join(summary_lines))
        
        return history
    
    def evaluate(
        self,
        test_data: List[np.ndarray],
        test_targets: List[int],
        verbose: bool = False
    ) -> Dict[str, float]:
        
        predictions = [self.predict(x) for x in test_data]
        
        if self.activation_type == ActivationFunction.STEP:
            correct = sum(1 for p, t in zip(predictions, test_targets) if p == t)
        else:
            correct = sum(1 for p, t in zip(predictions, test_targets) 
                         if (p >= 0.5 and t == 1) or (p < 0.5 and t == 0))
        
        accuracy = correct / len(test_data)
        
        metrics = {
            'accuracy': accuracy,
            'error_rate': 1 - accuracy,
            'correct': correct,
            'total': len(test_data)
        }
        
        if verbose:
            self._print_evaluation_details(test_data, test_targets, predictions)
        
        return metrics
    
    def _print_evaluation_details(
        self,
        test_data: List[np.ndarray],
        test_targets: List[int],
        predictions: List[Union[int, float]]
    ):
        
        table_lines = [
            "\n" + "=" * 70,
            "ДЕТАЛЬНАЯ ОЦЕНКА".center(70),
            "=" * 70,
            f"{'Входы':^12} | {'Цель':^8} | {'Предсказание':^12} | {'Сумма':^10} | {'Верно':^8}",
            "-" * 70
        ]
        
        for i, (inputs, target, pred) in enumerate(zip(test_data, test_targets, predictions)):
            _, weighted_sum = self.forward(inputs)
            
            if self.activation_type == ActivationFunction.STEP:
                is_correct = pred == target
            else:
                is_correct = (pred >= 0.5 and target == 1) or (pred < 0.5 and target == 0)
            
            table_lines.append(
                f"{str(inputs):^12} | {target:^8} | "
                f"{pred:^12.4f} | {weighted_sum:^10.4f} | "
                f"{'✓' if is_correct else '✗':^8}"
            )
        
        table_lines.extend(["-" * 70, ""])
        print("\n".join(table_lines))


class LogicGateDataset:
    @staticmethod
    def create_dataset(gate_type: LogicGate) -> Tuple[List[np.ndarray], List[int]]:
        
        inputs = [
            np.array([0, 0]),
            np.array([0, 1]),
            np.array([1, 0]),
            np.array([1, 1])
        ]
        
        if gate_type == LogicGate.AND:
            targets = [0, 0, 0, 1]
        elif gate_type == LogicGate.OR:
            targets = [0, 1, 1, 1]
        elif gate_type == LogicGate.NAND:
            targets = [1, 1, 1, 0]
        elif gate_type == LogicGate.XOR:
            targets = [0, 1, 1, 0]
        else:
            raise ValueError(f"Неподдерживаемая функция: {gate_type}")
        
        return inputs, targets
    
    @staticmethod
    def get_gate_description(gate_type: LogicGate) -> str:
        descriptions = {
            LogicGate.AND: "Логическое И (AND): 1 только когда оба входа = 1",
            LogicGate.OR: "Логическое ИЛИ (OR): 1 когда хотя бы один вход = 1",
            LogicGate.NAND: "Логическое И-НЕ (NAND): обратное AND",
            LogicGate.XOR: "Исключающее ИЛИ (XOR): 1 когда входы различны"
        }
        return descriptions.get(gate_type, "Неизвестная функция")


def run_experiment(
    gate_type: LogicGate,
    learning_rate: float = 0.1,
    epochs: int = 100,
    verbose: bool = True
) -> Perceptron:
    
    if verbose:
        experiment_header = [
            "\n" + "=" * 70,
            f"ЭКСПЕРИМЕНТ: {gate_type.value}".center(70),
            "=" * 70,
            f"\n{LogicGateDataset.get_gate_description(gate_type)}",
            "\nДанные для обучения:"
        ]
        print("\n".join(experiment_header))
    
    data, targets = LogicGateDataset.create_dataset(gate_type)
    
    if verbose:
        data_lines = [f"  {inputs} -> {target}" for inputs, target in zip(data, targets)]
        print("\n".join(data_lines))
    
    perceptron = Perceptron(
        n_inputs=2,
        learning_rate=learning_rate,
        activation=ActivationFunction.STEP,
        random_seed=42
    )
    
    history = perceptron.train(data, targets, epochs=epochs, verbose=verbose)
    metrics = perceptron.evaluate(data, targets, verbose=verbose)
    
    if verbose:
        print(f"\nТочность: {metrics['accuracy'] * 100:.2f}% ({metrics['correct']}/{metrics['total']})")
    
    return perceptron


def demonstrate_xor_limitation():
    
    xor_lines = [
        "\n" + "=" * 70,
        "ДЕМОНСТРАЦИЯ ОГРАНИЧЕНИЯ: ФУНКЦИЯ XOR".center(70),
        "=" * 70,
        "\n❌ Однослойный перцептрон НЕ МОЖЕТ выучить функцию XOR!",
        "Это классический пример задачи, не являющейся линейно разделимой.",
        "\nПопробуем обучить на XOR для демонстрации:"
    ]
    print("\n".join(xor_lines))
    
    perceptron = Perceptron(n_inputs=2, learning_rate=0.1, random_seed=42)
    data, targets = LogicGateDataset.create_dataset(LogicGate.XOR)
    
    history = perceptron.train(data, targets, epochs=50, verbose=False)
    metrics = perceptron.evaluate(data, targets, verbose=True)
    
    xor_results = [
        f"\nМаксимальная достигнутая точность: {metrics['accuracy'] * 100:.0f}%",
        "\nВывод: Для XOR требуется многослойный перцептрон (MLP)!"
    ]
    print("\n".join(xor_results))


def print_summary_table(perceptrons: List[Tuple[str, Perceptron]]):
    
    summary_lines = [
        "\n" + "=" * 70,
        "СВОДНЫЕ РЕЗУЛЬТАТЫ".center(70),
        "=" * 70,
        f"{'Функция':<10} | {'Точность':<10} | {'Эпох':<6} | {'Время (с)':<10} | {'Линейно':<10}",
        "-" * 70
    ]
    
    for name, perceptron in perceptrons:
        if perceptron.history:
            data, targets = LogicGateDataset.create_dataset(LogicGate[name])
            accuracy = perceptron.evaluate(data, targets, verbose=False)['accuracy']
            is_linear = "✓" if accuracy > 0.99 else "✗"
            
            summary_lines.append(
                f"{name:<10} | {accuracy * 100:<9.1f}% | "
                f"{len(perceptron.history.epochs):<6} | "
                f"{perceptron.training_time:<10.3f} | "
                f"{is_linear:^10}"
            )
    
    summary_lines.extend([
        "-" * 70,
        "✓ - линейно разделима   ✗ - нелинейно разделима",
        "=" * 70
    ])
    
    print("\n".join(summary_lines))


def main():
    
    main_header = [
        "=" * 70,
        "ПЕРЦЕПТРОН ДЛЯ ЛОГИЧЕСКИХ ФУНКЦИЙ".center(70),
        "=" * 70,
        "\nДемонстрация работы однослойного перцептрона",
        "и его ограничений на примере логических функций."
    ]
    print("\n".join(main_header))
    
    gates_to_test = [LogicGate.AND, LogicGate.OR, LogicGate.NAND, LogicGate.XOR]
    trained_perceptrons = []
    
    for gate in gates_to_test:
        if gate != LogicGate.XOR:
            perceptron = run_experiment(
                gate_type=gate,
                learning_rate=0.2,
                epochs=20,
                verbose=True
            )
            trained_perceptrons.append((gate.value, perceptron))
        else:
            demonstrate_xor_limitation()
    
    print_summary_table(trained_perceptrons)
    
    conclusion = [
        "\n" + "=" * 70,
        "ЗАКЛЮЧЕНИЕ".center(70),
        "=" * 70,
        "✅ Однослойный перцептрон успешно обучается линейно разделимым функциям.",
        "❌ Для нелинейно разделимых функций (XOR) требуется многослойная сеть.",
        "=" * 70
    ]
    print("\n".join(conclusion))


if __name__ == "__main__":
    main()
