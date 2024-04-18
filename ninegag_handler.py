import json
import time
import requests
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from bs4 import BeautifulSoup

software_names = [SoftwareName.CHROME.value]
operating_systems = [OperatingSystem.WINDOWS.value,
                     OperatingSystem.LINUX.value]

user_agent_rotator = UserAgent(
    software_names=software_names, operating_systems=operating_systems, limit=100)


def handle_url(link):
    user_agent = user_agent_rotator.get_random_user_agent()
    headers = {'User-Agent': user_agent}
    try:
        response = requests.get(link, headers=headers)
        soup = BeautifulSoup(response.content.decode(), 'html.parser')
        for script in soup.find_all('script', attrs={"type": "text/javascript"}):
            if "window._config = JSON.parse" in script.get_text():
                script_json_text = script.get_text()
                # TODO: clean it up, the following 3 lines are the only way I found to remove single backslashes, while keeping double ones as a single one
                script_json_text = script_json_text.replace(
                    "\\\\", "420<impossible-to-happean-naturally-string>2137")
                script_json_text = script_json_text.replace("\\", "")
                script_json_text = script_json_text.replace(
                    "420<impossible-to-happean-naturally-string>2137", "\\")
                # remove beginning and the end of the json to extract only json content
                script_json_text = script_json_text.replace(
                    "window._config = JSON.parse(\"", "")
                script_json_text = script_json_text.replace("\");", "")
                script_json_content = json.loads(script_json_text)
                return check_media_type(script_json_content['data']['post'])
    except Exception as X:
        print(X)
        pass
    return {}


def check_media_type(post_json_data):
    match post_json_data['type']:
        case "Photo":
            return handle_picture(post_json_data)
        case "Animated":
            return handle_video(post_json_data)
        case _:
            print(str(time.time()))
            print(post_json_data['type'])
            json_formatted_str = json.dumps(post_json_data, indent=2)
            with open(str(time.time()), "w") as f:
                f.write(json_formatted_str)
            return {}


def handle_picture(post_json_data):
    return_data = {}
    return_data['type'] = "pic"
    return_data['id'] = post_json_data['id']
    return_data['url'] = post_json_data['url']
    return_data['title'] = post_json_data['title']
    if "image700" in post_json_data['images']:
        return_data['media'] = post_json_data['images']['image700']['url']
    elif "image460" in post_json_data['images']:
        return_data['media'] = post_json_data['images']['image460']['url']
    return return_data


def handle_video(post_json_data):
    return_data = {}
    return_data['type'] = "vid"
    return_data['id'] = post_json_data['id']
    return_data['url'] = post_json_data['url']
    return_data['title'] = post_json_data['title']
    if "image700sv" in post_json_data['images']:
        return_data['media'] = post_json_data['images']['image700sv']['url']
        if post_json_data['images']['image700sv']['hasAudio'] == 0 and post_json_data['images']['image700sv']['duration'] <= 20:
            return_data['type'] = "gif"
    elif "image460sv" in post_json_data['images']:
        return_data['media'] = post_json_data['images']['image460sv']['url']
        return_data['hasAudio'] = post_json_data['images']['image460sv']['hasAudio']
        if post_json_data['images']['image460sv']['hasAudio'] == 0 and post_json_data['images']['image460sv']['duration'] <= 20:
            return_data['type'] = "gif"
    return return_data
