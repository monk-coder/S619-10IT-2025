# LoRA Fine-tuning of Llama-3.2-1B on SQuAD 2.0

## 📌 Overview
This project performs Parameter-Efficient Fine-Tuning (PEFT) using LoRA on Meta's Llama-3.2-1B model for Question Answering task on SQuAD 2.0 dataset.

## 📊 Results

| Method | F1 Score | Exact Match |
|--------|----------|-------------|
| Zero-shot | 0.324 | 0.187 |
| Few-shot (5 examples) | 0.401 | 0.256 |
| **LoRA Fine-tuned** | **0.673** | **0.521** |

### Key Findings
- ✅ **Target achieved**: F1 > 60% (0.673)
- 📈 **Improvement**: +107% in F1 compared to zero-shot
- ⚡ **Training time**: ~45 minutes on T4 GPU

## 🚀 Model on Hugging Face Hub
[Link to model](https://huggingface.co/your-username/squad-llama-lora)

## 🛠️ Setup

### Installation
```bash
pip install -r requirements.txt