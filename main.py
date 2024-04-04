import asyncio
from asyncio import exceptions
import aiogram
from aiogram import exceptions
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import state
from aiogram.types.web_app_info import WebAppInfo
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncpg
import config
from config import TOKEN, chat_id_to_forward, admins_id
from database import database_connect
import mysql.connector
import telebot
from aiogram.dispatcher.filters.state import State, StatesGroup

bot = telebot.TeleBot("6286125677:AAG_FPor6xFejfPNDqrz-H9PuKvYZTxJza4")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Обработчик команды "/start"
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    # Подключение базы данных
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("CREATE TABLE IF NOT EXISTS customers (user_id INTEGER, first_name VARCHAR(255), last_name VARCHAR(255), "
                     "UNIQUE (user_id, first_name, last_name))")
    sql = "INSERT IGNORE INTO customers (user_id, first_name, last_name) VALUES (%s, %s, %s)"
    user_id = message.chat.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    val = (user_id, first_name, last_name)
    mycursor.execute(sql, val)
    mydb.commit()

    await message.answer_photo('https://avatars.mds.yandex.net/i?id=26a591ac65a79ae54d1245454dd586987266f988-9690504-images-thumbs&n=13')

    # Добавление кнопок и вступительного текста
    main = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    main.add(types.KeyboardButton('💻 Открыть веб приложение', web_app=WebAppInfo(url='https://carych.ru/')))
    main.add(types.KeyboardButton('🤖 Взаимодействия с ботом'))

    await message.answer(f'👤 {message.from_user.full_name}, добро пожаловать в магазин автозапчастей CARЫЧ!\n\n'
                         '🚙 Мы специализируемся на предоставлении высококачественных автозапчастей, которые помогут вам поддерживать и улучшать ваш автомобиль.\n\n'
                         '❓ Если у вас возникли вопросы или вам требуется помощь, наши эксперты всегда готовы проконсультировать вас.\n\n'
                         'Желаем вам приятного покупательского опыта в нашем магазине!\n\n'
                         '<i>Основные взаимодействия с ботом происходят при помощи кнопок внизу экрана ⬇</i>'
                         ''

                         , reply_markup=main, parse_mode="html")

