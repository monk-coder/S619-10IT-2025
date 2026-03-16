def plot_history(history, save_path=None):
    # ... ваш код построения графиков ...
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"График сохранён: {save_path}")
    plt.show()

def plot_confusion_matrix(cm, save_path=None):
    # ... ваш код матрицы ошибок ...
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Матрица ошибок сохранена: {save_path}")
    plt.show()