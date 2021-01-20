import redis
from pathlib import Path
from typing import Optional
from dynaconf import loaders, settings
from google_search.utils.logger import logger

DEFAULT_PATH = "settings.toml"
BASE_SETTINGS = {
    "IS_DEVE": True,
    "BASE_URL": "https://www.google.com/",
    "HOME_DIR": str(Path().absolute()),
    "REDIS": {
        "HOST": 'localhost',
        "PORT": 6379,
        "DB": 4,
        "PASSWD": ""
    },
    "MYSQL": {
        "HOST": "",
        "USER": "",
        "PASSWD": "",
        "DATABASE": "",
        "PORT": 3306
    },
    "PUSH_URL_WITH_SBI_REDIS_KEY": 'PUSH_URL_WITH_SBI_REDIS_KEY',  # redis 获取带有sbi的url存入redis
    "USER_AGENT": [
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36"
    ]

}


def load_or_create_settings(path: Optional[str]):
    path = path or DEFAULT_PATH
    print(Path(path).exists())
    print(path)
    if not Path(path).exists():
        default_settings_path = str(Path.cwd() / Path(DEFAULT_PATH))
        logger.info(
            f'没有发现配置文件 "{Path(path).absolute()}". '
            f"创建默认配置文件: {default_settings_path}",
        )
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        loaders.write(default_settings_path, BASE_SETTINGS, env="default")

    settings.load_file(path=path)
    logger.info("配置文件加载成功")