# Обработчик кнопки 'Взаимодействия с ботом'
@dp.message_handler(text=['🤖 Взаимодействия с ботом'])
async def inline(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🔍 Поиск по каталогу'))
    markup.add(types.KeyboardButton('📝 Сделать заказ'))
    markup.add(types.KeyboardButton('👤 Онлайн-консультант'))
    markup.add(types.KeyboardButton('ℹ Информация о статусе заказа'))
    markup.add(types.KeyboardButton('🧮 Калькулятор стоимости'))
    markup.add(types.KeyboardButton('🗺 Геолокация магазина'
                                , web_app=WebAppInfo(url='https://yandex.ru/maps/54/yekaterinburg/?ll=60.526665%2C56.866304&mode=routes&rtext=~56.866362%2C60.526032&rtt=auto&ruri=~ymapsbm1%3A%2F%2Forg%3Foid%3D14775371131&z=17.74',callback_data="5")))
    markup.add(types.KeyboardButton('🏆 Отзывы и оценки', web_app=WebAppInfo(url='https://yandex.ru/maps/org/karych/14775371131/reviews/?ll=60.525537%2C56.866539&utm_campaign=v1&utm_medium=rating&utm_source=badge&z=16', callback_data="6")))
    markup.add(types.KeyboardButton('◀ Назад'))

    await message.answer('Выберите нужное действие ⬇:', reply_markup=markup)

# обработчик кнопки 'Назад'
@dp.message_handler(text=['◀ Назад'])
async def back(message: types.Message):
    await start(message)
# обработчик кнопки 'Выход' из админ панели
@dp.message_handler(text=['◀ Выход'])
async def back(message: types.Message):
    await start(message)


# Сделать заказ
class OrderForm(StatesGroup):
    entering_product_name = State()
    entering_product_quantity = State()

@dp.message_handler(text=['📝 Сделать заказ'])
async def phone_number(message: types.Message):
    await message.answer('Введите название товара чтобы добавить его в заказ:')
    await OrderForm.entering_product_name.set()
    if message.text == '◀ Назад':
        await state.finish()
        await start(message)

@dp.message_handler(state=OrderForm.entering_product_name)
async def enter_product_name(message: types.Message, state: FSMContext):
    # Сохраняем название товара
    await state.update_data(product_name=message.text)

    # Переводим пользователя в состояние ввода количества товара
    await message.answer('Введите количество товара:')
    await OrderForm.entering_product_quantity.set()

    if message.text == '◀ Назад':
        await state.finish()
        await start(message)


@dp.message_handler(state=OrderForm.entering_product_quantity)
async def enter_product_quantity(message: types.Message, state: FSMContext):
    # Сохраняем количество товара
    await state.update_data(product_quantity=message.text)
    # Получаем все данные из состояния
    data = await state.get_data()
    product_name = data.get('product_name')
    product_quantity = data.get('product_quantity')
    telegram_id = message.from_user.id
    customer_name = message.from_user.first_name
    # Подключаемся к базе данных
    mydb = database_connect
    mycursor = mydb.cursor()
    # Выполняем запрос с использованием параметров для корректной подстановки значений
    sql = "INSERT INTO orders (product_name, product_quantity, product_status, payment_status, TelegramID, CustomerName) VALUES (%s, %s, 'В обработке', 'Ожидается оплата', %s, %s)"
    values = (product_name, product_quantity, telegram_id, customer_name)
    mycursor.execute(sql, values)
    # Фиксируем изменения в базе данных
    mydb.commit()
    # Возвращаем пользователя в обычное состояние и завершаем добавление заказа
    mycursor.execute("SELECT order_id FROM orders ORDER BY order_id DESC LIMIT 1")
    last_order_id = mycursor.fetchone()[0]

    # Отправляем сообщение с номером заказа
    await message.answer(f'✅ Заказ успешно добавлен!'
                         f'\n\nВаш номер заказа: <code>{last_order_id}</code>'
                         f'\n\nЧтобы проверить статус вашего заказа нажмите на кнопку "ℹ Информация о статусе заказа"'
                         f'\n\nДля оплаты заказа нажмите: \n/payment', parse_mode="html")

    # Уведомления о поступлении нового заказа
    await bot.send_message(chat_id=chat_id_to_forward, text="❗ Поступил новый заказ ❗"
                                                            "\n\nПроверьте вкладку '📝 Просмотр заказов' через админ панель /admin")
    if message.text == '◀ Назад':
        await state.finish()
        await start(message)

    # Очищаем данные из состояния
    await state.reset_state()

class PhoneNumberState(StatesGroup):
    waiting_for_phone_number = State()

@dp.message_handler(text=['📱 Добавить номер телефона в базу'])
async def phone_number(message: types.Message):
    await message.answer('Введите свой номер телефона чтобы добавить его в базу:'
                         '\n(<i>Например: +78005553535</i>)', parse_mode='html')
    await PhoneNumberState.waiting_for_phone_number.set()


@dp.message_handler(state=PhoneNumberState.waiting_for_phone_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    phone_number = message.text
    # Получить информацию о пользователе по telegram id
    user_id = message.from_user.id
    mydb = database_connect
    mycursor = mydb.cursor()
    # Проверяем существование пользователя
    mycursor.execute("SELECT * FROM customers WHERE user_id=%s", (user_id,))
    user = mycursor.fetchone()

    if user:  # Если пользователь существует
        # выполнить SQL-запрос для добавления номера телефона в колонку phone
        mycursor.execute("UPDATE customers SET phone=%s WHERE user_id=%s", (phone_number, user_id))
        mydb.commit()

        await message.answer('Номер телефона успешно добавлен в базу данных!')
    else:
        await message.answer('Пользователь не найден.')

    # Деактивируем состояние
    await state.finish()


# Обработчик кнопки 'Онлайн-консультант'
@dp.message_handler(text=['👤 Онлайн-консультант'])
async def support(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🔵 Отправить контакт', request_contact=True))
    markup.add(types.KeyboardButton('📱 Добавить номер телефона в базу'))
    markup.add(types.KeyboardButton('◀ Назад'))

    await message.answer('Для связи с консультантом отправьте свой контакт нажатием на кнопку внизу экрана ⬇', reply_markup=markup)

# Обработчик ответа на отправленный контакт
@dp.message_handler(content_types=types.ContentType.CONTACT)
async def handle_contact(message: types.Message):
    await message.answer(f'{message.from_user.full_name}, спасибо что оставили заявку!\n\nКонсультант свяжется с вами в ближайшее время.')

    if message.forward_from is None:
        # Получаем контакт
        contact = message.contact

        # Отправляем контакт другому пользователю
        await bot.send_contact(chat_id=chat_id_to_forward, phone_number=contact.phone_number, first_name=contact.first_name,
                               last_name=contact.last_name)


# Обработчик команды "/admin"
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    # Проверяем, является ли отправитель администратором (можно добавить свою логику проверки)
    if message.from_user.id == admins_id:
        # Создаем InlineKeyboardMarkup с кнопками действий
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(types.KeyboardButton("📊 Статистика"))
        markup.add(types.KeyboardButton("✉ Рассылка"))
        markup.add(types.KeyboardButton("📦 Склад"))
        markup.add(types.KeyboardButton("📝 Изменение информации о статусе заказа"))
        markup.add(types.KeyboardButton("📝 Изменение стоимости заказа"))
        markup.add(types.KeyboardButton("📝 Просмотр заказов"))
        markup.add(types.KeyboardButton("📝 Удаление заказов"))
        markup.add(types.KeyboardButton("◀ Выход"))
        await message.reply("✅ Вы вошли в админ панель!", reply_markup=markup)
    else:
        await message.reply("🚫 У вас нет прав для входа в админ панель!")


class DeleteState(StatesGroup):
    waiting_order_id = State()

@dp.message_handler(text=["📝 Удаление заказов"])
async def stats(message: types.Message):
    await message.answer('Введите номер заказа, чтобы удалить его:')
    await DeleteState.waiting_order_id.set()

@dp.message_handler(state=DeleteState.waiting_order_id)
async def process_order_id(message: types.Message, state: FSMContext):
    order_id = message.text
    # Проверяем, есть ли введенный order_id в базе данных
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM `orders` WHERE order_id = %s;", (order_id,))
    result = mycursor.fetchall()

    if len(result) > 0:
       # Удаляем все данные с данным order_id из базы данных
       mycursor.execute("DELETE FROM `orders` WHERE order_id = %s;", (order_id,))
       mydb.commit()

       await message.answer('Данные успешно удалены!')

    else:
       await message.answer('Введенный заказ не найден в базе данных!')
    await state.finish()
##################

class ChangePriceState(StatesGroup):
    waiting_order_id = State()
    waiting_new_price = State()


@dp.message_handler(text=["📝 Изменение стоимости заказа"])
async def change_price(message: types.Message):
   await message.answer('Введите номер заказа, чтобы изменить его стоимость:')
   await ChangePriceState.waiting_order_id.set()

@dp.message_handler(state=ChangePriceState.waiting_order_id)
async def process_order_id(message: types.Message, state: FSMContext):
   order_id = message.text
   # Проверяем, есть ли введенный order_id в базе данных
   mydb = database_connect
   mycursor = mydb.cursor()
   mycursor.execute("SELECT * FROM `orders` WHERE order_id = %s;", (order_id,))
   result = mycursor.fetchone()

   if result:
      # Если заказ существует, спрашиваем новую стоимость
      await message.answer('Введите новую стоимость заказа:')
      await state.update_data(order_id=order_id)
      await ChangePriceState.waiting_new_price.set()
   else:
      await message.answer('Введенный заказ не найден в базе данных!')
      await state.finish()

@dp.message_handler(state=ChangePriceState.waiting_new_price)
async def process_new_price(message: types.Message, state: FSMContext):
    try:
        new_price = float(message.text)
    except ValueError:
        await message.answer('Неверный формат цены!')
        await state.finish()
        return

    data = await state.get_data()
    order_id = data.get('order_id')

    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("UPDATE `orders` SET product_price = %s WHERE order_id = %s;", (new_price, order_id))
    mydb.commit()
    await message.answer(f'✅ Стоимость заказа {order_id} изменена на {new_price} успешно!')
    await state.finish()


##################
@dp.message_handler(text="📝 Просмотр заказов")
async def stats(message: types.Message, state: FSMContext):
    # Получение данных из базы данных
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM `orders`")
    orders = mycursor.fetchall()
    if len(orders) > 0:
        response = "📝 Все заказы в работе:\n\n"
        for order in orders:
            response += f"🟢 Номер заказа: {order[0]}\nТовар: {order[1]}\nЦена: {order[2]} рублей\nКоличество: {order[3]} шт \nСтатус заказа: {order[4]} \n" \
                        f"Статус оплаты: {order[5]}\nTelegramID: {order[6]} \nИмя клиента: {order[7]}\n\n"
        await message.reply(response)
    else:
        await message.reply('Заказов пока нет!')
    await state.finish()


class SearchState(StatesGroup):
    waiting_for_product_status_number = State()

class ChangeState(StatesGroup):
    waiting_for_order_id = State()
    waiting_for_product_status = State()

@dp.message_handler(text=["📝 Изменение информации о статусе заказа"])
async def stats(message: types.Message):
    await message.answer('Введите номер заказа, чтобы изменить статус продукта:')
    await ChangeState.waiting_for_order_id.set()

@dp.message_handler(state=ChangeState.waiting_for_order_id)
async def process_order_id(message: types.Message, state: FSMContext):
    order_id = message.text

    # Проверяем, есть ли введенный order_id в базе данных
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM `orders` WHERE order_id = %s;", (order_id,))
    result = mycursor.fetchall()

    if len(result) > 0:
        # Сохраняем order_id в контексте для использования в следующем обработчике
        await state.update_data(order_id=order_id)
        await message.answer('Введите новый статус продукта:')
        await ChangeState.waiting_for_product_status.set()
    else:
        await message.answer('Введенный заказ не найден в базе данных')


@dp.message_handler(state=ChangeState.waiting_for_product_status)
async def process_product_status(message: types.Message, state: FSMContext):
    product_status = message.text

    # Получаем order_id из контекста
    data = await state.get_data()
    order_id = data.get('order_id')

    # Обновляем данные о статусе продукта в базе данных
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("UPDATE `orders` SET product_status = %s WHERE order_id = %s;", (product_status, order_id))
    mydb.commit()

    await message.answer('Статус продукта успешно обновлен!')
    await state.finish()



@dp.message_handler(text=["📊 Статистика"])
async def stats(message: types.Message):
    # Получение количества пользователей из базы данных
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("SELECT COUNT(*) FROM customers")
    count = mycursor.fetchone()[0]
    mydb.commit()
    await message.reply(f'👤 Количество пользователей пользующихся ботом: {count}')

    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("SELECT user_id, first_name, last_name, phone FROM `customers`")
    result = mycursor.fetchall()
    mydb.commit()
    if len(result) > 0:
        products_list = '\n\n'.join(
            [
                f'Telegram ID пользователя: {name[0]} \nИмя: {name[1]} \nФамилия: {name[2]} \nТелефон: {name[3]}'
                for name in
                result])
        await message.answer(f'👤 Пользователи использующие бота:\n\n{products_list}')
    else:
        await message.answer('Ошибка данных!')

@dp.message_handler(text=["📦 Склад"])
async def stats(message: types.Message):
    # Получение количества пользователей из базы данных
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("SELECT Name, Manufacturer, Quantity, Type, Price FROM `product`")
    result = mycursor.fetchall()
    mydb.commit()
    if len(result) > 0:
        products_list = '\n\n'.join(
            [f'{name[0]} \nПроизводитель: {name[1]} \nКоличество: {name[2]}шт. \nТип товара: {name[3]} \nЦена: {name[4]} рублей' for name in
             result])
        await message.reply(f'Товары которые есть на складе:\n\n{products_list}')
    else:
        await message.reply('Ошибка данных!')

class YourState(StatesGroup):
    waiting_for_message = State()

# Обработчик кнопки "Рассылка"
@dp.message_handler(text=['✉ Рассылка'])
async def send_message(message: types.Message):
    await message.answer('Введите сообщение для рассылки:')
    await YourState.waiting_for_message.set()

# Обработчик рассылки сообщений
@dp.message_handler(state=YourState.waiting_for_message, content_types=types.ContentTypes.TEXT)
async def process_send_message(message: types.Message, state: FSMContext):
    # Сохраняем текст для рассылки
    text = message.text
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("SELECT user_id FROM customers")
    newslatter = [row[0] for row in mycursor.fetchall()]
    mydb.commit()

    for user_id in newslatter:
        try:
            await bot.send_message(user_id, text)
        except exceptions.ChatNotFound:
            print(f"Чат с данным пользователем не найден: {user_id}")

    await state.finish()
    await message.answer("Рассылка успешно выполнена!")

class SearchType(StatesGroup):
    waiting_for_product_type = State()
class SearchTypeInline(StatesGroup):
    waiting_for_product_type = State()
    waiting_for_next_product1 = State()

# Обработчик кнопки "Поиск по каталогу"
@dp.message_handler(text=['🔍 Поиск по каталогу'])
async def search(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🔹 Антифриз'))
    markup.add(types.KeyboardButton('🔹 Масло моторное'))
    markup.add(types.KeyboardButton('🔹 Свечи'))
    markup.add(types.KeyboardButton('🔹 Тормозная жидкость'))
    markup.add(types.KeyboardButton('◀ Назад'))
    await message.answer('🔍 Нажмите на интересующий вас товар:\n\n'
                         '(<i>Например: Свечи, Масло моторное, Антифриз и т.д.</i>)'
                         '\n\n❗ Каталог постоянно обновляется! \nЕсли вы не нашли интересующий вас товар, свяжитель с консультантом при помощи кнопки '
                         '"👤 Онлайн-консультант"', parse_mode='html', reply_markup=markup)

    await SearchType.waiting_for_product_type.set()

@dp.message_handler(state=SearchType.waiting_for_product_type, content_types=types.ContentTypes.TEXT)
async def process_send_message(message: types.Message, state: FSMContext):
    mydb = database_connect
    mycursor = mydb.cursor()
    if message.text == '◀ Назад':
        await state.finish()
        await start(message)

    # Антифриз
    elif message.text == '🔹 Антифриз':
        mycursor.execute("SELECT Name, Manufacturer, Quantity, Price, Url FROM product WHERE Type = 'Антифриз' LIMIT 1;")
        result = mycursor.fetchone()
        if result is not None:
            # Добавление кнопки "Следующий товар"
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton('➡', callback_data='next_product1')
            )
            await message.answer_photo('https://f.nodacdn.net/351551')
            await message.answer(
                'Нажмите кнопку для просмотра товаров категории "Антифриз".',
                reply_markup=markup)

            await SearchTypeInline.waiting_for_next_product1.set()
        else:
            await message.reply('Товаров категории "Антифриз" нет!')
    elif message.text == '◀ Назад':
        await state.finish()
        await start(message)

    # Масло моторное
    elif message.text == '🔹 Масло моторное':
        mycursor.execute(
            "SELECT Name, Manufacturer, Quantity, Price, Url FROM product WHERE Type = 'Масло моторное' LIMIT 1;")
        result = mycursor.fetchone()
        if result is not None:
            # Добавление кнопки "Следующий товар"
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton('➡', callback_data='next_product2')
            )
            await message.answer_photo('https://bmw-apan.ro/wp-content/uploads/sites/15/2019/06/bmw-service-avantaje-ulei-bmw-original.jpg')
            await message.answer(
                'Нажмите кнопку для просмотра товаров категории "Масло моторное".',
                reply_markup=markup)

            await SearchTypeInline.waiting_for_next_product1.set()
        else:
            await message.reply('Товаров категории "Масло моторное" нет!')
    elif message.text == '◀ Назад':
        await state.finish()
        await start(message)

    # Тормозная жидкость
    elif message.text == '🔹 Тормозная жидкость':
        mycursor.execute(
            "SELECT Name, Manufacturer, Quantity, Price, Url FROM product WHERE Type = 'Тормозная жидкость' LIMIT 1;")
        result = mycursor.fetchone()
        if result is not None:
            # Добавление кнопки "Следующий товар"
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton('➡', callback_data='next_product3')
            )
            await message.answer_photo('https://cs14.pikabu.ru/post_img/2022/09/08/7/og_og_1662637522212180444.jpg')
            await message.answer(
                'Нажмите кнопку для просмотра товаров категории "Тормозная жидкость".',
                reply_markup=markup)

            await SearchTypeInline.waiting_for_next_product1.set()
        else:
            await message.reply('Товаров категории "Тормозная жидкость" нет!')
    elif message.text == '◀ Назад':
        await state.finish()
        await start(message)

    # Свечи
    elif message.text == '🔹 Свечи':
        mycursor.execute("SELECT Name, Manufacturer, Quantity, Price FROM `product` WHERE Type = 'Свечи';")
        result = mycursor.fetchall()
        if len(result) > 0:
            products_list = '\n\n'.join(
                [f'{name[0]} \nПроизводитель: {name[1]} \nКоличество: {name[2]} шт. \nЦена: {name[3]} рублей' for name in
                 result])
            await message.reply(f'📦 Товары с типом "Свечи":\n\n{products_list}')
        else:
            await message.reply('Товаров с типом "Свечи" нет!')
    elif message.text == '◀ Назад':
        await state.finish()
        await start(message)
    else:
        await message.reply('Данного товара нет в базе!\n\n'
                            'Не нашли интересующий товар? Не беда!\n\n'
                            'Свяжитесь с консультантом при помощи кнопки: 👤 Онлайн-консультант.')


# Антифриз Inline
@dp.callback_query_handler(lambda c: c.data == 'next_product1', state=SearchTypeInline.waiting_for_next_product1)
async def process_next_product_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_index = data.get('product_index', 0)
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute(
        "SELECT Name, Manufacturer, Quantity, Price, Url FROM product WHERE Type = 'Антифриз' LIMIT 1 OFFSET %s;",
        (product_index,))
    result = mycursor.fetchone()

    if result is not None:
        products_list = f'{result[0]} \nПроизводитель: {result[1]} \nКоличество: {result[2]} шт. \nЦена: {result[3]} руб. \n<a href="{result[4]}">Страница товара</a>'

        await callback_query.message.edit_text(f'📦 Товары категории "Антифриз":\n\n{products_list}', parse_mode=types.ParseMode.HTML)

        # Обновите индекс товара в состоянии
        await state.update_data(product_index=product_index + 1)
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton('➡', callback_data='next_product1'),

        )
        await callback_query.message.edit_reply_markup(reply_markup=markup)
    else:
        await state.finish()
        await callback_query.message.edit_text('Товары категории "Антифриз" закончились!')

