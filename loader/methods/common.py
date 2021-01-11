import base64
import secrets
import datetime

from django.core.files.base import ContentFile
from loader.models import Screenshots

def save_images(obj, test):
    ext = ".png"
    if "screens" in obj.data:
        if isinstance(obj.data["screens"], list) or isinstance(obj.data["screens"], dict):
            for screenshot in obj.data['screens']:
                # If images data has list/dict format, for example [{name: base64}, {name: base64}]
                year = datetime.date.today().year
                month = datetime.date.today().month
                day = datetime.date.today().day
                folder = secrets.token_urlsafe(6)
                path = f"screenshots/{year}/{month}/{day}/" + folder + "/"
                if isinstance(screenshot, dict):
                    name = screenshot["name"]
                    data = ContentFile(base64.b64decode(screenshot["image"]), name=folder + "/" + name + ext)
                    s_data = Screenshots(test=test, name=name, image=data,
                                         thumbnail=path + name + "_thumb" + ext)
                # Images as list items: [base64, base64...]
                else:
                    name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    data = ContentFile(base64.b64decode(screenshot), name=folder +"/ "+ name + ext)
                    s_data = Screenshots(test=test, name=name, image=data,
                                         thumbnail=path + "/" + name + "_thumb" + ext)

                s_data.save(folder, name)
