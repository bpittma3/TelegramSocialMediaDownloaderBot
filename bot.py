#!/usr/bin/env python3
import configparser
import json
import os
import re
import signal
import sys
import traceback

import telebot
from instagrapi import Client
from telebot.formatting import escape_markdown
from telebot.types import (InputMediaPhoto, InputMediaVideo,
                           LinkPreviewOptions, ReplyParameters)
from tendo import singleton

import file_downloader
import instagram_handler
import ninegag_handler
import twitter_handler

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
    "twitter": "((http.?://)|^| )(www.)?(x|twitter).com",
    "instagram": "((http.?://)|^| )(www.)?instagram.com",
}

instagram_client = Client()


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


@bot.message_handler(regexp=SITE_REGEXES['9gag'], func=lambda message: message.from_user.id in ALLOWED_USERS or message.chat.id in ALLOWED_CHATS)
@bot.message_handler(regexp=SITE_REGEXES['twitter'], func=lambda message: message.from_user.id in ALLOWED_USERS or message.chat.id in ALLOWED_CHATS)
@bot.message_handler(regexp=SITE_REGEXES['instagram'], func=lambda message: message.from_user.id in ALLOWED_USERS or message.chat.id in ALLOWED_CHATS)
def handle_supported_site(message):
    if message.forward_origin and message.forward_origin.sender_user.id == BOT_ID:
        return
    msgContent = message.text.split()

    r1 = re.compile(SITE_REGEXES['9gag'])
    ninegagLinks = list(filter(r1.match, msgContent))
    for link in ninegagLinks:
        link = link.split("?")  # we don't need parameters after ?
        handler_response = ninegag_handler.handle_url(link[0])
        if "type" in handler_response:
            send_post_to_tg(message, handler_response)
        else:
            print("Can't handle 9gag link: ")
            print(*link, sep="?")

    r2 = re.compile(SITE_REGEXES['twitter'])
    twitterLinks = list(filter(r2.match, msgContent))
    for link in twitterLinks:
        link = link.split("?")  # we don't need parameters after ?
        handler_response = twitter_handler.handle_url(link[0])
        if "type" in handler_response:
            send_post_to_tg(message, handler_response)
        else:
            print("Can't handle twitter link: ")
            print(*link, sep="?")

    r3 = re.compile(SITE_REGEXES['instagram'])
    igLinks = list(filter(r3.match, msgContent))
    for link in igLinks:
        link = link.split("?")  # we don't need parameters after ?
        handler_response = instagram_handler.handle_url(
            instagram_client, link[0])
        if "type" in handler_response:
            send_post_to_tg(message, handler_response)
        else:
            print("Can't handle instagram link: ")
            print(*link, sep="?")
            print(handler_response)


def send_post_to_tg(orig_tg_msg, handler_response):
    caption = prepare_caption(handler_response)
    msg_to_reply_to = orig_tg_msg

    if handler_response['site'] == "twitter":
        msg_to_reply_to = handle_quote_reply_tweet(
            orig_tg_msg, handler_response, caption)

    match (handler_response['type']):
        case "media":
            return send_media_post(orig_tg_msg, handler_response, caption, msg_to_reply_to)
        case "text":
            return send_text_post(orig_tg_msg, caption, msg_to_reply_to)
        case _:
            return bot.reply_to(msg_to_reply_to, ERROR_MESSAGE)


def prepare_caption(handler_response):
    caption = ""
    if "text" in handler_response:
        caption += handler_response['text']
    if "author" in handler_response:
        caption += "\n\nby: " + handler_response['author']
    if "url" in handler_response:
        caption += "\n" + handler_response['url']
    caption = escape_markdown(caption)

    if "poll" in handler_response and handler_response['poll'] == True:
        caption = "*This post is a poll\!*\n\n" + caption

    if handler_response['site'] == "twitter" and "community_note" in handler_response and handler_response['community_note'] == True:
        caption += parse_community_notes(handler_response)

    return caption


def parse_community_notes(handler_response):
    if "community_note_links" not in handler_response:
        return "\n\n*This tweet has community notes*:\n" + escape_markdown(handler_response['community_note_text'])

    note_arr = []
    split_indices = []
    links = []
    text = handler_response['community_note_text']

    split_indices.append(0)
    for link in handler_response['community_note_links']:
        split_indices.append(link['from'])
        split_indices.append(link['to'])
        links.append(link['url'])
    split_indices.append(None)

    link_index = 0
    for i in range(len(split_indices) - 1):
        is_link = i % 2 == 1
        if not is_link:
            note_arr.append(
                {"text": text[split_indices[i]:split_indices[i+1]], "is_link": is_link})
        else:
            note_arr.append({"text": text[split_indices[i]:split_indices[i+1]],
                            "is_link": is_link, "link": links[link_index]})
            link_index += 1

    note = "\n\n*This tweet has community notes*:\n"
    for note_part in note_arr:
        if note_part["is_link"]:
            note += "[" + escape_markdown(note_part["text"]) + \
                "](" + note_part["link"] + ")"
        else:
            note += escape_markdown(note_part["text"])

    return note