# Масло моторное Inline
@dp.callback_query_handler(lambda c: c.data == 'next_product2', state=SearchTypeInline.waiting_for_next_product1)
async def process_next_product_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_index = data.get('product_index', 0)
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute(
        "SELECT Name, Manufacturer, Quantity, Price, Url FROM product WHERE Type = 'Масло моторное' LIMIT 1 OFFSET %s;",
        (product_index,))
    result = mycursor.fetchone()

    if result is not None:
        products_list = f'{result[0]} \nПроизводитель: {result[1]} \nКоличество: {result[2]} шт. \nЦена: {result[3]} руб. \n<a href="{result[4]}">Страница товара</a>'

        await callback_query.message.edit_text(f'📦 Товары категории "Масло моторное":\n\n{products_list}', parse_mode=types.ParseMode.HTML)

        # Обновите индекс товара в состоянии
        await state.update_data(product_index=product_index + 1)
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton('➡', callback_data='next_product2'),

        )
        await callback_query.message.edit_reply_markup(reply_markup=markup)
    else:
        await state.finish()
        await callback_query.message.edit_text('Товары категории "Масло моторное" закончились!')

# Тормозная жидкость Inline
@dp.callback_query_handler(lambda c: c.data == 'next_product3', state=SearchTypeInline.waiting_for_next_product1)
async def process_next_product_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_index = data.get('product_index', 0)
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute(
        "SELECT Name, Manufacturer, Quantity, Price, Url FROM product WHERE Type = 'Тормозная жидкость' LIMIT 1 OFFSET %s;",
        (product_index,))
    result = mycursor.fetchone()

    if result is not None:
        products_list = f'{result[0]} \nПроизводитель: {result[1]} \nКоличество: {result[2]} шт. \nЦена: {result[3]} руб. \n<a href="{result[4]}">Страница товара</a>'

        await callback_query.message.edit_text(f'📦 Товары категории "Тормозная жидкость":\n\n{products_list}', parse_mode=types.ParseMode.HTML)

        # Обновите индекс товара в состоянии
        await state.update_data(product_index=product_index + 1)
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton('➡', callback_data='next_product3'),

        )
        await callback_query.message.edit_reply_markup(reply_markup=markup)
    else:
        await state.finish()
        await callback_query.message.edit_text('Товары категории "Тормозная жидкость" закончились!')



