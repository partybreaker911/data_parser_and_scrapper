from flask_script import Manager
from dotenv import load_dotenv
from app import app

# Загрузка переменных окружения из файла .env
load_dotenv()

manager = Manager(app)

if __name__ == "__main__":
    # Создание базы данных
    with app.app_context():
        pass

    manager.run()
