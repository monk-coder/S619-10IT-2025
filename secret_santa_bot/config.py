import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = 'sqlite:///secret_santa.db'