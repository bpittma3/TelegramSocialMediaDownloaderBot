#!/usr/bin/env python3
import configparser
import json
import os
import re
import telebot

config = configparser.ConfigParser()
if os.path.isfile("config.txt"):
    config.read("config.txt")
else:
    print("No config file. Create config file and run the script again.")
    exit(1)

ALLOWED_USERS = json.loads(config['config']['allowed_users'])

bot = telebot.TeleBot(config['config']['token'])


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.from_user.id in ALLOWED_USERS:
        bot.reply_to(message, "Hi, I can download media from different social media and send them to you here on telegram. Send me a link and I'll take care of the rest.")
    else:
        print(message.from_user)
        bot.reply_to(
            message, "Hi, only approved users can use me. Contact " + config['config']['owner_username'] + " if you think you should get the access :)")


@bot.message_handler(regexp="http.*9gag", func=lambda message: message.from_user.id in ALLOWED_USERS)
def handle_9gag(message):
    bot.reply_to(message, "It looks like a link to 9gag.")
    msgContent = message.text.split()
    r = re.compile("http.*9gag")
    ninegagLinks = list(filter(r.match, msgContent))
    for link in ninegagLinks:
        link = link.split("?")
        bot.reply_to(message, link)


@bot.message_handler(regexp="http", func=lambda message: message.from_user.id in ALLOWED_USERS)
def handle_link(message):
    bot.reply_to(message, "This site is not supported yet.")


bot.polling()
