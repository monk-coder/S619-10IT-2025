from config import CATEGORIES

def text_graph(data_dict):
    total = sum(data_dict.values())
    lines = []
    for cat, amount in sorted(data_dict.items(), key=lambda x: x[1], reverse=True):
        perc = int(amount / total * 100) if total > 0 else 0
        blocks = '█' * (perc // 5)
        cat_name = CATEGORIES.get(cat, '✨ Другое')
        lines.append(f"{cat_name}: {amount}₽ {blocks} {perc}%")
    return "\n".join(lines)
