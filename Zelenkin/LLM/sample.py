import torch
import argparse
from model import GPT
from config import Config
import pickle


def load_checkpoint(checkpoint_path, device='cpu'):
    # Добавляем Config в список безопасных глобальных объектов
    torch.serialization.add_safe_globals([Config])

    # Загружаем с weights_only=False для совместимости
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)

    # Создаем конфиг из сохраненного состояния
    config = checkpoint['config']
    model = GPT(config)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()

    return model, checkpoint


def main():
    parser = argparse.ArgumentParser(description='Generate text from trained model')
    parser.add_argument('--checkpoint', type=str, required=True, help='Path to checkpoint')
    parser.add_argument('--prompt', type=str, default='ROMEO:', help='Prompt for generation')
    parser.add_argument('--max_new_tokens', type=int, default=200, help='Maximum tokens to generate')
    parser.add_argument('--temperature', type=float, default=0.8, help='Sampling temperature')
    parser.add_argument('--top_k', type=int, default=50, help='Top-k sampling parameter')
    parser.add_argument('--device', type=str, default='cpu', help='Device to use')

    args = parser.parse_args()

    device = torch.device(args.device if torch.cuda.is_available() and args.device == 'cuda' else 'cpu')

    try:
        model, checkpoint = load_checkpoint(args.checkpoint, device)
        print(f"Loaded checkpoint from iteration {checkpoint.get('iteration', 'unknown')}")
    except FileNotFoundError:
        print(f"Error: Checkpoint file '{args.checkpoint}' not found!")
        print("Please train the model first using: python train.py")
        return
    except Exception as e:
        print(f"Error loading checkpoint: {e}")
        return

    try:
        with open('vocab.pkl', 'rb') as f:
            stoi, itos = pickle.load(f)
    except FileNotFoundError:
        print("Error: Vocabulary file 'vocab.pkl' not found!")
        print("Please train the model first using: python train.py")
        return

    # Проверяем, что промпт не пустой
    if not args.prompt:
        args.prompt = " "

    # Преобразуем промпт в токены
    prompt_tokens = []
    for ch in args.prompt:
        if ch in stoi:
            prompt_tokens.append(stoi[ch])
        else:
            # Если символа нет в словаре, используем 0 (первый символ)
            prompt_tokens.append(0)

    context = torch.tensor([prompt_tokens], dtype=torch.long, device=device)

    print(f"\nPrompt: {args.prompt}")
    print(f"Temperature: {args.temperature}, Top-k: {args.top_k}")
    print("\n" + "=" * 50)

    with torch.no_grad():
        generated = model.generate(
            context,
            args.max_new_tokens,
            temperature=args.temperature,
            top_k=args.top_k
        )

    # Декодируем сгенерированные токены
    generated_text = ''
    for idx in generated[0].tolist():
        if idx in itos:
            generated_text += itos[idx]
        else:
            generated_text += '?'

    print(generated_text)
    print("\n" + "=" * 50)


if __name__ == '__main__':
    main()