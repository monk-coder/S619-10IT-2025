"""Точка входа в приложение"""
from config import get_config
from data.loader import load_mnist
from network.mlp import MLP
from optimizers.sgd import SGD
from training.trainer import Trainer
from visualization.plots import plot_history, plot_confusion
from sklearn.metrics import classification_report

def main():
    cfg = get_config()
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = load_mnist()
    
    # Создаем модель
    layer_sizes = [784] + cfg.hidden + [10]
    model = MLP(layer_sizes, reg_lambda=cfg.reg)
    optimizer = SGD(lr=cfg.lr)
    
    # Обучение
    trainer = Trainer(model, optimizer, X_train, y_train, X_val, y_val, cfg.batch_size)
    history = trainer.train(cfg.epochs)
    
    # Оценка
    test_acc = model.score(X_test, y_test)
    y_pred = model.predict(X_test)
    print(f"\nTest accuracy: {test_acc:.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred, digits=4))
    
    # Визуализация
    plot_history(history, 'history.png' if cfg.save_plots else None)
    plot_confusion(y_test, y_pred, 'confusion.png' if cfg.save_plots else None)

if __name__ == '__main__':
    main()