def handle_quote_reply_tweet(orig_tg_msg, handler_response, caption):
    if handler_response['quote']:
        if orig_tg_msg.chat.id not in ALLOWED_CHATS:
            handler_response_for_quote_tweet = twitter_handler.handle_url(
                handler_response['quote_url'])
            if "type" in handler_response_for_quote_tweet:
                return send_post_to_tg(
                    orig_tg_msg, handler_response_for_quote_tweet)
            else:
                print("Can't handle twitter link: " +
                      handler_response['quote_url'])
                return orig_tg_msg
        else:
            caption += "\n\n*Note:* This message is a quote tweet\."
            return orig_tg_msg
    elif handler_response['reply']:
        if orig_tg_msg.chat.id not in ALLOWED_CHATS:
            handler_response_for_reply_to_tweet = twitter_handler.handle_url(
                handler_response['reply_url'])
            if "type" in handler_response_for_reply_to_tweet:
                return send_post_to_tg(
                    orig_tg_msg, handler_response_for_reply_to_tweet)
            else:
                print("Can't handle twitter link: " +
                      handler_response['reply_url'])
                return orig_tg_msg
        else:
            caption += "\n\n*Note:* This message is a reply to another tweet\."
            return orig_tg_msg
    else:
        return orig_tg_msg


def send_media_post(orig_tg_msg, handler_response, caption, msg_to_reply_to):
    if len(handler_response['media']) == 1:
        return send_singular_media_post(
            orig_tg_msg, handler_response, caption, msg_to_reply_to)
    else:
        return send_multiple_media_post(
            orig_tg_msg, handler_response, caption, msg_to_reply_to)


def send_singular_media_post(orig_tg_msg, handler_response, caption, msg_to_reply_to):
    media = handler_response['media'][0]
    if media[1] == "photo":
        sent_message = bot.send_photo(chat_id=orig_tg_msg.chat.id,
                                      photo=media[0],
                                      caption=caption,
                                      has_spoiler=handler_response['spoiler'],
                                      reply_parameters=ReplyParameters(
                                          message_id=msg_to_reply_to.message_id,
                                          allow_sending_without_reply=True))
    elif media[1] == "video":
        sent_message = bot.send_video(chat_id=orig_tg_msg.chat.id,
                                      video=media[0],
                                      caption=caption,
                                      has_spoiler=handler_response['spoiler'],
                                      reply_parameters=ReplyParameters(
                                          message_id=msg_to_reply_to.message_id,
                                          allow_sending_without_reply=True))
    elif media[1] == "gif":
        sent_message = bot.send_animation(chat_id=orig_tg_msg.chat.id,
                                          animation=media[0],
                                          caption=caption,
                                          has_spoiler=handler_response['spoiler'],
                                          reply_parameters=ReplyParameters(
                                              message_id=msg_to_reply_to.message_id,
                                              allow_sending_without_reply=True))
    else:
        print("This type of media (" + media[1] + ") is not supported.")
        print(handler_response)
        return orig_tg_msg

    delete_handled_message(orig_tg_msg)
    return sent_message


def send_multiple_media_post(orig_tg_msg, handler_response, caption, msg_to_reply_to):
    media_group = []
    i = 0
    for media in handler_response['media']:
        if media[1] == "photo":
            media_group.append(InputMediaPhoto(
                media=media[0], has_spoiler=handler_response['spoiler']))
        elif media[1] == "video":
            media_group.append(InputMediaVideo(
                media=media[0], has_spoiler=handler_response['spoiler']))
        elif media[1] == "gif":
            filename = file_downloader.download_video(
                media[0], handler_response['site'], handler_response['id'] + "_" + str(i))
            i += 1
            media_group.append(InputMediaVideo(
                media=open(filename, "rb"), has_spoiler=handler_response['spoiler']))
        else:
            print("This type of media (" + media[1] + ") is not supported.")
            print(handler_response)

    if len(media_group) > 1:
        media_group[0].caption = caption
        # workaround for a bug in telebot, will be fixed in a newer than 4.17.0 release
        media_group[0].parse_mode = PARSE_MODE
        sent_message_arr = bot.send_media_group(chat_id=orig_tg_msg.chat.id,
                                                media=media_group,
                                                reply_parameters=ReplyParameters(
                                                    message_id=msg_to_reply_to.message_id,
                                                    allow_sending_without_reply=True))

        delete_handled_message(orig_tg_msg)
        # send_media_group returns an array of msgs, we need just the first one
        return sent_message_arr[0]
    else:
        print("Multi media post contains only one supported media.")
        print(handler_response)
        return orig_tg_msg


def send_text_post(orig_tg_msg, caption, msg_to_reply_to):
    sent_message = bot.send_message(chat_id=orig_tg_msg.chat.id,
                                    text=caption,
                                    reply_parameters=ReplyParameters(
                                        message_id=msg_to_reply_to.message_id,
                                        allow_sending_without_reply=True),
                                    link_preview_options=LinkPreviewOptions(is_disabled=True))
    delete_handled_message(orig_tg_msg)
    return sent_message


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


def exit_gracefully(signum, frame):
    print("Captured signal: " + str(signum))
    traceback.print_stack(frame)
    sys.exit(signum)

# def main():


signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

if config['instagram'].getboolean('do_login'):
    instagram_handler.login_ig_user(instagram_client, config['instagram'])
else:
    instagram_handler.set_basic_settings(instagram_client)

while True:
    try:
        bot.polling()
    except Exception as e:
        # Handle the exception here
        print("An error occurred:", str(e))
