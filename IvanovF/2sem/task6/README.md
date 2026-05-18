# Llama-3.2-1B + LoRA — SQuAD 2.0 QA

**Модель на HuggingFace:** https://huggingface.co/truettwo/task6

---

## Результаты

| Метод           |     F1     | Exact Match |
|-----------------|:----------:|:-----------:|
| Zero-shot       |   8.28%    |    4.0%     |
| Few-shot (5)    |   0.0%     |    0.0%     |
| **LoRA (наша)** | **61.63%** |  **43.0%**  |

> Оценка на 200 примерах из SQuAD 2.0 validation.  
> Улучшение F1 vs zero-shot: **+53.35%**  
> Few-shot показал 0% — длинный prefix обрезал контекст до лимита 512 токенов.

---

## Структура проекта

```
finetuning/
├── finetune_squad.ipynb   # обучение (Google Colab T4)
├── inference.py           # локальный запуск: 3 демо + интерактив
├── evaluate.py            # метрики F1 / Exact Match
├── requirements.txt
└── README.md
```

---

## Быстрый старт

```bash
pip install -r requirements.txt

# Демо — 3 вопроса из SQuAD 2.0 val
python inference.py --adapter your-username/squad-llama-lora

# Интерактивный режим
python inference.py --adapter your-username/squad-llama-lora --interactive

# Полная оценка (zero-shot + few-shot + LoRA)
python evaluate.py --adapter your-username/squad-llama-lora --mode all --n 500
```

---

## Конфигурация обучения

| Параметр        | Значение                              |
|-----------------|---------------------------------------|
| Base model      | `meta-llama/Llama-3.2-1B`            |
| Quantization    | NF4 4-bit (QLoRA)                    |
| LoRA rank `r`   | 16                                    |
| LoRA alpha      | 32                                    |
| Target modules  | q, k, v, o, gate, up, down proj      |
| `max_steps`     | 500                                   |
| Batch size      | 4 (grad_accum=2 → effective 8)       |
| Learning rate   | 2e-4                                  |
| LR scheduler    | cosine                                |
| Warmup          | 50 steps (10%)                        |
| Optimizer       | adamw_8bit                            |
| Train examples  | 10 000                                |
| Время на T4     | ~40 минут                             |

---

## Промпт-шаблон

```
### Context:
{context}

### Question:
{question}

### Answer:
{answer}
```

Loss считается **только по токенам ответа** — промпт маскируется через `labels = -100`.

---

## Ответы на вопросы защиты

### Зачем LoRA вместо full fine-tuning?

Full fine-tuning Llama-3.2-1B (~1.2B параметров) требует ~16 GB VRAM только под оптимизатор AdamW (2 момента × fp32 × 1.2B параметров). T4 имеет 16 GB всего — не влезает даже без активаций и батча.

LoRA замораживает базовые веса и добавляет низкоранговые матрицы `ΔW = A·Bᵀ`, где `A ∈ ℝ^{d×r}`, `B ∈ ℝ^{r×k}`. При `r=16` обучается лишь ~1% параметров: всё помещается в память, обучение в 3–5× быстрее, нет catastrophic forgetting базовых знаний модели.

### Как 4-bit quantization влияет на качество?

Используется NF4 (NormalFloat4) — оптимальное квантование для нормально распределённых весов LLM. Потеря качества составляет менее 1–2% F1 по сравнению с fp16, потому что:

- вычисления (forward / backward pass) остаются в fp16 — квантуется только **хранение** весов
- меньший размер модели позволяет взять больший batch, что частично компенсирует потерю точности
- double quantization дополнительно квантует константы квантования → экономия ещё ~0.4 GB

### Что такое rank `r` в LoRA и как его выбрать?

Ранг `r` — размерность внутреннего пространства адаптера. Матрица `ΔW = A·Bᵀ` имеет ранг не более `r`, то есть это low-rank approximation полного дообучения. Чем больше `r` — тем выразительнее адаптер, но тем больше обучаемых параметров.

Практические ориентиры:

| Диапазон   | Когда использовать                          |
|------------|---------------------------------------------|
| `r = 4–8`  | Простые задачи: классификация, перефразирование |
| `r = 16–32`| **Наш случай**: экстракция ответов (QA)     |
| `r = 64–128` | Сложная генерация, instruction tuning     |

Выбирают по ablation на val loss. `alpha = 2×r` — стандартное соотношение: `alpha` масштабирует `ΔW` и не зависит от конкретного значения `r`.