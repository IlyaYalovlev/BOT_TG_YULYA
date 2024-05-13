import telebot
from telebot import types
import schedule
import time
import psycopg2
from psycopg2 import Error
from openpyxl import Workbook
import os
from dotenv import load_dotenv

# Загрузка переменных среды из файла .env
load_dotenv()

# Получение значений переменных среды
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


bot = telebot.TeleBot(BOT_TOKEN)

# Функция для отправки сообщения "найдёшь для меня минутку?"
def send_reminder(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = types.KeyboardButton('Да!')
    item2 = types.KeyboardButton('Нет')

    markup.add(item1, item2)

    bot.send_message(user_id, "Найдёшь для меня минутку?", reply_markup=markup)

# Функция для планирования напоминания
def remind_later(message):
    # Запланировать отправку напоминания через 24 часа
    schedule.every().day.at("14:00").do(send_reminder, message.from_user.id)

    bot.send_message(message.chat.id, "Хорошо, напомню завтра в 14:00.", reply_markup=types.ReplyKeyboardRemove(selective=False))

# Обработчик ответа на вопрос "Найдёшь для меня минутку?"
@bot.message_handler(func=lambda message: message.text == 'Да!' or message.text == 'Нет')
def handle_minutes(message):
    if message.text == 'Да!':
        bot.send_message(message.chat.id, "Отлично! Как тебя зовут?")
        bot.register_next_step_handler(message, process_name_step)
    elif message.text == 'Нет':
        remind_later(message)

# Стартовое сообщение
@bot.message_handler(commands=['start'])
def main(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = types.KeyboardButton('Поехали!')
    item2 = types.KeyboardButton('Давай попозже.')
    markup.add(item1, item2)

    bot.send_message(message.chat.id, 'Привет! \nДавай познакомимся, сейчас я задам тебе несколько вопросов.',
                     reply_markup=markup)

# Обработчик ответа на вопрос "Поехали!"
@bot.message_handler(func=lambda message: message.text == 'Поехали!')
def handle_go(message):
    markup = types.ReplyKeyboardRemove(selective=False)

    bot.send_message(message.chat.id, 'Отлично! Как тебя зовут?', reply_markup=markup)
    bot.register_next_step_handler(message, process_name_step)

# Запись имени в бд
def process_name_step(message):
    name = message.text
    user_id = message.from_user.id
    username = message.from_user.username

    # Соединение с базой данных
    connection = connect_to_db()
    if connection is not None:
        try:
            cursor = connection.cursor()
            postgres_insert_query = """INSERT INTO users (name, user_id, username) VALUES (%s, %s, %s)"""
            record_to_insert = (name, user_id, username)
            cursor.execute(postgres_insert_query, record_to_insert)
            connection.commit()
            print("Информация о пользователе успешно сохранена в базе данных")
        except (Exception, psycopg2.Error) as error:
            print("Ошибка при выполнении запроса к базе данных:", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
                print("Соединение с базой данных закрыто")
    else:
        print("Не удалось подключиться к базе данных")

    bot.send_message(message.chat.id, f'Приятно познакомиться, {name}!')

    # Задаем вопрос о возрасте
    bot.send_message(message.chat.id, 'Сколько тебе лет?')
    bot.register_next_step_handler(message, process_age_step)

# Запись возраста в бд
def process_age_step(message):
    age = message.text

    # Соединение с базой данных
    connection = connect_to_db()
    if connection is not None:
        try:
            cursor = connection.cursor()
            postgres_update_query = """UPDATE users SET age = %s WHERE user_id = %s"""
            record_to_update = (age, message.from_user.id)
            cursor.execute(postgres_update_query, record_to_update)
            connection.commit()
            print("Возраст успешно сохранен в базе данных")
        except (Exception, psycopg2.Error) as error:
            print("Ошибка при выполнении запроса к базе данных:", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
                print("Соединение с базой данных закрыто")
    else:
        print("Не удалось подключиться к базе данных")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item = types.KeyboardButton("Поделиться контактом", request_contact=True)
    markup.add(item)
    bot.send_message(message.chat.id, "Поделись, пожалуйста, своим контактом.", reply_markup=markup)
    bot.register_next_step_handler(message, process_contact_step)

# Запись города в бд
def process_contact_step(message):
    contact = message.contact
    c1 = f"{contact.first_name} {contact.last_name}, {contact.phone_number}"
    # Соединение с базой данных
    connection = connect_to_db()
    if connection is not None:
        try:
            cursor = connection.cursor()
            postgres_update_query = """UPDATE users SET city = %s WHERE user_id = %s"""
            record_to_update = (c1, message.from_user.id)
            cursor.execute(postgres_update_query, record_to_update)
            connection.commit()
            print("Город успешно сохранен в базе данных")
        except (Exception, psycopg2.Error) as error:
            print("Ошибка при выполнении запроса к базе данных:", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
                print("Соединение с базой данных закрыто")
    else:
        print("Не удалось подключиться к базе данных")

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = types.KeyboardButton('IT')
    item2 = types.KeyboardButton('Маркетинг')
    item3 = types.KeyboardButton('Продюсирование')
    item4 = types.KeyboardButton('Бьюти')
    item5 = types.KeyboardButton('Фешн')
    item6 = types.KeyboardButton('Другое')

    # Добавляем кнопки в клавиатуру
    markup.add(item1, item2, item3, item4, item5, item6)
    # Задаем вопрос о Нише
    bot.send_message(message.chat.id, 'В какой нише ты сейчас работаешь?',  reply_markup=markup)
    bot.register_next_step_handler(message, process_industry_step)

# Запись ниши в бд
def process_industry_step(message):
    industry = message.text

    # Соединение с базой данных
    connection = connect_to_db()
    if connection is not None:
        try:
            cursor = connection.cursor()
            postgres_update_query = """UPDATE users SET industry = %s WHERE user_id = %s"""
            record_to_update = (industry, message.from_user.id)
            cursor.execute(postgres_update_query, record_to_update)
            connection.commit()
            print("Ниша успешно сохранена в базе данных")
        except (Exception, psycopg2.Error) as error:
            print("Ошибка при выполнении запроса к базе данных:", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
                print("Соединение с базой данных закрыто")
    else:
        print("Не удалось подключиться к базе данных")

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = types.KeyboardButton('0-50т.руб.')
    item2 = types.KeyboardButton('50-150т.руб.')
    item3 = types.KeyboardButton('150-500т.руб.')
    item4 = types.KeyboardButton('500+т.руб.')


    # Добавляем кнопки в клавиатуру
    markup.add(item1, item2, item3, item4)
    # Задаем вопрос о доходе
    bot.send_message(message.chat.id, 'Сколько в среднем ты сейчас зарабатываешь?', reply_markup=markup)
    bot.register_next_step_handler(message, process_income_step)

# Запись дохода в бд
def process_income_step(message):
    income = message.text

    # Соединение с базой данных
    connection = connect_to_db()
    if connection is not None:
        try:
            cursor = connection.cursor()
            postgres_update_query = """UPDATE users SET income_range = %s WHERE user_id = %s"""
            record_to_update = (income, message.from_user.id)
            cursor.execute(postgres_update_query, record_to_update)
            connection.commit()
            print("Доход успешно сохранен в базе данных")
        except (Exception, psycopg2.Error) as error:
            print("Ошибка при выполнении запроса к базе данных:", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
                print("Соединение с базой данных закрыто")
    else:
        print("Не удалось подключиться к базе данных")

    markup = types.ReplyKeyboardRemove(selective=False)
    # Отправляем сообщение о запросе адреса электронной почты
    bot.send_message(message.chat.id,
                         'Спасибо за твои ответы! Теперь подскажи мне свою почту, чтобы я мог отправить тебе подарок за прохождение опроса.',  reply_markup=markup)

    # Регистрируем следующий шаг для обработки адреса электронной почты
    bot.register_next_step_handler(message, process_email_step)



def process_email_step(message):
        email = message.text
        # Здесь можно выполнить любую дополнительную обработку адреса электронной почты,
        # например, проверку его формата или отправку подтверждения

        # В данном примере мы просто сохраняем адрес в базе данных
        # Соединение с базой данных
        connection = connect_to_db()
        if connection is not None:
            try:
                cursor = connection.cursor()
                postgres_update_query = """UPDATE users SET email = %s WHERE user_id = %s"""
                record_to_update = (email, message.from_user.id)
                cursor.execute(postgres_update_query, record_to_update)
                connection.commit()
                print("Email успешно сохранен в базе данных")
            except (Exception, psycopg2.Error) as error:
                print("Ошибка при выполнении запроса к базе данных:", error)
            finally:
                if connection:
                    cursor.close()
                    connection.close()
                    print("Соединение с базой данных закрыто")
        else:
            print("Не удалось подключиться к базе данных")
        bot.send_message(message.chat.id, 'Спасибо, в ближайшее время пришлю тебе урок.')

# Функция для подключения к базе данных
def connect_to_db():
    try:
        # Указываем параметры подключения к вашей локальной базе данных
        connection = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        print("Подключение к базе данных успешно")
        return connection
    except (Exception, Error) as error:
        print("Ошибка при подключении к базе данных:", error)
        return None


# Функция для извлечения данных из базы данных и сохранения их в Excel-файл
def save_database_to_excel():
    # Подключение к базе данных
    connection = connect_to_db()
    if connection is not None:
        try:
            cursor = connection.cursor()
            # Выполнение запроса к базе данных
            cursor.execute("SELECT * FROM users")
            # Получение результатов запроса
            rows = cursor.fetchall()
            # Создание нового файла Excel
            wb = Workbook()
            ws = wb.active
            # Запись данных в файл Excel
            for row_index, row in enumerate(rows, start=1):
                for col_index, value in enumerate(row, start=1):
                    ws.cell(row=row_index, column=col_index, value=value)
            # Сохранение файла Excel
            wb.save("users_data.xlsx")
            print("Данные успешно сохранены в Excel-файл")
        except (Exception, psycopg2.Error) as error:
            print("Ошибка при выполнении запроса к базе данных:", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
                print("Соединение с базой данных закрыто")
    else:
        print("Не удалось подключиться к базе данных")

# Обработчик команды от пользователя для запроса данных из базы данных и отправки Excel-файла
@bot.message_handler(func=lambda message: (message.from_user.id == 1793440675 or message.from_user.id == 453421227) and message.text.lower() == 'база')
def send_data_to_excel(message):
    # Вызов функции для сохранения данных в Excel
    save_database_to_excel()
    # Отправка Excel-файла пользователю
    with open("users_data.xlsx", "rb") as file:
        bot.send_document(message.chat.id, file)

if __name__ == "__main__":
    connect_to_db()

# Начать опрос сообщений без остановки
bot.polling(non_stop=True, timeout=30)

# Периодическая проверка расписания
while True:
    schedule.run_pending()
    time.sleep(1)
