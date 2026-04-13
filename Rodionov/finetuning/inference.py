import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import argparse


class LlamaSQuADInference:
    def __init__(self, model_path="your-username/squad-llama-lora"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Загружаем базовую модель
        base_model_name = "meta-llama/Llama-3.2-1B"
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token

        # Загружаем модель с LoRA адаптерами
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )

        self.model = PeftModel.from_pretrained(base_model, model_path)
        self.model.eval()

    def predict(self, context, question):
        prompt = f"""Context: {context}

Question: {question}

Answer:"""

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.1,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id
            )

        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        answer = generated_text.split("Answer:")[-1].strip()

        return answer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default="your-username/squad-llama-lora")
    args = parser.parse_args()

    inference = LlamaSQuADInference(args.model_path)

    # Тестовые примеры из SQuAD 2.0 validation set
    test_examples = [
        {
            "context": "The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, France. It is named after the engineer Gustave Eiffel, whose company designed and built the tower. Constructed from 1887 to 1889 as the entrance to the 1889 World's Fair, it was initially criticized by some of France's leading artists and intellectuals for its design, but it has become a global cultural icon of France and one of the most recognizable structures in the world.",
            "question": "Who designed the Eiffel Tower?"
        },
        {
            "context": "The Apollo program, also known as Project Apollo, was the third United States human spaceflight program carried out by NASA, which succeeded in landing the first humans on the Moon from 1969 to 1972. It was first conceived during Dwight D. Eisenhower's administration as a three-person spacecraft to follow the one-person Project Mercury.",
            "question": "How many people could the Apollo spacecraft carry?"
        },
        {
            "context": "Python is an interpreted, high-level and general-purpose programming language. Created by Guido van Rossum and first released in 1991, Python's design philosophy emphasizes code readability with its notable use of significant whitespace.",
            "question": "What is the capital of France?"
        }
    ]

    for i, example in enumerate(test_examples, 1):
        print(f"\nExample {i}:")
        print(f"Question: {example['question']}")
        answer = inference.predict(example['context'], example['question'])
        print(f"Answer: {answer}")


if __name__ == "__main__":
    main()