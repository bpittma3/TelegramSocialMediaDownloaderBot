#!/usr/bin/env python3
import ninegag_handler
import twitter_handler
import configparser
import json
import os
import re
import telebot
from telebot.types import ReplyParameters, InputFile
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


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.from_user.id in ALLOWED_USERS:
        bot.reply_to(message, "Hi, I can download media from different social media and send them to you here on telegram. Send me a link and I'll take care of the rest.")
    else:
        print(message.from_user)
        bot.reply_to(
            message, "Hi, only approved users can use me. Contact " + config['config']['owner_username'] + " if you think you should get the access :)")


@bot.message_handler(regexp="http.*9gag", func=lambda message: message.from_user.id in ALLOWED_USERS or message.chat.id in ALLOWED_CHATS)
def handle_9gag(message):
    # bot.reply_to(message, "It looks like a link to 9gag.")
    msgContent = message.text.split()
    r = re.compile("http.*9gag")
    ninegagLinks = list(filter(r.match, msgContent))
    for link in ninegagLinks:
        link = link.split("?")
        maybe_tg_media = ninegag_handler.handle_url(link[0])
        if "media" in maybe_tg_media:
            caption = maybe_tg_media['title'] + \
                "\n" + maybe_tg_media['url']
            match (maybe_tg_media['type']):
                case "pic":
                    bot.send_photo(chat_id=message.chat.id,
                                   photo=maybe_tg_media['media'],
                                   caption=caption,
                                   reply_parameters=ReplyParameters(message_id=message.message_id, allow_sending_without_reply=True))
                    delete_handled_message(message)
                case "gif":
                    bot.send_animation(chat_id=message.chat.id,
                                       animation=maybe_tg_media['media'],
                                       caption=caption,
                                       reply_parameters=ReplyParameters(message_id=message.message_id, allow_sending_without_reply=True))
                    delete_handled_message(message)
                case "vid":
                    if "filename" in maybe_tg_media:
                        bot.send_video(chat_id=message.chat.id,
                                       video=InputFile(
                                           maybe_tg_media['filename']),
                                       caption=caption,
                                       reply_parameters=ReplyParameters(message_id=message.message_id, allow_sending_without_reply=True))
                        delete_handled_message(message)
                    else:
                        bot.reply_to(
                            message, "Can't download this 9gag post. Try again later.")
                case _:
                    bot.reply_to(
                        message, "Can't download this 9gag post. Try again later.")
        else:
            bot.reply_to(
                message, "Can't download this 9gag post. Try again later.")


@bot.message_handler(regexp="https://x.com", func=lambda message: message.from_user.id in ALLOWED_USERS or message.chat.id in ALLOWED_CHATS)
@bot.message_handler(regexp="http.*twitter", func=lambda message: message.from_user.id in ALLOWED_USERS or message.chat.id in ALLOWED_CHATS)
def handle_twitter(message):
    msgContent = message.text.split()
    r = re.compile("(https://x.com|http.*twitter)")
    twitterLinks = list(filter(r.match, msgContent))
    for link in twitterLinks:
        link = link.split("?")
        maybe_twitter_media = twitter_handler.handle_url(link[0])
        if "type" in maybe_twitter_media:
            caption = maybe_twitter_media['text'] + \
                "\nby: " + maybe_twitter_media['author'] + \
                "\n" + maybe_twitter_media['url']
            match (maybe_twitter_media['type']):
                case "pic":
                    bot.send_photo(chat_id=message.chat.id,
                                   photo=maybe_twitter_media['media'],
                                   caption=caption,
                                   has_spoiler=maybe_twitter_media['spoiler'],
                                   reply_parameters=ReplyParameters(message_id=message.message_id, allow_sending_without_reply=True))
                    delete_handled_message(message)
                case "text":
                    bot.reply_to(message, caption)
                    delete_handled_message(message)
                case _:
                    bot.reply_to(
                        message, "Can't download this tweet. Try again later.")


@bot.message_handler(regexp="http", func=lambda message: message.from_user.id in ALLOWED_USERS or message.chat.id in ALLOWED_CHATS)
def handle_link(message):
    if message.chat.id not in ALLOWED_CHATS:
        bot.reply_to(message, "This site is not supported yet.")


def delete_handled_message(message):
    try:
        bot.delete_message(message.chat.id, message.id)
    except Exception as X:
        print(X)
        print("Cant remove message in chat " +
              message.chat.title + " (" + str(message.chat.id) + ").")


while (True):
    try:
        bot.polling()
    except Exception as X:
        print(X)