class CalculateState(StatesGroup):
    calculate_finish_price = State()

@dp.message_handler(text=['🧮 Калькулятор стоимости'])
async def search(message: types.Message):
    if message.text == '◀ Назад':
        await state.finish()
        await start(message)
    else:
        await message.answer('📝 Введите название товара и его количество(через запятую), чтобы получить точную стоимость заказа.'
                         '\n\n(<i>Например: ASIA Р-ОАТ purple -36 1L, 8</i>)', parse_mode='html')
        await CalculateState.calculate_finish_price.set()





@dp.message_handler(state=CalculateState.calculate_finish_price, content_types=types.ContentTypes.TEXT)
async def process_send_message(message: types.Message, state: FSMContext):
    # Получаем введенные пользователем название товара и его количество
    product_info = message.text.split(',')
    product_name = product_info[0].strip()
    product_quantity = int(product_info[1].strip())
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute(
        f"SELECT Name, Price, Quantity, (Price * {product_quantity}) AS total FROM product WHERE Name = '{product_name}'")
    result = mycursor.fetchall()

    if len(result) > 0:
        products_list = '\n\n'.join(
            [f'{name[0]}  \nЦена: {name[1]} рублей. \nКоличество: {product_quantity} шт. \nИтог: {name[3]} рублей.' for name in
             result])
        await message.reply(f'Итоговая цена: \n\n{products_list}')
    elif message.text == '◀ Назад':
        await state.finish()
        await start(message)
    else:
        await message.reply(f'Итоговая цена не рассчитывается!')

    await state.finish()


