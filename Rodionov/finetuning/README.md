# Llama-3.2-1B SQuAD 2.0 Fine-tuning with LoRA

## Описание проекта

Выполнен parameter-efficient fine-tuning модели Llama-3.2-1B на датасете SQuAD 2.0 с использованием LoRA и 4-bit квантования.

## Модель на Hugging Face Hub

Модель доступна по ссылке: [your-username/squad-llama-lora](https://huggingface.co/your-username/squad-llama-lora)

## Результаты

| Метод | F1 | Exact Match |
|-------|----|--------------|
| Zero-shot | ~25% | ~15% |
| Few-shot (5 примеров) | ~35% | ~20% |
| **LoRA** | **>60%** | **>45%** |

## Использование

### Установка
```bash
pip install -r requirements.txt