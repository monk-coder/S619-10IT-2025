import re, string
from collections import Counter
from datasets import load_dataset

def normalize_answer(s):
    def remove_articles(t): return re.sub(r'\b(a|an|the)\b', ' ', t)
    def white_space_fix(t): return ' '.join(t.split())
    def remove_punc(t): return ''.join(c for c in t if c not in string.punctuation)
    return white_space_fix(remove_articles(remove_punc(s.lower())))

def f1_score(pred, gt):
    pred_t, gt_t = normalize_answer(pred).split(), normalize_answer(gt).split()
    common = Counter(pred_t) & Counter(gt_t)
    num_same = sum(common.values())
    if num_same == 0: return 0.0
    p, r = num_same/len(pred_t), num_same/len(gt_t)
    return 2*p*r/(p+r) if p+r > 0 else 0.0

def predict(context, question):
    prompt = f"Context: {context}\nQuestion: {question}\nAnswer:"
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=64, pad_token_id=tokenizer.eos_token_id)
    return tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()

model.eval()
val = load_dataset("squad_v2", split="validation").select(range(20))
f1s, ems = [], []

print("🔍 Оценка на 20 примерах...")
for ex in val:
    gt = ex["answers"]["text"][0] if ex["answers"]["text"] else "unknown"
    pred = predict(ex["context"], ex["question"])
    f1s.append(f1_score(pred, gt))
    ems.append(1.0 if normalize_answer(pred) == normalize_answer(gt) else 0.0)

print(f"\n{'='*50}")
print(f"RESULTS (n=20):")
print(f"F1 Score:      {sum(f1s)/len(f1s)*100:.2f}%")
print(f"Exact Match:   {sum(ems)/len(ems)*100:.2f}%")
print(f"{'='*50}")