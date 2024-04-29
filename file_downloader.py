import os
import time
from pathlib import Path
from urllib.request import urlretrieve


def download_video(url, site, id):
    filename = "temp/" + site + "/" + id + ".mp4"
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
                        id + str(time.time()) + ".mp4"
                    os.rename(temp_filename, final_filename)
                    return final_filename
        else:
            return filename
    except Exception as e:
        # Handle the exception here
        print("An error occurred:", str(e))
        return ""