class SearchState(StatesGroup):
    waiting_for_product_status_number = State()
#Информация о статусе заказа
@dp.message_handler(text=['ℹ Информация о статусе заказа'])
async def get_data_from_db(message: types.Message):
    await message.answer('📝 Введите номер заказа чтобы получить информацию о статусе заказа:')
    await SearchState.waiting_for_product_status_number.set()

@dp.message_handler(state=SearchState.waiting_for_product_status_number, content_types=types.ContentTypes.TEXT)
async def process_send_message(message: types.Message, state: FSMContext):
    search_number = message.text
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("SELECT product_name, product_price, product_quantity, product_status FROM `orders` WHERE order_id = %s;", (search_number,))
    result = mycursor.fetchall()
    if len(result) > 0:
        products_list = '\n\n'.join(
            [f'{name[0]}  \nЦена: {name[1]} рублей. \nКоличество: {name[2]} шт. \nСтатус: {name[3]}'  for name in
             result])
        await message.reply(f'📦 Ваш статус заказа под номером {search_number}:\n\n{products_list}')
    elif message.text == '◀ Назад':
        await state.finish()
        await start(message)
    else:
        await message.reply(f'📦 Заказов с данным номером "{search_number}" нет!')

    await state.finish()


async def check_order_status(bot):
    last_order_id = None

    while True:
        mydb = database_connect
        mycursor = mydb.cursor()

        mycursor.execute("SELECT * FROM orders WHERE order_id > %s ORDER BY order_id ASC", (last_order_id or 0,))
        result = mycursor.fetchall()
        mydb.commit()

        for order in result:
            order_id = order[1]
            product_status = order[2]
            telegram_id = order[3]

            if product_status == "В обработке":
                await bot.send_message(chat_id=telegram_id,
                                       text=f"Изменился статус вашего заказа. Номер заказа: {order_id}")

            last_order_id = order_id

        mycursor.close()

        await asyncio.sleep(5)


