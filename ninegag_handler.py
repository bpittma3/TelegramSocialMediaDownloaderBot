import json
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
    response = requests.get(link, headers=headers)
    soup = BeautifulSoup(response.content.decode(), 'html.parser')
    for script in soup.find_all('script', attrs={"type": "text/javascript"}):
        if "window._config = JSON.parse" in script.get_text():
            temp0 = script.get_text()
            temp1 = temp0.replace("\\", "")
            temp2 = temp1.replace("window._config = JSON.parse(\"", "")
            script_json_text = temp2.replace("\");", "")
            script_json_content = json.loads(script_json_text)
            check_media_type(script_json_content['data']['post'])


def check_media_type(post_json_data):
    match post_json_data['type']:
        case "Photo":
            handle_picture(post_json_data)


def handle_picture(post_json_data):
    return_data = {}
    return_data['url'] = post_json_data['url']
    return_data['title'] = post_json_data['title']
    return_data['media'] = post_json_data['images']['image700']['url']
    print(return_data)


handle_url("https://9gag.com/gag/a9yjpq0")
