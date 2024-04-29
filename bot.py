#!/usr/bin/env python3
import ninegag_handler
import twitter_handler
import configparser
import json
import os
import re
import telebot
from telebot.types import ReplyParameters, InputMediaPhoto, InputMediaVideo, LinkPreviewOptions
from telebot.formatting import escape_markdown
from tendo import singleton

me = singleton.SingleInstance()  # will sys.exit(-1) if other instance is running

config = configparser.ConfigParser()
if os.path.isfile("config.txt"):
    config.read("config.txt")
else:
    print("No config file. Create config file and run the script again.")
    exit(1)

ALLOWED_USERS = json.loads(config['config']['allowed_users'])
ALLOWED_CHATS = json.loads(config['config']['allowed_chats'])

bot = telebot.TeleBot(config['config']['token'])
BOT_ID = bot.get_me().id
PARSE_MODE = "MarkdownV2"
bot.parse_mode = PARSE_MODE

ERROR_MESSAGE = escape_markdown("Can't download this post. Try again later.")

SITE_REGEXES = {
    "9gag": "((http.?://)|^| )(www.)?9gag.com",
    "twitter": "((http.?://)|^| )(www.)?(x|twitter).com"
}


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.from_user.id in ALLOWED_USERS:
        welcome_message_text = escape_markdown("Hi, I can download media from different social media and send" +
                                               " them to you here on telegram. Send me a link and I'll take care of the rest.")
        bot.reply_to(message=message, text=welcome_message_text)
    else:
        print(message.from_user)
        unwelcome_message_text = escape_markdown("Hi, only approved users can use me. Contact " +
                                                 config['config']['owner_username'] +
                                                 " if you think you should get the access :)")
        bot.reply_to(message=message,
                     text=unwelcome_message_text,
                     parse_mode=None)


@bot.message_handler(regexp=SITE_REGEXES["9gag"], func=lambda message: message.from_user.id in ALLOWED_USERS or message.chat.id in ALLOWED_CHATS)
def handle_9gag(message):
    if message.forward_origin and message.forward_origin.sender_user.id == BOT_ID:
        return
    # bot.reply_to(message, "It looks like a link to 9gag.")
    msgContent = message.text.split()
    r = re.compile(SITE_REGEXES["9gag"])
    ninegagLinks = list(filter(r.match, msgContent))
    for link in ninegagLinks:
        link = link.split("?")
        maybe_tg_media = ninegag_handler.handle_url(link[0])
        if "media" in maybe_tg_media:
            caption = maybe_tg_media['title'] + \
                "\n" + maybe_tg_media['url']
            caption = escape_markdown(caption)
            match (maybe_tg_media['type']):
                case "pic":
                    bot.send_photo(chat_id=message.chat.id,
                                   photo=maybe_tg_media['media'],
                                   caption=caption,
                                   reply_parameters=ReplyParameters(
                                       message_id=message.message_id, allow_sending_without_reply=True))
                    delete_handled_message(message)
                case "gif":
                    bot.send_animation(chat_id=message.chat.id,
                                       animation=maybe_tg_media['media'],
                                       caption=caption,
                                       reply_parameters=ReplyParameters(
                                           message_id=message.message_id, allow_sending_without_reply=True))
                    delete_handled_message(message)
                case "vid":
                    bot.send_video(chat_id=message.chat.id,
                                   video=maybe_tg_media['media'],
                                   caption=caption,
                                   reply_parameters=ReplyParameters(
                                       message_id=message.message_id, allow_sending_without_reply=True))
                    delete_handled_message(message)
                case _:
                    bot.reply_to(message, ERROR_MESSAGE)
        else:
            bot.reply_to(message, ERROR_MESSAGE)


@bot.message_handler(regexp=SITE_REGEXES["twitter"], func=lambda message: message.from_user.id in ALLOWED_USERS or message.chat.id in ALLOWED_CHATS)
def handle_twitter(message):
    if message.forward_origin and message.forward_origin.sender_user.id == BOT_ID:
        return
    msgContent = message.text.split()
    r = re.compile(SITE_REGEXES["twitter"])
    twitterLinks = list(filter(r.match, msgContent))
    for link in twitterLinks:
        link = link.split("?")
        maybe_twitter_media = twitter_handler.handle_url(link[0])
        if "type" in maybe_twitter_media:
            sent_twitter_reply(message, maybe_twitter_media)