# Обработчик оплаты заказов
@dp.message_handler(commands=['payment'])
async def payment_command(message: types.Message):
    await message.answer('📝 Введите номер заказа для оплаты:')

@dp.message_handler(regexp=r'^\d+$')
async def process_payment(message: types.Message):
    order_id = message.text
    mydb = database_connect
    cursor = mydb.cursor()
    # Выполняем запрос к базе данных для получения суммы заказа
    cursor.execute('SELECT product_price, product_name, product_quantity FROM orders WHERE order_id = %s', (order_id,))
    result = cursor.fetchone()
    mydb.commit()
    if result is None:
        await message.answer('❌ Заказ не найден!')
    else:
        product_price = result[0]
        product_name = result[1]
        product_quantity = result[2]
        await message.answer('❗ Внимательно проверьте номер и итоговую цену вашего заказа!\n\n'
                             f'Наименование товара: <strong>{product_name}</strong>\n'
                             f'Количество товара, шт.: <strong>{product_quantity}</strong>\n\n'
                             'Если вы с чем-то не согласны или заметили ошибку, свяжитесь с консультантом при помощи кнопки "👤 Онлайн-консультант"',
                             parse_mode='html')
        if product_price > 0:
            await bot.send_invoice(
                chat_id=message.chat.id,
                title='Оплата заказа',
                description=f'Оплата заказа №{order_id}',
                payload='order_payload',
                provider_token=config.PAYMENT_TOKEN,
                start_parameter='optional',
                currency='RUB',
                prices=[
                    types.LabeledPrice(label='Сумма заказа', amount=product_price)
                    # Используем сумму заказа из базы данных
                ]
            )
        else:
            await message.answer('Сумма заказа не может быть отрицательной или равной нулю!')

