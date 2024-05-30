import asyncio
from asyncio import exceptions
from aiogram import exceptions
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import state
from aiogram.types.web_app_info import WebAppInfo
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TOKEN, chat_id_to_forward, admins_id
from database import database_connect
import mysql.connector
import telebot
from aiogram.dispatcher.filters.state import State, StatesGroup
import mysql.connector

bot = telebot.TeleBot("6286125677:AAG_FPor6xFejfPNDqrz-H9PuKvYZTxJza4")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Обработчик команды "/start"
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    # Подключение базы данных
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("CREATE TABLE IF NOT EXISTS customers ("
                     "user_id INTEGER, "
                     "first_name VARCHAR(255), "
                     "last_name VARCHAR(255), "
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
    main.add(types.KeyboardButton('💻 Открыть веб-приложение', web_app=WebAppInfo(url='https://carych.ru/')))
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
    markup.add(types.KeyboardButton('📝 Оформить заказ по VIN или  гос.номеру'))
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



class Order2(StatesGroup):
    entering_Number2 = State()
    entering_Name2 = State()
    entering_Phone2 = State()

@dp.message_handler(text=['📝 Оформить заказ по VIN или  гос.номеру'])
async def Number(message: types.Message):
    await message.answer('1️⃣ Введите гос.номер или VIN номер вашего автомобиля:')
    await Order2.entering_Number2.set()
    if message.text == '◀ Назад':
        await state.finish()
        await start(message)


@dp.message_handler(state=Order2.entering_Number2)
async def Number2(message: types.Message, state: FSMContext):
    # Сохраняем название товара
    await state.update_data(product_number=message.text)
    # Переводим пользователя в состояние ввода количества товара
    await message.answer('2️⃣ Введите название/тип запчасти:')
    await Order2.entering_Name2.set()
    if message.text == '◀ Назад':
        await state.finish()
        await start(message)

@dp.message_handler(state=Order2.entering_Name2)
async def Name(message: types.Message, state: FSMContext):
    # Сохраняем количество товара
    await state.update_data(product_name=message.text)

    # Спрашиваем номер телефона у пользователя
    await message.answer('3️⃣ Введите ваш номер телефона для связи:')
    await Order2.entering_Phone2.set()

@dp.message_handler(state=Order2.entering_Phone2)
async def enter_phone_number(message: types.Message, state: FSMContext):
    # Сохраняем номер телефона
    await state.update_data(phone=message.text)

    # Получаем все данные из состояния
    data = await state.get_data()
    product_number = data.get('product_number')
    product_name = data.get('product_name')
    phone = data.get('phone')
    customer_name = message.from_user.first_name

    # Подключаемся к базе данных
    mydb = database_connect
    mycursor = mydb.cursor()

    # Выполняем запрос с использованием параметров для корректной подстановки значений
    sql = "INSERT INTO orders2 (Number, Name, Phone, CustomerName) VALUES (%s, %s, %s, %s)"
    values = (product_number, product_name, phone, customer_name)
    mycursor.execute(sql, values)

    # Фиксируем изменения в базе данных
    mydb.commit()

    mycursor.fetchall()  # Fetch all results from the INSERT query

    mycursor.execute("SELECT ID, Name FROM orders2 ORDER BY ID DESC LIMIT 1")
    result = mycursor.fetchone()
    product_name = result[1]



    await message.answer(f'✅ Заказ успешно добавлен!'
                         f'\n\n🚗 {message.from_user.full_name}, спасибо что оставили заявку на покупку "{product_name}" для своего автомобиля.'
                         f'\n\n⌛ Ожидайте, скоро с вами свяжется менеджер компании для уточнения деталей.')

    await bot.send_message(chat_id=chat_id_to_forward, text="❗ Поступил новый заказ по гос.номеру или VIN номеру автомобиля❗"
                                                            "\n\nПроверьте вкладку '📝 Заказы оформленные по VIN или гос.номеру' через админ панель /admin")

    # Очищаем данные из состояния
    await state.reset_state()







# Сделать заказ
class OrderForm(StatesGroup):
    entering_product_name = State()
    entering_product_quantity = State()
    entering_phone_number = State()

@dp.message_handler(text=['📝 Сделать заказ'])
async def phone_number(message: types.Message):
    await message.answer('1️⃣ Введите название товара чтобы добавить его в заказ:')
    await OrderForm.entering_product_name.set()
    if message.text == '◀ Назад':
        await state.finish()
        await start(message)

@dp.message_handler(state=OrderForm.entering_product_name)
async def enter_product_name(message: types.Message, state: FSMContext):
    # Сохраняем название товара
    await state.update_data(product_name=message.text)

    # Переводим пользователя в состояние ввода количества товара
    await message.answer('2️⃣ Введите количество товара:')
    await OrderForm.entering_product_quantity.set()

    if message.text == '◀ Назад':
        await state.finish()
        await start(message)

@dp.message_handler(state=OrderForm.entering_product_quantity)
async def enter_product_quantity(message: types.Message, state: FSMContext):
    # Сохраняем количество товара
    await state.update_data(product_quantity=message.text)

    # Спрашиваем номер телефона у пользователя
    await message.answer('3️⃣ Введите ваш номер телефона для связи:')
    await OrderForm.entering_phone_number.set()  # Change this line

@dp.message_handler(state=OrderForm.entering_phone_number)
async def enter_phone_number(message: types.Message, state: FSMContext):
    # Сохраняем номер телефона
    await state.update_data(phone_number=message.text)

    # Получаем все данные из состояния
    data = await state.get_data()
    product_name = data.get('product_name')
    product_quantity = data.get('product_quantity')
    phone_number = data.get('phone_number')
    telegram_id = message.from_user.id
    customer_name = message.from_user.first_name

    # Подключаемся к базе данных
    mydb = database_connect
    mycursor = mydb.cursor()

    # Выполняем запрос с использованием параметров для корректной подстановки значений
    sql = "INSERT INTO orders (product_name, product_quantity, phone, product_status, payment_status, TelegramID, CustomerName) VALUES (%s, %s, %s, 'В обработке', 'Ожидается оплата', %s, %s)"
    values = (product_name, product_quantity, phone_number, telegram_id, customer_name)
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
    # Проверяем, является ли отправитель администратором
    if message.from_user.id == admins_id:
        # Создаем InlineKeyboardMarkup с кнопками действий
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(types.KeyboardButton("📊 Статистика"))
        markup.add(types.KeyboardButton("✉ Рассылка"))
        markup.add(types.KeyboardButton("📝 Заказы"))
        markup.add(types.KeyboardButton("📦 Товары на складе"))
        markup.add(types.KeyboardButton("◀ Выход"))
        await message.reply("✅ Вы вошли в админ панель!", reply_markup=markup)
    else:
        await message.reply("🚫 У вас нет прав для входа в админ панель!")


@dp.message_handler(text=['📝 Заказы'])
async def inline(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📝 Просмотр заказов"))
    markup.add(types.KeyboardButton("📝 Заказы оформленные по VIN или гос.номеру"))
    markup.add(
        types.KeyboardButton('📝 Поиск по VIN или гос.номеру', web_app=WebAppInfo(url='https://avtocod.ru/')))
    markup.add(types.KeyboardButton("📝 Изменение информации о статусе заказа"))
    markup.add(types.KeyboardButton("📝 Изменение информации о статусе оплаты"))
    markup.add(types.KeyboardButton("📝 Изменение стоимости заказа"))
    markup.add(types.KeyboardButton("📝 Удаление заказа"))
    markup.add(types.KeyboardButton("◀ Назад в админ панель"))

    await message.answer('Выберите нужное действие ⬇:', reply_markup=markup)

@dp.message_handler(text=['◀ Назад в админ панель'])
async def back(message: types.Message):
    await admin_panel(message)


@dp.message_handler(text=['📦 Товары на складе'])
async def inline2(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📦 Склад"))
    markup.add(types.KeyboardButton("✒ Добавить новый товар на склад"))
    markup.add(types.KeyboardButton("✒ Изменить цену товара"))
    markup.add(types.KeyboardButton("✒ Изменить количество товара"))
    markup.add(types.KeyboardButton("❌ Удалить товар со склада"))
    markup.add(types.KeyboardButton("◀ Назад в админ панель"))

    await message.answer('Выберите нужное действие ⬇:', reply_markup=markup)


class ChangeQuantity(StatesGroup):
    change_quantity_id = State()
    change_quantity = State()

@dp.message_handler(text=['✒ Изменить количество товара'])
async def add_new_product(message: types.Message):
    await message.answer('Введите ID товара, которому хотите поменять количество:')
    await ChangeQuantity.change_quantity_id.set()

@dp.message_handler(state=ChangeQuantity.change_quantity_id)
async def process_order_id(message: types.Message, state: FSMContext):
   ID = message.text
   # Проверяем, есть ли введенный order_id в базе данных
   mydb = database_connect
   mycursor = mydb.cursor()
   mycursor.execute("SELECT * FROM `product` WHERE ID = %s;", (ID,))
   result = mycursor.fetchone()

   if result:
      # Если заказ существует, спрашиваем новую стоимость
      await message.answer('Введите новое количество товара:')
      await state.update_data(ID=ID)  # Update the state data with the correct key
      await ChangeQuantity.change_quantity.set()
   else:
      await message.answer('Введенный заказ не найден в базе данных!')
      await state.finish()

@dp.message_handler(state=ChangeQuantity.change_quantity)
async def process_new_price(message: types.Message, state: FSMContext):
    try:
        quantity = int(message.text)
    except ValueError:
        await message.answer('Неверный формат!')
        await state.finish()
        return

    data = await state.get_data()
    ID = data.get('ID')  # Retrieve the ID using the correct key

    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("UPDATE `product` SET Quantity = %s WHERE ID = %s;", (quantity, ID))
    mydb.commit()

    # Check if any row was affected by the update statement
    if mycursor.rowcount > 0:
        await message.answer(f'✅ Количество товара под номером {ID} изменено на {quantity} успешно!')
    else:
        await message.answer(f'❌ Количество товара под номером {ID} не изменено, т.к. запись не найдена или имеет другой формат!')

    await state.finish()


class ChangeProductPrice(StatesGroup):
    change_price_id = State()
    change_price_price = State()

@dp.message_handler(text=['✒ Изменить цену товара'])
async def add_new_product(message: types.Message):
    await message.answer('Введите ID товара, которому хотите поменять цену:')
    await ChangeProductPrice.change_price_id.set()

@dp.message_handler(state=ChangeProductPrice.change_price_id)
async def process_order_id(message: types.Message, state: FSMContext):
   ID = message.text
   # Проверяем, есть ли введенный order_id в базе данных
   mydb = database_connect
   mycursor = mydb.cursor()
   mycursor.execute("SELECT * FROM `product` WHERE ID = %s;", (ID,))
   result = mycursor.fetchone()

   if result:
      # Если заказ существует, спрашиваем новую стоимость
      await message.answer('Введите новую стоимость товара:')
      await state.update_data(ID=ID)  # Update the state data with the correct key
      await ChangeProductPrice.change_price_price.set()
   else:
      await message.answer('Введенный заказ не найден в базе данных!')
      await state.finish()

@dp.message_handler(state=ChangeProductPrice.change_price_price)
async def process_new_price(message: types.Message, state: FSMContext):
    try:
        new_price = float(message.text)
    except ValueError:
        await message.answer('Неверный формат цены!')
        await state.finish()
        return

    data = await state.get_data()
    ID = data.get('ID')  # Retrieve the ID using the correct key

    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("UPDATE `product` SET Price = %s WHERE ID = %s;", (new_price, ID))
    mydb.commit()

    # Check if any row was affected by the update statement
    if mycursor.rowcount > 0:
        await message.answer(f'✅ Стоимость товара под номером {ID} изменена на {new_price} успешно!')
    else:
        await message.answer(f'❌ Стоимость товара под номером {ID} не изменена, т.к. запись не найдена или имеет другой формат!')

    await state.finish()

############
class AddProductForm(StatesGroup):
    entering_product_name = State()
    entering_manufacturer = State()
    entering_product_type = State()
    entering_product_quantity = State()
    entering_product_price = State()
    entering_product_url = State()

@dp.message_handler(text=['✒ Добавить новый товар на склад'])
async def add_new_product(message: types.Message):
    await message.answer('1️⃣ Введите название товара:')
    await AddProductForm.entering_product_name.set()


@dp.message_handler(state=AddProductForm.entering_product_name)
async def enter_product_name(message: types.Message, state: FSMContext):
    # Сохраняем название товара
    await state.update_data(product_name=message.text)

    # Переводим пользователя в состояние ввода производителя
    await message.answer('2️⃣ Введите название производителя:')
    await AddProductForm.entering_manufacturer.set()

@dp.message_handler(state=AddProductForm.entering_manufacturer)
async def enter_manufacturer(message: types.Message, state: FSMContext):
    # Сохраняем название производителя
    await state.update_data(manufacturer=message.text)

    # Переводим пользователя в состояние ввода типа товара
    await message.answer('3️⃣ Введите тип товара:')
    await AddProductForm.entering_product_type.set()

@dp.message_handler(state=AddProductForm.entering_product_type)
async def enter_product_type(message: types.Message, state: FSMContext):
    # Сохраняем тип товара
    await state.update_data(product_type=message.text)

    # Переводим пользователя в состояние ввода количества товара
    await message.answer('4️⃣ Введите количество товара на складе:')
    await AddProductForm.entering_product_quantity.set()

@dp.message_handler(state=AddProductForm.entering_product_quantity)
async def enter_product_quantity(message: types.Message, state: FSMContext):
    # Сохраняем количество товара на складе
    await state.update_data(product_quantity=message.text)

    # Переводим пользователя в состояние ввода цены товара
    await message.answer('5️⃣ Введите цену товара за штуку:')
    await AddProductForm.entering_product_price.set()

@dp.message_handler(state=AddProductForm.entering_product_price)
async def enter_product_price(message: types.Message, state: FSMContext):
    # Сохраняем цену товара за штуку
    await state.update_data(product_price=message.text)

    # Спрашиваем ссылку на товар у пользователя
    await message.answer('6️⃣ Введите ссылку на товар (опционально):')
    await AddProductForm.entering_product_url.set()

@dp.message_handler(state=AddProductForm.entering_product_url)
async def enter_product_url(message: types.Message, state: FSMContext):
    await state.update_data(product_url=message.text)
    data = await state.get_data()
    product_name = data.get('product_name')
    manufacturer = data.get('manufacturer')
    product_type = data.get('product_type')
    product_quantity = data.get('product_quantity')
    product_price = data.get('product_price')
    product_url = data.get('product_url')


    try:
        product_id = await add_product_to_db(product_name, manufacturer, product_type, product_quantity, product_price, product_url)
        await message.answer(f'✅ Новый товар успешно добавлен на склад!')
    except mysql.connector.Error as e:
        await message.answer(f'❌ Ошибка добавления товара: {e}')
    finally:
        await state.reset_state()

async def add_product_to_db(product_name, manufacturer, product_type, product_quantity, product_price, product_url):
    mydb = database_connect
    mycursor = mydb.cursor()
    sql = "INSERT INTO product (Name, Manufacturer, Type, Quantity, Price, Url) VALUES (%s, %s, %s, %s, %s, %s)"
    values = (product_name, manufacturer, product_type, product_quantity, product_price, product_url)
    mycursor.execute(sql, values)
    mydb.commit()
    mycursor.execute("SELECT ID FROM product ORDER BY ID DESC LIMIT 1")
    result = mycursor.fetchone()
    product_id = result[0]






@dp.message_handler(text=['◀ Назад в админ панель'])
async def back(message: types.Message):
    await admin_panel(message)



class DeleteProductStorage(StatesGroup):
    delproduct = State()

@dp.message_handler(text=["❌ Удалить товар со склада"])
async def stats(message: types.Message):
    await message.answer('Введите номер товара со склада, чтобы удалить его:')
    await DeleteProductStorage.delproduct.set()

@dp.message_handler(state=DeleteProductStorage.delproduct)
async def process_order_id(message: types.Message, state: FSMContext):
    ID = message.text
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM `product` WHERE ID = %s;", (ID,))
    result = mycursor.fetchall()

    if len(result) > 0:
       # Удаляем все данные с данным order_id из базы данных
       mycursor.execute("DELETE FROM `product` WHERE ID = %s;", (ID,))
       mydb.commit()

       await message.answer(f'✅ Товар под номером {ID} успешно удален!')

    else:
       await message.answer('Введенный заказ не найден в базе данных!')
    await state.finish()



class DeleteState(StatesGroup):
    waiting_order_id = State()

@dp.message_handler(text=["📝 Удаление заказа"])
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
            response += f"\n\n🟢 Номер заказа: {order[0]}\nТовар: {order[1]}\nЦена: {order[2]} рублей\nКоличество: {order[3]} шт \nСтатус заказа: {order[4]} \n" \
                        f"Статус оплаты: {order[5]}\nИмя клиента: {order[7]}\nНомер телефона: <code>{order[8]}</code>"
        await message.reply(response, parse_mode='html')
    else:
        await message.reply('Заказов пока нет!')
    await state.finish()



@dp.message_handler(text="📝 Заказы оформленные по VIN или гос.номеру")
async def stats(message: types.Message, state: FSMContext):
    # Получение данных из базы данных
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM `orders2`")
    orders = mycursor.fetchall()
    if len(orders) > 0:
        response = "📝 Все заказы в работе:\n\n"
        for order in orders:
            response += (f"\n\n🟢 Номер заказа: {order[0]}\nVIN или гос.номер: <code>{order[1]}</code>\nНазвание/тип запчасти: {order[2]}\nНомер телефона: <code>{order[3]}</code>\nИмя клиента: {order[4]}")
        await message.reply(response, parse_mode='html')
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
    await message.answer('Введите номер заказа, чтобы изменить его статус:')
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
        await message.answer('Введенный заказ не найден в базе данных!')


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


#

class ChangeState2(StatesGroup):
    waiting_for_order_id = State()
    waiting_for_payment_status = State()

@dp.message_handler(text=["📝 Изменение информации о статусе оплаты"])
async def stats(message: types.Message):
    await message.answer('Введите номер заказа, чтобы изменить его статус оплаты:')
    await ChangeState2.waiting_for_order_id.set()

@dp.message_handler(state=ChangeState2.waiting_for_order_id)
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
        await message.answer('Введите новый статус оплаты:')
        await ChangeState2.waiting_for_payment_status.set()
    else:
        await message.answer('Введенный заказ не найден в базе данных!')


@dp.message_handler(state=ChangeState2.waiting_for_payment_status)
async def process_payment_status(message: types.Message, state: FSMContext):
    payment_status = message.text

    # Получаем order_id из контекста
    data = await state.get_data()
    order_id = data.get('order_id')

    # Обновляем данные о статусе оплаты в базе данных
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute("UPDATE `orders` SET payment_status = %s WHERE order_id = %s;", (payment_status, order_id))
    mydb.commit()

    await message.answer('Статус оплаты успешно обновлен!')
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
    mycursor.execute("SELECT ID, Name, Manufacturer, Quantity, Type, Price FROM `product`")
    result = mycursor.fetchall()
    mydb.commit()

    low_stock_products = []
    for product in result:
        if product[3] < 10:
            low_stock_products.append(product)

    if len(result) > 0:
        products_list = '\n'.join(
            [f'\n🟢 ID товара: <code>{name[0]}</code> \nНазвание: <code>{name[1]}</code> \nПроизводитель: {name[2]} \nКоличество: {name[3]}шт. \nТип товара: {name[4]} \nЦена: {name[5]} рублей' for name in
             result])
        await message.reply(f'Товары которые есть на складе:\n\n{products_list}', parse_mode='html')

    if low_stock_products:
        low_stock_message = '\n'.join(
            [f'\n⚠️ ID товара: <code>{product[0]}</code> \nНазвание: <code>{product[1]}</code> \nПроизводитель: {product[2]} \n<u>Количество: {product[3]} шт.</u> \nТип товара: {product[4]} \nЦена: {product[5]} рублей' for product in
             low_stock_products])
        await message.reply(f'❗ Товары с низким количеством на складе:\n\n{low_stock_message}', parse_mode='html')
    else:
        await message.reply('Все товары на складе в достаточном количестве.')


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
                         '\n\n❗ Каталог постоянно обновляется! \nЕсли вы не нашли интересующий вас товар, свяжитель с консультантом при помощи кнопки: '
                         '👤 Онлайн-консультант', parse_mode='html', reply_markup=markup)

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
                            'Не нашли интересующий товар?\n\n'
                            'Свяжитесь с консультантом при помощи кнопки: 👤 Онлайн-консультант.')


# Антифриз Inline
@dp.callback_query_handler(lambda c: c.data == 'next_product1', state=SearchTypeInline.waiting_for_next_product1)
async def process_next_product_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    product_index = data.get('product_index', 0)
    mydb = database_connect
    mycursor = mydb.cursor()
    mycursor.execute(
        "SELECT Name, Manufacturer, Quantity,Price, Url FROM product WHERE Type = 'Антифриз' LIMIT 1 OFFSET %s;",
        (product_index,))
    result = mycursor.fetchone()

    if result is not None:
        products_list = f'<code>{result[0]}</code> \nПроизводитель: {result[1]} \nКоличество: {result[2]} шт. \nЦена: {result[3]} руб. \n<a href="{result[4]}">Страница товара</a>'

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
        await callback_query.message.edit_text('😔 Товары категории "Антифриз" закончились!'
                                               '\n\nНе нашли интересующий товар?'
                                               '\n\nСвяжитесь с консультантом при помощи кнопки в главном меню: '
                                               '\n👤 Онлайн-консультант.'
                                               '\n\nДля выхода в главное меню нажмите кнопку: ◀ Назад.')

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
        products_list = f'<code>{result[0]}</code> \nПроизводитель: {result[1]} \nКоличество: {result[2]} шт. \nЦена: {result[3]} руб. \n<a href="{result[4]}">Страница товара</a>'

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
        await callback_query.message.edit_text('😔 Товары категории "Масло моторное" закончились!'
                                               '\n\nНе нашли интересующий товар?'
                                               '\n\nСвяжитесь с консультантом при помощи кнопки в главном меню: '
                                               '\n👤 Онлайн-консультант.'
                                               '\n\nДля выхода в главное меню нажмите кнопку: ◀ Назад.')

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
        products_list = f'<code>{result[0]}</code> \nПроизводитель: {result[1]} \nКоличество: {result[2]} шт. \nЦена: {result[3]} руб. \n<a href="{result[4]}">Страница товара</a>'

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
        await callback_query.message.edit_text('😔 Товары категории "Тормозная жидкость" закончились!'
                                               '\n\nНе нашли интересующий товар?'
                                               '\n\nСвяжитесь с консультантом при помощи кнопки в главном меню: '
                                               '\n👤 Онлайн-консультант.'
                                               '\n\nДля выхода в главное меню нажмите кнопку: ◀ Назад.')


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
            [f'<code>{name[0]}</code>  \nЦена за 1 шт.: {name[1]} рублей. \nКоличество: {product_quantity} шт. \nИтог: <code>{name[3]}</code> рублей.' for name in
             result])
        await message.reply(f'🧮 Итоговая цена: \n\n{products_list}', parse_mode='html')
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
    mycursor.execute("SELECT product_name, product_price, product_quantity, product_status, payment_status FROM `orders` WHERE order_id = %s;", (search_number,))
    result = mycursor.fetchall()
    if len(result) > 0:
        products_list = '\n\n'.join(
            [f'{name[0]}  \nЦена: {name[1]} рублей. \nКоличество: {name[2]} шт. \nСтатус заказа: {name[3]} \nСтатус оплаты: {name[4]}' for name in
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


class QrNumber(StatesGroup):
    waiting_for_qrcode = State()
    waiting_for_number = State()

# Обработчик оплаты заказов
@dp.message_handler(commands=['payment'])
async def payment_command(message: types.Message):
    await message.answer('📝 Введите номер заказа для оплаты:')
    await QrNumber.waiting_for_number.set()

@dp.message_handler(regexp=r'^\d+$', state=QrNumber.waiting_for_number)
async def process_payment(message: types.Message, state: FSMContext):
    order_id = message.text
    mydb = database_connect
    cursor = mydb.cursor()
    # Выполняем запрос к базе данных для получения суммы заказа
    cursor.execute('SELECT order_id, product_price, product_name, product_quantity FROM orders WHERE order_id = %s', (order_id,))
    result = cursor.fetchone()
    mydb.commit()
    if result is None:
        await message.answer('❌ Заказ не найден!')
    else:
        id = result[0]
        product_price = result[1]
        product_name = result[2]
        product_quantity = result[3]
        await message.answer('❗ Внимательно проверьте данные вашего заказа!\n\n'
                             f'1️⃣ Номер товара: <strong>{id}</strong>\n'
                             f'2️⃣ Наименование товара: <strong>{product_name}</strong>\n'
                             f'3️⃣ Количество товара, шт.: <strong>{product_quantity}</strong>\n'
                             f'4️⃣ Итоговая цена, руб.: <strong>{product_price}</strong>\n\n'
                             'Если вы с чем-то не согласны или заметили ошибку, свяжитесь с консультантом при помощи кнопки "👤 Онлайн-консультант"',
                             parse_mode='html')

        if result is not None:

            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton('1️⃣', callback_data='qrcode'),
                types.InlineKeyboardButton('2️⃣', callback_data='number')
            )

        await message.answer('Для оплаты заказа можете использовать любой из двух возможных способов (для выбора нажмите на кнопку с подходящим вариантом):'
                             '\n\n1️⃣ Оплата по QR-коду'
                             '\n\n2️⃣ Перевод по номеру телефона', reply_markup=markup)


class QrNumber(StatesGroup):
    waiting_for_qrcode = State()
    waiting_for_number = State()

@dp.callback_query_handler(lambda c: c.data == 'qrcode', state=QrNumber.waiting_for_number)
async def process_next_product_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text('Вы выбрали способ оплаты заказа используя QR-код. Существует два способа оплаты QR-кодом.'
                                           '\n\n1️⃣ Наведите камеру телефона на QR-код, после чего вас автоматически перекинет в приложение банка на страницу оплаты по реквизитам.'
                                           '\n\n2️⃣ Сохраните QR-код, после чего зайдите в приложение банка в меню "Оплатить по QR-коду" и загрузите QR-код нажав на кнопку "Загрузить изображение".')
    await bot.send_photo(callback_query.message.chat.id, open('carych_payment.png', 'rb'))
    await callback_query.message.answer('🟢 Укажите сумму и в комментарии к платежу отправьте номер вашего заказа, оплатите заказ.'
                                        '\n\n✅ После успешной оплаты с вами свяжется консультант!')
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'number', state=QrNumber.waiting_for_number)
async def process_next_product_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text('Вы выбрали способ оплаты заказа используя номер телефона.'
                                           '\n\nРеквизиты для отправки по номеру телефона:'
                                           '\nНомер телефона: <code>+79617787178</code>'
                                           '\nПолучатель: <code>Михаил Валерьевич З.</code>'
                                           '\nБанк получателя: <code>Сбербанк</code>'
                                           '\n\n🟢 Укажите сумму и в комментарии к платежу отправьте номер вашего заказа, оплатите заказ.'
                                           '\n✅ После успешной оплаты с вами свяжется консультант!', parse_mode='html')
    await state.finish()






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

