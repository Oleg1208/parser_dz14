import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from bs4 import BeautifulSoup
from requests import get
import re
from datetime import datetime
from csv import DictWriter
TOKEN = 'your_bot_token'  # Вставьте ваш токен бота
# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# Функция для запуска парсинга
def run_parser():
    new = '/feed/'
    max_posts = 10
    count = 0
    results = []

    try:
        with open('base.csv', mode='w', encoding='utf8') as f:
            writer = DictWriter(f, fieldnames=['date', 'title', 'link', 'text'], delimiter=';')
            writer.writeheader()

            while new and count < max_posts:
                row = {}
                res = get(f'https://pythondigest.ru{new}', timeout=10)
                if res.status_code != 200:
                    break

                soup = BeautifulSoup(res.text, 'html.parser')

                for tag in soup.find_all('div', class_='item-container'):
                    title_tag = tag.find(rel=['nofollow'])
                    row['title'] = title_tag.get_text(strip=True) if title_tag else "Нет заголовка"
                    row['link'] = title_tag.get('href') if title_tag else "Нет ссылки"

                    date_tag = tag.find('small')
                    if date_tag:
                        d1 = re.search(r'\d{2}\.\d{2}\.\d{4}', date_tag.get_text())
                        row['date'] = datetime.strptime(d1[0], '%d.%m.%Y').date() if d1 else "Нет даты"
                    else:
                        row['date'] = "Нет даты"

                    text_paragraphs = tag.find_all('p')
                    row['text'] = ''.join(
                        [x.get_text(strip=True) for x in text_paragraphs]) if text_paragraphs else "Нет текста"

                    writer.writerow(row)
                    results.append(row)
                    count += 1

                    if count >= max_posts:
                        break

                pagination = soup.find('ul', class_='pagination pagination-sm')
                if pagination:
                    links = pagination.find_all('li')
                    new = links[-1].a.get('href') if links else None
                    if not new or new == '#':
                        break
                else:
                    break
    except Exception as e:
        return f"Ошибка при парсинге: {e}"

    return results


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Я бот-парсер. Введи /help, чтобы узнать, что я могу.")


# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "/start - Приветствие\n"
        "/help - Список команд\n"
        "/parse - Запуск парсера\n"
        "/results - Получить последние результаты"
    )
    await update.message.reply_text(help_text)


# Команда /parse
async def parse(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Начинаю парсинг...")
    results = run_parser()
    if isinstance(results, str):
        await update.message.reply_text(results)
    else:
        await update.message.reply_text(f"Парсинг завершен. Найдено {len(results)} записей.")


# Команда /results
async def results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        with open('base.csv', encoding='utf8') as f:
            lines = f.readlines()
            if len(lines) > 1:
                await update.message.reply_text(''.join(lines[1:11]))
            else:
                await update.message.reply_text("Результаты еще не созданы. Запустите /parse для начала.")
    except FileNotFoundError:
        await update.message.reply_text("Файл результатов не найден. Сначала запустите /parse.")


if __name__ == '__main__':
    application = ApplicationBuilder().token('TOKEN').build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("parse", parse))
    application.add_handler(CommandHandler("results", results))

    application.run_polling()
