
from google_search.utils.settings import load_or_create_settings
load_or_create_settings('')
from dynaconf import settings
from google_search.utils.config import BaseSettings
if __name__ == '__main__':
    print(settings.MYSQL.HOST)
    url = BaseSettings.redis_conn.lpop('data')
    print(url)