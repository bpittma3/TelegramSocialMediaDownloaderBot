import json
import requests


def handle_url(link):
    headers = {'User-Agent': "Telegram Social Media Downloader Bot"}
    link_parts = link.split('/')
    id = link_parts[-1]
    try:
        response = requests.get(
            "https://api.fxtwitter.com/tgSocialMediaDownloaderBot/status/" + id, headers=headers)
        result = json.loads(response.text)
        if result['code'] == 200:
            return handle_tweet(result['tweet'])
        else:
            return {}
    except Exception as e:
        # Handle the exception here
        print("An error occurred:", str(e))


def handle_tweet(tweet):
    return_data = {}
    if "media" in tweet:
        if "mosaic" in tweet["media"]:
            return_data['type'] = "pic"
            return_data['media'] = tweet["media"]["mosaic"]["formats"]["jpeg"]
        elif "photos" in tweet["media"]:
            return_data['type'] = "pic"
            return_data['media'] = tweet["media"]["photos"][0]["url"]
        return_data['spoiler'] = tweet['possibly_sensitive']
    else:
        return_data['type'] = "text"
    return_data['text'] = tweet["text"]
    return_data['author'] = tweet["author"]["name"] + \
        " (@\\" + tweet["author"]["screen_name"] + ")"
    return_data['url'] = tweet['url']
    return return_data