def sent_twitter_reply(message, maybe_twitter_media):
    caption = maybe_twitter_media['text'] + \
        "\n\nby: " + maybe_twitter_media['author'] + \
        "\n" + maybe_twitter_media['url']
    caption = escape_markdown(caption)

    if maybe_twitter_media["poll"]:
        caption = "*This tweet is a poll\!*\n\n" + caption

    if maybe_twitter_media["quote"]:
        if message.chat.id not in ALLOWED_CHATS:
            maybe_quote_twitter_media = twitter_handler.handle_url(
                maybe_twitter_media["quote_url"])
            tg_reply_message = sent_twitter_reply(
                message, maybe_quote_twitter_media)
        else:
            caption += "\n\n*Note:* This message is a quote tweet\."
            tg_reply_message = message
    elif maybe_twitter_media["reply"]:
        if message.chat.id not in ALLOWED_CHATS:
            maybe_reply_twitter_media = twitter_handler.handle_url(
                maybe_twitter_media["reply_url"])
            tg_reply_message = sent_twitter_reply(
                message, maybe_reply_twitter_media)
        else:
            caption += "\n\n*Note:* This message is a reply to another tweet\."
            tg_reply_message = message
    else:
        tg_reply_message = message

    match (maybe_twitter_media['type']):
        case "media":
            if len(maybe_twitter_media['media']) == 1:
                media = maybe_twitter_media['media'][0]
                if media[1] == "photo":
                    return_message = bot.send_photo(chat_id=message.chat.id,
                                                    photo=media[0],
                                                    caption=caption,
                                                    has_spoiler=maybe_twitter_media['spoiler'],
                                                    reply_parameters=ReplyParameters(
                                                        message_id=tg_reply_message.message_id, allow_sending_without_reply=True))
                elif media[1] == "video":
                    return_message = bot.send_video(chat_id=message.chat.id,
                                                    video=media[0],
                                                    caption=caption,
                                                    has_spoiler=maybe_twitter_media['spoiler'],
                                                    reply_parameters=ReplyParameters(
                                                        message_id=tg_reply_message.message_id, allow_sending_without_reply=True))
                elif media[1] == "gif":
                    return_message = bot.send_animation(chat_id=message.chat.id,
                                                        animation=media[0],
                                                        caption=caption,
                                                        has_spoiler=maybe_twitter_media['spoiler'],
                                                        reply_parameters=ReplyParameters(
                                                            message_id=tg_reply_message.message_id, allow_sending_without_reply=True))
            else:
                media_group = []
                i = 0
                for media in maybe_twitter_media['media']:
                    if media[1] == "photo":
                        media_group.append(InputMediaPhoto(
                            media=media[0], has_spoiler=maybe_twitter_media['spoiler']))
                    elif media[1] == "video":
                        media_group.append(InputMediaVideo(
                            media=media[0], has_spoiler=maybe_twitter_media['spoiler']))
                    elif media[1] == "gif":
                        filename = twitter_handler.download_video(
                            media[0], maybe_twitter_media['id'] + "_" + str(i))
                        i += 1
                        media_group.append(InputMediaVideo(
                            media=open(filename, "rb"), has_spoiler=maybe_twitter_media['spoiler']))
                    else:
                        continue

                if len(media_group) > 1:
                    media_group[0].caption = caption
                    # workaround for a bug in telebot
                    media_group[0].parse_mode = PARSE_MODE
                    return_message_arr = bot.send_media_group(chat_id=message.chat.id,
                                                              media=media_group,
                                                              reply_parameters=ReplyParameters(
                                                                  message_id=tg_reply_message.message_id, allow_sending_without_reply=True))

                    # send_media_group returns an array of msgs, we need just the first one
                    return_message = return_message_arr[0]

            delete_handled_message(message)
        case "text":
            return_message = bot.send_message(chat_id=message.chat.id,
                                              text=caption,
                                              reply_parameters=ReplyParameters(
                                                  message_id=tg_reply_message.message_id, allow_sending_without_reply=True),
                                              link_preview_options=LinkPreviewOptions(is_disabled=True))
            delete_handled_message(message)
        case _:
            return_message = bot.reply_to(message, ERROR_MESSAGE)

    return return_message


@bot.message_handler(regexp="http", func=lambda message: message.from_user.id in ALLOWED_USERS or message.chat.id in ALLOWED_CHATS)
def handle_link(message):
    if message.chat.id not in ALLOWED_CHATS:
        bot.reply_to(message, "This site is not supported yet\.")


@bot.message_handler(regexp="test", func=lambda message: message.from_user.id in ALLOWED_USERS)
def test(message):
    pass


def delete_handled_message(message):
    try:
        bot.delete_message(message.chat.id, message.id)
    except Exception as e:
        # Handle the exception here
        print("An error occurred:", str(e))
        print("Cant remove message in chat " +
              str(message.chat.title) + " (" + str(message.chat.id) + ").")


while (True):
    try:
        bot.polling()
    except Exception as e:
        # Handle the exception here
        print("An error occurred:", str(e))
