def save(self, path):
    """Сохранение весов модели"""
    weights = {}
    biases = {}
    for i, layer in enumerate(self.layers):
        if hasattr(layer, 'W'):  # Dense слой
            weights[f'W{i}'] = layer.W
            biases[f'b{i}'] = layer.b
    np.savez(path, **weights, **biases)
    print(f"Модель сохранена в {path}")