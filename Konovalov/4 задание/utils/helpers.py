from datetime import datetime, timedelta

def parse_amount(text):
    try:
        amount = float(text.replace(',', '.').replace(' ', ''))
        return round(amount, 2) if amount > 0 else 0
    except:
        return 0

def day_range():
    today = datetime.now()
    start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end

def week_range():
    end = datetime.now()
    start = end - timedelta(days=7)
    return start, end

def month_range():
    today = datetime.now()
    start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = start.replace(month=start.month+1) if start.month < 12 else start.replace(year=start.year+1, month=1)
    end = next_month - timedelta(seconds=1)
    return start, end

def category_info(category):
    for cat in EXPENSE_CATEGORIES:
        if cat[0] == category:
            return {"emoji": cat[1], "name": cat[2]}
    return {"emoji": "📦", "name": category}