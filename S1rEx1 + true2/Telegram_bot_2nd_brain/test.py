# Анализ книг

books = []
def get_book():
    book = ()
    name = str(input("Введите название книги(или стоп): "))
    if name == "стоп":
        print_results()
    author = str(input("Введите автора книги: "))
    pages = int(input("Введите количество страниц: "))
    book = (name, author, pages)
    books.append(book)

def print_results(books):
    for book in books:
        for name, author, pages in book:
            