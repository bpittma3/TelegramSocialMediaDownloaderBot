def handle_url(ig_client, link):
    media_id = ig_client.media_pk_from_url(link)
    api_response = ig_client.media_info(media_id).dict()
    return_data = {}
    return_data['site'] = "instagram"
    return_data['id'] = api_response['id']
    return_data['url'] = link
    return_data['text'] = api_response['caption_text'] + \
        "\n" + api_response['accessibility_caption']
    return_data['spoiler'] = False
    match api_response['media_type']:
        case 1:  # photo
            return_data['media'] = [
                [api_response['thumbnail_url'].unicode_string(), "photo"]]
            return_data['type'] = "media"
            return return_data
        case 2:  # video
            return_data['media'] = [
                [api_response['video_url'].unicode_string(), "video"]]
            return_data['type'] = "media"
            return return_data
        case 8:  # album
            return_data['media'] = []
            for media in api_response['resources']:
                if media['media_type'] == 1:
                    return_data['media'].append(
                        [media['thumbnail_url'].unicode_string(), "photo"])
                elif media['media_type'] == 2:
                    return_data['media'].append(
                        [media['video_url'].unicode_string(), "video"])
                else:
                    print("This type of media (" +
                          media['media_type'] + ") is not supported.")
                    print(api_response)
            return return_data
        case _:  # unknown
            print("This type of media (" +
                  api_response['media_type'] + ") is not supported.")
            print(api_response)
            return {}
