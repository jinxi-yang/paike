with open('index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '待定' in line:
            print(f"{i+1}: {line.strip()[:150]}")
