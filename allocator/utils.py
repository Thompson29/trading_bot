def summarize_allocation(allocation: dict):
    for etf, amount in allocation.items():
        print(f"{etf}: ${amount}")

def calculate_diffs(current_alloc, target_alloc, total_value):
    diffs = {}
    for symbol, target_pct in target_alloc.items():
        current_value = current_alloc.get(symbol, 0)
        target_value = total_value * target_pct
        diffs[symbol] = round(target_value - current_value, 2)
    return diffs