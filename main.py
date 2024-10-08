import re
from datetime import datetime
from csv import DictWriter
from bs4 import BeautifulSoup
from requests import get

new = '/feed/'
max_posts = 10  # Ограничиваем количество записей до 10
count = 0  # Инициализируем счётчик для отслеживания количества новостей

# Открываем файл для записи данных в формате CSV
with open('base.csv', mode='w', encoding='utf8') as f:
    # Создаем объект DictWriter с заданными именами полей
    writer = DictWriter(f, fieldnames=['date', 'title', 'link', 'text'], delimiter=';')
    writer.writeheader()  # Записываем заголовки в файл

    # Цикл для парсинга страниц
    while new and count < max_posts:  # Работает, пока есть новые страницы и пока не достигли лимита
        row = {}  # Словарь для хранения данных одной новости
        try:
            # Выполняем HTTP GET-запрос к текущему URL с тайм-аутом
            res = get(f'https://pythondigest.ru{new}', timeout=10)
            if res.status_code != 200:  # Проверяем, успешно ли выполнен запрос
                print(f"Ошибка запроса: {res.status_code}")  # Выводим сообщение об ошибке
                break  # Прерываем цикл при ошибке
        except Exception as e:
            print(f"Ошибка при выполнении запроса: {e}")  # Выводим сообщение об исключении
            break  # Прерываем цикл при возникновении исключения

        soup = BeautifulSoup(res.text, 'html.parser')  # Парсим HTML контент

        # Ищем контейнеры с новостями
        for tag in soup.find_all('div', class_='item-container'):
            # Находим элемент, содержащий заголовок (предположительно, с атрибутом rel)
            title_tag = tag.find(rel=['nofollow'])
            if title_tag:
                row['title'] = title_tag.get_text(strip=True)  # Записываем заголовок
                row['link'] = title_tag.get('href')  # Записываем ссылку на новость
            else:
                row['title'] = "Нет заголовка"  # Если заголовка нет
                row['link'] = "Нет ссылки"  # Если ссылки нет

            # Находим элемент, содержащий дату
            date_tag = tag.find('small')
            if date_tag:
                d1 = re.search(r'\d{2}\.\d{2}\.\d{4}', date_tag.get_text())  # Ищем дату по шаблону
                if d1:
                    d2 = datetime.strptime(d1[0], '%d.%m.%Y').date()  # Преобразуем строку в дату
                    row['date'] = d2  # Записываем дату
                else:
                    row['date'] = "Нет даты"  # Если дата не найдена
            else:
                row['date'] = "Нет даты"  # Если элемента с датой нет

            # Собираем текст новости из всех параграфов
            text_paragraphs = tag.find_all('p')
            row['text'] = ''.join([x.get_text(strip=True) for x in
                                   text_paragraphs]) if text_paragraphs else "Нет текста"  # Записываем текст

            writer.writerow(row)  # Записываем строку в CSV файл
            count += 1  # Увеличиваем счётчик на 1

            if count >= max_posts:  # Проверяем, достигли ли лимита
                break  # Выходим из цикла, если достигли лимита

        # Обрабатываем пагинацию
        pagination = soup.find('ul', class_='pagination pagination-sm')  # Ищем элемент пагинации
        if pagination:
            links = pagination.find_all('li')  # Находим все элементы пагинации
            if links:
                new = links[-1].a.get('href')  # Получаем ссылку на следующую страницу (последнюю)
                # Проверка на наличие нового URL для пагинации
                if not new or new == '#':
                    break  # Если нет новой ссылки или она не действительна, выходим из цикла
            else:
                break  # Если не найдены элементы пагинации, выходим из цикла
        else:
            break  # Если не найдена пагинация, выходим из цикла

            # Выводим сообщение о завершении
        print("Парсинг завершен. Результаты сохранены в файл 'base.csv'.")

