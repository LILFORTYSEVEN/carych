import mysql.connector


# Подключение к базе данных
database_connect = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="carych"
    )