@dp.pre_checkout_query_handler()
async def pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(
        pre_checkout_query_id=pre_checkout_query.id,
        ok=True
    )

@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    order_id = message.successful_payment.invoice_payload
    mydb = database_connect
    cursor = mydb.cursor()
    # Обновляем колонку payment_status в таблице orders
    cursor.execute('UPDATE orders SET payment_status = "Заказ оплачен" WHERE order_id = %s', (order_id,))
    mydb.commit()
    await message.answer('✅ Оплата прошла успешно!\n\nСпасибо за покупку в нашем магазине ❤')
dp.register_message_handler(payment_command, commands=['payment'])
dp.register_message_handler(process_payment)
dp.register_message_handler(successful_payment)

# Уведомления о поступлении новых заказов





# Обработчик ошибок
@dp.message_handler(content_types=["audio", "document", "photo", "sticker", "video", "video_note", "voice", "location",
                "new_chat_members", "left_chat_member", "new_chat_title", "new_chat_photo", "delete_chat_photo",
               "group_chat_created", "supergroup_chat_created", "channel_chat_created", "migrate_to_chat_id",
                "migrate_from_chat_id", "pinned_message"])
async def error(message: types.Message):
   await message.answer("❌ Неизвестная команда!\n"
                      "Для взаимодействия с ботом используйте кнопки внизу экрана ⬇")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    executor.start_polling(dp, loop=loop, skip_updates=True)

