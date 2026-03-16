python
import urllib.request
import os

print("Скачивание MNIST...")
os.makedirs('data', exist_ok=True)

urls = [
    ('train-images-idx3-ubyte.gz', 'http://yann.lecun.com/exdb/mnist/train-images-idx3-ubyte.gz'),
    ('train-labels-idx1-ubyte.gz', 'http://yann.lecun.com/exdb/mnist/train-labels-idx1-ubyte.gz'),
    ('t10k-images-idx3-ubyte.gz', 'http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz'),
    ('t10k-labels-idx1-ubyte.gz', 'http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz')
]

for filename, url in urls:
    filepath = os.path.join('data', filename)
    if not os.path.exists(filepath):
        print(f'  Скачиваю {filename}...')
        try:
            urllib.request.urlretrieve(url, filepath)
            print(f'    Готово!')
        except:
            print(f'    Ошибка, пропускаю...')
    else:
        print(f'  {filename} уже есть')

print("\nПроверка файлов в data/:")
for f in os.listdir('data'):
    print(f"  - {f}")