# -*- coding: utf-8 -*-

import logging
import re
from functools import wraps

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from threading import Lock

__author__ = 'Rico'

BOT_TOKEN = "<your_bot_token>"
BOT_SENDS = "\U0001F916 *Bot:*"
STRANGER_SENDS = "\U0001F464:"

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

if not re.match(r"[0-9]+:[a-zA-Z0-9\-_]+", BOT_TOKEN):
    logging.error("Bot token not correct - please check.")
    exit(1)

updater = Updater(token=BOT_TOKEN)
dispatcher = updater.dispatcher
tg_bot = updater.bot
lock = Lock()

chatting_users = []
# TODO searching_users list must have as many fields, as there are search filters + 1.
searching_users = []


def restricted(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            logger.info("Unauthorized access denied for method '{}' for user {}.".format(func.__name__, user_id))
            return
        return func(bot, update, *args, **kwargs)

    return wrapped


def start(bot, update):
    user_id = update.message.from_user.id
    user = update.message.from_user
    db = sqlitedb.get_instance()
    db.add_user(user.id, "en", user.first_name, user.last_name, user.username)

    if (user_id not in searching_users) and (user_already_chatting(user_id) == -1):
        # search for another "searching" user in searching_users list
        if len(searching_users) > 0:
            # delete the other searching users from the list of searching_users
            logger.debug("Another user is searching now. There are 2 users. Matching them now!")

            with lock:
                partner_id = searching_users[0]
                del searching_users[0]

            # add both users to the list of chatting users with the user_id of the other user.
            chatting_users.append([user_id, partner_id])
            chatting_users.append([partner_id, user_id])

            bot.send_message(user_id, "{} {}".format(BOT_SENDS, "You are connected to a stranger. Have fun and be nice!"), parse_mode="Markdown")
            bot.send_message(partner_id, "{} {}".format(BOT_SENDS, "You are connected to a stranger. Have fun and be nice!"), parse_mode="Markdown")
        else:
            # if no user is searching, add him to the list of searching users.
            # TODO later when you can search for specific gender, this condition must be changed
            searching_users.append(user_id)
            bot.send_message(user_id, "{} {}".format(BOT_SENDS, "Added you to the searching users!"), parse_mode="Markdown")

    elif user_id in searching_users:
        bot.send_message(user_id, "{} {}".format(BOT_SENDS, "You are already searching. Please wait!"), parse_mode="Markdown")


def stop(bot, update):
    user_id = update.message.from_user.id
    if (user_id in searching_users) or (user_already_chatting(user_id) >= 0):

        if user_id in searching_users:
            # remove user from searching users
            index = user_already_searching(user_id)
            del searching_users[index]

        elif user_already_chatting(user_id) >= 0:
            # remove both users from chatting users
            partner_id = get_partner_id(user_id)

            index = user_already_chatting(user_id)
            del chatting_users[index]

            partner_index = user_already_chatting(partner_id)
            del chatting_users[partner_index]

            # send message that other user left the chat
            bot.send_message(partner_id, BOT_SENDS + "Your partner left the chat", parse_mode="Markdown")
            bot.send_message(user_id, BOT_SENDS + "You left the chat!", parse_mode="Markdown")


@restricted
def ban(bot, update, args):
    """Bans a user from using this bot - does not end a running chat of that user"""
    if len(args) == 0:
        return
    db = sqlitedb.get_instance()

    banned_user_id = args[0]
    logger.info("Banning user {}".format(banned_user_id))
    if not re.match("[0-9]+", banned_user_id):
        update.message.reply_text("{} UserID is in invalid format!".format(BOT_SENDS), parse_mode="Markdown")
        return

    db.ban(banned_user_id)
    update.message.reply_text("{} Banned user {}".format(BOT_SENDS, banned_user_id), parse_mode="Markdown")


def in_chat(bot, update):
    user_id = update.message.from_user.id

    if update.message.photo is not None:
        try:
            photo = update.message.photo[0].file_id
        except IndexError:
            photo = None

    text = update.message.text
    audio = update.message.audio
    voice = update.message.voice
    document = update.message.document
    caption = update.message.caption
    video = update.message.video
    video_note = update.message.video_note
    sticker = update.message.sticker
    location = update.message.location

    partner_id = get_partner_id(user_id)
    if partner_id != -1:
        if photo is not None:
            bot.send_photo(partner_id, photo=photo, caption=caption)
        elif audio is not None:
            bot.send_audio(partner_id, audio=audio.file_id)
        elif voice is not None:
            bot.send_voice(partner_id, voice=voice.file_id)
        elif video is not None:
            bot.send_video(partner_id, video=video.file_id)
        elif document is not None:
            bot.send_document(partner_id, document=document.file_id, caption=caption)
        elif sticker is not None:
            bot.send_sticker(partner_id, sticker=sticker.file_id)
        elif location is not None:
            bot.send_location(partner_id, location=location)
        elif video_note is not None:
            bot.send_video_note(partner_id, video_note=video_note.file_id)
        else:
            bot.send_message(partner_id, text="{} {}".format(STRANGER_SENDS, text))


def get_partner_id(user_id):
    if len(chatting_users) > 0:
        for pair in chatting_users:
            if pair[0] == user_id:
                return int(pair[1])

    return -1


# checks if user is already chatting with someone
# returns index in the list if yes
# returns -1 if user is not chatting
def user_already_chatting(user_id):
    counter = 0
    if len(chatting_users) > 0:
        for pair in chatting_users:
            if pair[0] == user_id:
                return counter
            counter += 1

    return -1


# checks if a user is already searching for a chat partner
# returns index in list of searching users, if yes
# returns -1 if user is not searching
def user_already_searching(user_id):
    counter = 0
    if len(searching_users) > 0:
        for user in searching_users:
            if user == user_id:
                return counter
            counter += 1

    return -1

handlers = []
handlers.append(CommandHandler('start', start))
handlers.append(CommandHandler('stop', stop))
handlers.append(CommandHandler('ban', ban, pass_args=True))
handlers.append(MessageHandler(Filters.all, in_chat))

for handler in handlers:
    dispatcher.add_handler(handler)

updater.start_polling()
