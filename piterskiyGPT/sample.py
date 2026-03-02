import numpy as np
import argparse
import pickle
from model import TransformerLM
from bpe import BPETokenizer

def generate(model, tokenizer, prompt, max_new_tokens, temperature=1.0, top_k=None):
    model.eval()
    
    # Токенизируем промпт
    input_ids = np.array(tokenizer.encode(prompt)).reshape(1, -1)
    
    for _ in range(max_new_tokens):
        # Обрезаем до максимальной длины модели
        if input_ids.shape[1] > model.max_seq_len:
            input_ids = input_ids[:, -model.max_seq_len:]
        
        # Forward pass
        logits = model.forward(input_ids)
        
        # Берем логиты последнего токена
        next_token_logits = logits[0, -1, :] / temperature
        
        # Top-k фильтрация
        if top_k is not None:
            indices = np.argpartition(next_token_logits, -top_k)[-top_k:]
            mask = np.ones_like(next_token_logits) * -np.inf
            mask[indices] = next_token_logits[indices]
            next_token_logits = mask
        
        # Softmax для вероятностей
        probs = np.exp(next_token_logits - np.max(next_token_logits))
        probs = probs / np.sum(probs)
        
        # Сэмплируем
        next_token = np.random.choice(len(probs), p=probs)
        
        # Добавляем к последовательности
        input_ids = np.concatenate([input_ids, [[next_token]]], axis=1)
        
        # Декодируем для вывода (опционально)
        yield tokenizer.decode([next_token])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, required=True, help='Prompt for generation')
    parser.add_argument('--max_new_tokens', type=int, default=100)
    parser.add_argument('--temperature', type=float, default=0.8)
    parser.add_argument('--top_k', type=int, default=40)
    parser.add_argument('--model_path', type=str, default='model_params.pkl')
    args = parser.parse_args()
    
    # Загружаем токенизатор
    tokenizer = BPETokenizer()
    tokenizer.load('bpe_model.json')
    
    # Создаем модель с теми же параметрами
    VOCAB_SIZE = 1000
    D_MODEL = 128
    N_HEAD = 4
    N_LAYER = 3
    MAX_SEQ_LEN = 128
    
    model = TransformerLM(
        vocab_size=VOCAB_SIZE,
        d_model=D_MODEL,
        n_head=N_HEAD,
        n_layer=N_LAYER,
        max_seq_len=MAX_SEQ_LEN
    )
    
    # Загружаем параметры
    with open(args.model_path, 'rb') as f:
        params = pickle.load(f)
    
    # Восстанавливаем параметры
    model_params = [p for p, _ in model.get_parameters()]
    for p, loaded_p in zip(model_params, params):
        p[:] = loaded_p
    
    # Генерируем
    print(f'Prompt: {args.prompt}')
    print('Generated: ', end='', flush=True)
    
    for token in generate(model, tokenizer, args.prompt, 
                          args.max_new_tokens, args.temperature, args.top_k):
        print(token, end='', flush=True)
    
    print()
