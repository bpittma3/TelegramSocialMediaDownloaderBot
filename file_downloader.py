import os
import time
import traceback
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlretrieve


def download_video(url, site, id):
    path = urlparse(url).path
    ext = os.path.splitext(path)[1] or ".mp4"
    filename = "temp/" + site + "/" + id + ext
    temp_filename = filename + ".temp." + str(time.time())
    try:
        Path("temp/" + site + "/").mkdir(parents=True, exist_ok=True)
        if (not os.path.isfile(filename)):
            if (not os.path.isfile(temp_filename)):
                urlretrieve(url, temp_filename)
                if not os.path.isfile(filename):
                    os.rename(temp_filename, filename)
                    return filename
                else:
                    final_filename = "temp/" + site + "/" + \
                        id + str(time.time()) + ext
                    os.rename(temp_filename, final_filename)
                    return final_filename
        else:
            return filename
    except Exception as e:
        print(time.strftime("%d.%m.%Y %H:%M:%S", time.localtime()))
        traceback.print_exception(type(e), e, e.__traceback__)
        print("Couldn't download video from url: " + url)
        print()
        return ""
