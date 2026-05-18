import evaluate
from datasets import load_dataset

metric = evaluate.load("squad_v2")

# Здесь нужно написать функцию, которая генерирует ответы модели и сравнивает
# (можно сделать в ноутбуке или отдельно)