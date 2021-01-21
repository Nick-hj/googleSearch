
from google_search.utils.settings import load_or_create_settings
load_or_create_settings('')
from dynaconf import settings
from google_search.models.upload_image import sbi_via_upload_image
if __name__ == '__main__':
    sbi_via_upload_image('C:\\Users\\haiju\\Desktop\\女装-out.jpg')