import re
import string
from collections import Counter

def normalize_answer(s: str) -> str:
    def remove_articles(text): 
        return re.sub(r'\b(a|an|the)\b', ' ', text)
    def white_space_fix(text): 
        return ' '.join(text.split())
    def remove_punc(text): 
        return ''.join(ch for ch in text if ch not in string.punctuation)
    def lower(text): 
        return text.lower()
    return white_space_fix(remove_articles(remove_punc(lower(s))))

def f1_score(prediction: str, ground_truth: str) -> float:
    pred_tokens = normalize_answer(prediction).split()
    gt_tokens = normalize_answer(ground_truth).split()
    common = Counter(pred_tokens) & Counter(gt_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0
    precision = num_same / len(pred_tokens)
    recall = num_same / len(gt_tokens)
    return (2 * precision * recall) / (precision + recall)

def exact_match_score(prediction: str, ground_truth: str) -> float:
    return 1.0 if normalize_answer(prediction) == normalize_answer(ground_truth) else 0.0
