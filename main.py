import flask
import requests
import datetime
import pandas as pd
import os
# import json
import re
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import math
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


# CryptoInformerBot
TOKEN = "1742351143:AAFMkOhnIwnVcZ6P3PXrNSdSNAa3BJeJw4M"
URL = "https://api.telegram.org/bot1742351143:AAFMkOhnIwnVcZ6P3PXrNSdSNAa3BJeJw4M/"


# Telebotik
# TOKEN = "1596358230:AAG2Set8-LxEoE2UZDOVq8f0crYnh3iLACw"
# URL = "https://api.telegram.org/bot1596358230:AAG2Set8-LxEoE2UZDOVq8f0crYnh3iLACw/"

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:postgres@localhost:5432/postgres"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


import dataloader
import pghelper
# import models


df = pd.read_csv("coins.csv")
COINS = pd.read_csv("coins.csv")["name"].to_list()
SYMBOLS = pd.read_csv("coins.csv")["symbol"].to_list()
users = {}
alarm_enter_listener = {}
tz_delta_enter_listener = {}
MAX_SCHED_ALARM = 3
currently_checked_price_for_sched = {}
currently_checked_price_for_alarm = {}


# FIXME: remve temp methods
# region =========== TEMP =====================
def send_user_info(chat_id):
    user = pghelper.get_user_info(chat_id)
    msg = "<b>User info:</b>\n"
    if user is not None:
        msg += " - Name: {}\n".format(user.first_name)
        msg += " - Time delta: {}\n".format(user.tz_delta)
    else:
        msg += "There is no any user in database yet"
    url = URL + "sendMessage"
    answer = {"chat_id": chat_id, "text": msg, "parse_mode": "html"}
    requests.post(url, json=answer)


def send_alarm_info(chat_id):
    alarms = pghelper.get_alarms(chat_id)
    msg = "<b>Alarms info:</b>\n"
    if alarms is not None:
        for alarm in alarms:
            msg += " - coin symbol: {}\n".format(alarm.coin_symbol)
            msg += " - coin name: {}\n".format(alarm.coin_name)
            msg += " - min value: {}\n".format(alarm.min_value)
            msg += " - max value: {}\n".format(alarm.max_value)
            msg += "----------\n"
    else:
        msg += "No alarms yet"
    url = URL + "sendMessage"
    answer = {"chat_id": chat_id, "text": msg, "parse_mode": "html"}
    requests.post(url, json=answer)


def send_schedule_info(chat_id):
    schedules = pghelper.get_schedules(chat_id)
    msg = "<b>Schedules info:</b>\n"
    if schedules is not None:
        for schedule in schedules:
            msg += " - coin symbol: {}\n".format(schedule.coin_symbol)
            msg += " - coin name: {}\n".format(schedule.coin_name)
            msg += " - is daily: {}\n".format(schedule.is_daily)
            msg += " - time daily: {}\n".format(schedule.time_daily)
            msg += " - hourly interval: {}\n".format(schedule.hourly_interval)
            msg += " - last send: {}\n".format(datetime.datetime.fromtimestamp(schedule.last_send).isoformat())
            msg += "----------\n"
    else:
        msg += "No schedules yet"
    url = URL + "sendMessage"
    answer = {"chat_id": chat_id, "text": msg, "parse_mode": "html"}
    requests.post(url, json=answer)


# endregion  ===============================


def send_sticker(chat_id, filename):
    url = URL + "sendSticker"
    params = {'chat_id': chat_id}
    with open(filename, "rb") as f:
        files = {'sticker': f}
        requests.post(url, params, files=files)


def send_photo(chat_id, filename):
    url = URL + "sendPhoto"
    params = {'chat_id': chat_id}
    with open(filename, "rb") as f:
        files = {'photo': f}
        requests.post(url, params, files=files)


# send simple message with text
def send_message(chat_id, text="Bla-bla-bla again today..."):
    url = URL + "sendMessage"
    # answer json for POST request
    answer = {"chat_id": chat_id,
              "text": text,
              "parse_mode": "html"}
    requests.post(url, json=answer)


def send_message_with_reply_keyboard(chat_id, text=""):
    url = URL + "sendMessage"
    # answer with ReplyKeyboard
    answer = {"chat_id": chat_id,
              "text": text,
              "reply_markup": {
                  "keyboard": [[{"text": "Bitcoin"}, {"text": "Other currency"}],
                               [{"text": "Available currencies"}, {"text": "Settings"}],
                               [{"text": "Schedule"}, {"text": "Alarm"}]],
                  "resize_keyboard": True}}
    requests.post(url, json=answer)


def send_price_with_inline_keyboard(chat_id, text="", prefix="price:"):
    url = URL + "sendMessage"
    # answer with InlineKeyboard
    answer = {"chat_id": chat_id,
              "text": text,
              "reply_markup": {
                  "inline_keyboard": [
                      [{"text": "Show 1d history", "callback_data": prefix + "last_changes"},
                      {"text": "Show 7d history", "callback_data": prefix + "show_history"}],
                      [{"text": "Cancel", "callback_data": "cancel:cancel"}]]}}
    requests.post(url, json=answer)


def send_coins_with_inline_keyboard(chat_id, text="", prefix="price:0"):  # prefix example:  sched:0
    url = URL + "sendMessage"
    # print("send_coins_with_inline_keyboard() prefix -> ", prefix)
    # answer with InlineKeyboard - 22 buttons with coins' symbols
    inline_keyboard = all_coins_inline_keyboard(prefix)
    answer = {"chat_id": chat_id,
              "text": text,
              "reply_markup": {
                  "inline_keyboard": inline_keyboard}}

    requests.post(url, json=answer)


def all_coins_inline_keyboard(prefix):
    lbls = []
    num = 0
    pref = ""
    pinf = prefix.split(":")
    if len(pinf) > 1:
        pref = pinf[0] + ":"
        num = int(pinf[-1])

    if num < 5:
        for indx in range(num * 9, num * 9 + 9):
            lbl = df.iloc[indx]["symbol"]
            lbls.append(lbl)
    else:
        for indx in range(45, 50):
            lbl = df.iloc[indx]["symbol"]
            lbls.append(lbl)

    inline_keyboard = [[
        {"text": lbls[0], "callback_data": pref + lbls[0]},
        {"text": lbls[1], "callback_data": pref + lbls[1]},
        {"text": lbls[2], "callback_data": pref + lbls[2]}
    ], [
        {"text": lbls[3], "callback_data": pref + lbls[3]},
        {"text": lbls[4], "callback_data": pref + lbls[4]}]
    ]
    # print("all_coins_inline_keyboard() prefix -> {}, pinf -> {}, pref -> {}, num -> {}".format(prefix,pinf, pref,num))
    prev_next_hide = [{"text": "Cancel", "callback_data": "cancel:cancel"}]
    if num < 5:
        added_buttons = [
            {"text": lbls[6], "callback_data": pref + lbls[6]},
            {"text": lbls[7], "callback_data": pref + lbls[7]},
            {"text": lbls[8], "callback_data": pref + lbls[8]}]
        inline_keyboard[1].append({"text": lbls[5], "callback_data": pref + lbls[5]})
        inline_keyboard.append(added_buttons)
        pref1 = "next:" + pref + str(num)
        prev_next_hide.insert(0, {"text": "Next", "callback_data": pref1})
    if num > 0:
        pref2 = "prev:" + pref + str(num)
        prev_next_hide.insert(0, {"text": "Previous", "callback_data": pref2})

    inline_keyboard.append(prev_next_hide)
    return inline_keyboard


def on_tap_prev_next_keyboard(chat_id, message_id, message, prefix):
    url = URL + "editMessageText"
    inline_keyboard = all_coins_inline_keyboard(prefix)
    answer = {"chat_id": chat_id,
              "message_id": message_id,
              "text": message,
              "reply_markup": {
                  "inline_keyboard": inline_keyboard}
              }
    requests.post(url, json=answer)


def remove_inline_keyboard(chat_id, message_id, text):
    url = URL + "editMessageText"
    answer = {"chat_id": chat_id,
              "message_id": message_id,
              "text": text,
              "parse_mode": "html"}
    requests.post(url, json=answer)


def send_message_schedule(chat_id, sched_exists, prefix):  # prefix -> "add_del_schedule:BTC"
    url = URL + "sendMessage"
    print("send_message_schedule() --> prefix: {}, exists = ".format(prefix), sched_exists)
    prefix_list = prefix.split(":")
    callback = "add_schedule:" + prefix_list[1] + ":"
    if sched_exists == False:
        msg = "I can inform you daily or hourly about currency price"
        answer = {"chat_id": chat_id,
                  "text": msg,
                  "reply_markup": {
                      "inline_keyboard": [[
                          {"text": "Daily", "callback_data": callback + "daily"},
                          {"text": "Hourly", "callback_data": callback + "hourly"},
                          {"text": "Cancel", "callback_data": "cancel:cancel"}]]}}
        requests.post(url, json=answer)
    else:
        send_message_replace_schedule(chat_id, prefix)


def send_message_replace_schedule(chat_id, prefix):
    url = URL + "sendMessage"
    pref = "replace_sched:" + prefix
    pref_list = prefix.split(":")

    sched = pghelper.get_schedule_for_coin(chat_id, pref_list[-1]);
    if schedules is not None:
        # schedule = schedules[0]
        coin_name = sched.coin_name
        coin_symbol = sched.coin_symbol
        is_daily = sched.is_daily
        time_daily = sched.time_daily
        hourly_interval = sched.hourly_interval
        msg = "<b><u>You already have schedule for {}:</u></b>\n<b>You will be informed about {} ({}) price ".format(
            coin_name,
            coin_name,
            coin_symbol)

        if is_daily > 0:
            msg += "daily at {}:00</b>".format(time_daily)
        else:
            if hourly_interval == 1:
                msg += "every hour</b>"
            else:
                msg += "every {} hours</b>".format(hourly_interval)

    msg += "\n\nReplace existing scedule for {}?".format(pref_list[-1])
    # answer with InlineKeyboard
    answer = {"chat_id": chat_id,
              "text": msg,
              "reply_markup": {
                  "inline_keyboard": [[{"text": "Replace", "callback_data": pref},
                                       {"text": "Cancel", "callback_data": "cancel:cancel"}]]},
              "parse_mode": "html"}
    requests.post(url, json=answer)


def send_message_replace_alarm(chat_id, coin_symbol, msg):
    url = URL + "sendMessage"
    pref = "replace_alarm_max_num:" + coin_symbol
    text = msg
    # answer with InlineKeyboard
    answer = {"chat_id": chat_id,
              "text": text,
              "reply_markup": {
                  "inline_keyboard": [
                      [{"text": "Remove", "callback_data": pref},
                       {"text": "Cancel", "callback_data": "cancel:cancel"}]]},
              "parse_mode": "html"}
    requests.post(url, json=answer)


def send_message_ask_time(chat_id, prefix):
    url = URL + "sendMessage"
    msg = "Select the time when do you want to get info"
    callback = "sched_day_time:" + prefix + ":"
    answer = {"chat_id": chat_id,
              "text": msg,
              "reply_markup": {
                  "inline_keyboard": [[
                      {"text": "8:00", "callback_data": callback + "8"},
                      {"text": "9:00", "callback_data": callback + "9"},
                      {"text": "10:00", "callback_data": callback + "10"},
                      {"text": "11:00", "callback_data": callback + "11"}],
                      [{"text": "12:00", "callback_data": callback + "12"},
                       {"text": "13:00", "callback_data": callback + "13"},
                       {"text": "14:00", "callback_data": callback + "14"},
                       {"text": "15:00", "callback_data": callback + "15"}],
                      [{"text": "16:00", "callback_data": callback + "16"},
                       {"text": "17:00", "callback_data": callback + "17"},
                       {"text": "18:00", "callback_data": callback + "18"},
                       {"text": "19:00", "callback_data": callback + "19"}],
                      [{"text": "20:00", "callback_data": callback + "20"},
                       {"text": "21:00", "callback_data": callback + "21"},
                       {"text": "22:00", "callback_data": callback + "22"},
                       {"text": "23:00", "callback_data": callback + "23"}],
                      [{"text": "Cancel", "callback_data": "cancel:cancel"}]]}}
    requests.post(url, json=answer)


def send_message_ask_timezone_delta(chat_id, prefix):
    url = URL + "sendMessage"
    msg = "<b>Select your time zone.\n Or send me your current time in 24 hour format (something like this:  18:35)</b>"
    callback = "tz_delta:" + prefix + ":"
    answer = {"chat_id": chat_id,
              "text": msg,
              "reply_markup": {
                  "inline_keyboard": [[
                      {"text": "EDT", "callback_data": callback + "-4"},
                      {"text": "CDT", "callback_data": callback + "-5"},
                      {"text": "MDT", "callback_data": callback + "-6"},
                      {"text": "PDT", "callback_data": callback + "-7"}],

                      [{"text": "Cancel", "callback_data": "cancel:cancel"}]]},
              "parse_mode": "html"}

    tz_delta_enter_listener[chat_id] = {"is_waiting": True, "user_time": -1, "dif": 0}
    requests.post(url, json=answer)


def send_message_ask_hour_interval(chat_id, prefix):
    url = URL + "sendMessage"
    msg = "Select the time interval to be  informed"
    callback = "sched_hour_interval:" + prefix + ":"
    answer = {"chat_id": chat_id,
              "text": msg,
              "reply_markup": {
                  "inline_keyboard": [[
                      {"text": "1 hour", "callback_data": callback + "1"},
                      {"text": "2 hours", "callback_data": callback + "2"},
                      {"text": "3 hours", "callback_data": callback + "3"}],
                      [{"text": "6 hours", "callback_data": callback + "6"},
                       {"text": "9 hours", "callback_data": callback + "9"},
                       {"text": "12 hours", "callback_data": callback + "12"}],
                      [{"text": "Cancel", "callback_data": "cancel:cancel"}]]}}
    requests.post(url, json=answer)


# Standard message handler
def message_handler(data):
    chat_id = data["message"]["chat"]["id"]
    from_user = data["message"]["from"]["first_name"]
    message = data["message"]["text"]

    # FIXME: remove after test
    print(message)

    # Send /start greetings
    if message == "/start":
        send_sticker(chat_id, "detective.webp")
        msg = "Welcome, {}! \nI am CryptoInformer, a bot who wants to help you.\n" \
              "Give me cryptocurrency name or symbol and I will show you its price and 7d history".format(from_user)
        send_message_with_reply_keyboard(chat_id, msg)
        if pghelper.user_exists(chat_id) == False:
            # print("adding user to db..")
            pghelper.add_user(chat_id, from_user)
    # Send coin symbols as inline keyboard
    elif message == "Other currency":
        msg = "Select currency or enter another name or symbol to get info"
        prefix = "price:0"
        send_coins_with_inline_keyboard(chat_id, msg, prefix)

    # Send list of currencies available
    elif message == "Available currencies":
        msg = coins_list()
        send_message(chat_id, msg)

    # Send selected currency price with inline keyboard (by SYMBOL)
    elif message.upper() in SYMBOLS:
        info = show_currency_info(data["message"]["text"].upper(), chat_id)
        price = info[0]
        coin_name = info[1]
        msg = coin_name + ": " + price
        send_price_with_inline_keyboard(chat_id, msg)

    # Send selected currency price with inline keyboard (by COIN NAME)
    elif message.title() in COINS:
        symbol = symbol_by_name(data["message"]["text"].title())
        info = show_currency_info(symbol, chat_id)
        price = info[0]
        coin_name = info[1]
        msg = coin_name + ": " + price
        send_price_with_inline_keyboard(chat_id, msg)

    # Schedule
    elif message == "Schedule":
        scheds = pghelper.get_schedules(chat_id)
        if scheds is not None and len(scheds.all()) >= MAX_SCHED_ALARM:
            print("MAX NUMBER OF SCHEDULES REACHED")
            # Handle the number of existing alarms
            send_message_handle_schedules(chat_id)
        else:
            msg = "Select currency to create schedule and periodically get info"
            prefix = "new_schedule:0"
            send_coins_with_inline_keyboard(chat_id, msg, prefix)


    # Settings
    elif message == "Settings":
        send_message_sched_alarms_settings(chat_id)


    # Alarm
    elif message == "Alarm":
        alarms = pghelper.get_alarms(chat_id)
        if alarms is not None and len(alarms.all()) >= MAX_SCHED_ALARM:
            print("MAX NUMBER OF ALARMS REACHED")
            # Handle the number of existing alarms
            send_message_handle_alarms(chat_id)
        else:
            send_coins_with_inline_keyboard(chat_id, "Select currency to be informed", "alarm_symbol:0")

    # FIXME: remove testing methods
    # region ======== for test ========
    elif message == "/userinfo":
        send_user_info(chat_id)

    elif message == "/schedinfo":
        send_schedule_info(chat_id)

    elif message == "/alarminfo":
        send_alarm_info(chat_id)
    # endregion =======================

    else:
        print("..reading message..")
        if chat_id in tz_delta_enter_listener and tz_delta_enter_listener[chat_id]["is_waiting"] == True:
            print("--> chat_id in tz_delta_enter_listener")
            tz_delta = read_tz_delta_value(message)
            if tz_delta is not None:
                pghelper.set_tz_delta(chat_id, tz_delta)
                tz_delta_enter_listener[chat_id]["is_waiting"] = False
                send_message(chat_id, text="Thank you! Your time zone has been set")
                # update_schedules_with_tz_delta(chat_id, tz_delta)

            return

        if chat_id in alarm_enter_listener and alarm_enter_listener[chat_id]["is_waiting"] == True:
            print("--> chat_id in alarm_enter_listener and alarm_enter_listener[chat_id][is_waiting] == True")
            coin_symbol = alarm_enter_listener[chat_id]["symbol"]
            coin_name = name_by_symbol(coin_symbol)
            alarm = read_alarm_values(message)
            print("..reading alarm numbers..")
            if alarm is not None:
                try:
                    pghelper.add_alarm(chat_id, coin_symbol, coin_name, alarm["min"], alarm["max"])
                    send_message(chat_id, "Thank you. Alarm has been set")
                    alarm_enter_listener[chat_id]["is_waiting"] = False
                    print("alarm has been set")
                except:
                    send_message(chat_id, "Sorry, I could not set alarm. Please try again")
                    alarm_enter_listener[chat_id]["is_waiting"] = False
                    print("error setting alarm")
            else:
                send_message(chat_id, "Sorry, I don't understand. Enter please correct alarm value(s)")
        else:
            send_message(chat_id, "Sorry, I don't understand. Enter please correct currency name or symbol to get info")


# Callback from inline keyboard handler
def inquery_handler(data):
    chat_id = data["callback_query"]["message"]["chat"]["id"]
    message_id = data["callback_query"]["message"]["message_id"]
    text = data["callback_query"]["message"]["text"]
    callback_text = data["callback_query"]["data"]
    callback_list = callback_text.split(":")

    print("inquery callback_text: ", callback_text)
    print("inquery callback list: ", callback_list)

    if len(callback_list) > 0:
        prefix = callback_list[0]
        callback = callback_list[-1]

        if callback == "show_history":
            filename = str(chat_id) + "_plot.png"
            send_photo(chat_id, filename)
            # Remove tmp image file
            try:
                os.remove(filename)
            except:
                print("Error deleting file ", filename)

            filename = str(chat_id) + "_changes.png"
            # Remove tmp image file
            try:
                os.remove(filename)
            except:
                print("Error deleting file ", filename)

            remove_inline_keyboard(chat_id, message_id, text)
        elif callback == "last_changes":
            filename = str(chat_id) + "_changes.png"
            send_photo(chat_id, filename)
            # Remove tmp image file
            try:
                os.remove(filename)
            except:
                print("Error deleting file ", filename)

            filename = str(chat_id) + "_plot.png"
            # Remove tmp image file
            try:
                os.remove(filename)
            except:
                print("Error deleting file ", filename)

            remove_inline_keyboard(chat_id, message_id, text)

        elif callback == "hide" or callback == "cancel":
            remove_inline_keyboard(chat_id, message_id, text)

        # Next and Prev from keyboard with coins
        elif prefix == "next" or prefix == "prev":
            if prefix == "prev":
                indx = int(callback_list[-1])
                if indx > 0:
                    indx -= 1
                pref = callback_list[1] + ":" + str(indx)
            elif prefix == "next":
                indx = int(callback_list[-1])
                if indx < 5:
                    indx += 1
                pref = callback_list[1] + ":" + str(indx)
            on_tap_prev_next_keyboard(chat_id, message_id, text, pref)

        # Send selected coin info
        elif prefix == "price" and callback in SYMBOLS:
            remove_inline_keyboard(chat_id, message_id, text)
            info = show_currency_info(callback, chat_id)
            price = info[0]
            coin_name = info[1]
            msg = coin_name + ": " + price
            send_price_with_inline_keyboard(chat_id, msg)

        # Coin for new schedule selected
        elif prefix == "new_schedule" and callback in SYMBOLS:
            remove_inline_keyboard(chat_id, message_id, text)
            # check if schedule for this coin exists
            exists = pghelper.schedule_exists(chat_id, callback)
            pref = "add_del_schedule:" + callback
            send_message_schedule(chat_id, exists, pref)

        elif prefix == "show_existing_sched":
            remove_inline_keyboard(chat_id, message_id, text)
            show_existing_schedule(chat_id, callback)

        elif prefix == "replace_sched":
            print("replace schedule for ", callback)
            remove_inline_keyboard(chat_id, message_id, text="Writing new scedule for {}".format(callback))
            pghelper.delete_schedule(chat_id, callback)
            pref = "add_del_schedule:" + callback
            send_message_schedule(chat_id, False, pref)

        elif prefix == "add_schedule":
            remove_inline_keyboard(chat_id, message_id, text)
            coin_symbol = callback_list[1]
            if callback == "daily":
                print("add daily schedule. callback_text: ", callback_text)
                pref = callback_list[1] + ":" + callback
                send_message_ask_time(chat_id, pref)
            elif callback == "hourly":
                print("add hourly schedule. callback_text: ", callback_text)
                pref = callback_list[1] + ":" + callback
                send_message_ask_hour_interval(chat_id, pref)
        elif prefix == "del_schedule_max_num":
            remove_inline_keyboard(chat_id, message_id, text)
            coin_symbol = callback_list[-1]
            coin_name = name_by_symbol(coin_symbol)
            print("delete schedule for ", coin_symbol)
            pghelper.delete_schedule(chat_id, coin_symbol)
            send_message(chat_id, "Done! Schedule for {} ({}) has been deleted. Now you can add the new one".format(
                    coin_name, callback))

        elif prefix == "sched_day_time":
            remove_inline_keyboard(chat_id, message_id, text)
            print("select time for daily schedule. callback_text: ", callback_text)
            coin_symbol = callback_list[1]
            coin_name = name_by_symbol(coin_symbol)
            daily_time = int(callback)
            # tz_delta = dbhandler.get_timezone_delta(chat_id)
            # if tz_delta is not None:
            #     daily_time += tz_delta
            pghelper.add_schedule(chat_id, isDaily=1, coinSymbol=coin_symbol,
                                      coinName=coin_name, timeDaily=daily_time,
                                      hourlyInterval=0)
            send_message(chat_id,
                             "Done! You will receive {} ({}) price daily at {}:00".format(coin_name, coin_symbol,
                                                                                          daily_time))
            pref = callback_list[1] + ":" + callback_list[2] + ":" + callback
            if pghelper.timezone_delta_exists(chat_id) == False:
                tz_delta_enter_listener[chat_id] = {"is_waiting": True, "user_time": -1, "dif": 0}
                send_message_ask_timezone_delta(chat_id, pref)

        elif prefix == "tz_delta":
            remove_inline_keyboard(chat_id, message_id, text)
            print("timezine selected. callback_text: ", callback_text)
            tz_delta = int(callback)
            pghelper.set_tz_delta(chat_id, tz_delta)
            if tz_delta_enter_listener[chat_id] is not None:
                tz_delta_enter_listener[chat_id]["is_waiting"] = False

        elif prefix == "sched_hour_interval":
            remove_inline_keyboard(chat_id, message_id, text)
            print("sched_hour_interval. callback_text: ", callback_text)
            coin_symbol = callback_list[1]
            coin_name = name_by_symbol(coin_symbol)
            hour_interval = int(callback)
            pghelper.add_schedule(chat_id, isDaily=0, coinSymbol=coin_symbol,
                                      coinName=coin_name, timeDaily=0,
                                      hourlyInterval=hour_interval)
            str_hours = "{} hours".format(hour_interval)
            if hour_interval == 1:
                str_hours = "hour"
            send_message(chat_id,
                             "Done! You will receive {} ({}) price info every {}".format(coin_name, coin_symbol,
                                                                                         str_hours))

        # Coin for alarm selected
        elif prefix == "alarm_symbol" and callback in SYMBOLS:
            remove_inline_keyboard(chat_id, message_id, text)
            coin_symbol = callback
            coin_name = name_by_symbol(coin_symbol)

            existing_alarm = pghelper.get_alarm_for_coin(chat_id, coin_symbol)
            if existing_alarm is not None:
                if chat_id in alarm_enter_listener:
                    alarm_enter_listener[chat_id]["is_waiting"] = False
                # print(existing_alarm["coin_symbol"],": ", existing_alarm["min_value"], " <-> ", existing_alarm["max_value"])
                msg = "<b><u>You already have alarm for {} ({})</u>:\nYou will be informed when {} price will be: \n - under the {} usd\n - over the {} usd</b>\n\n" \
                      "Do you want to remove it?".format(existing_alarm.coin_name, existing_alarm["coin_symbol"],
                                                         existing_alarm.coin_name,
                                                         existing_alarm.min_value, existing_alarm["max_value"])
                send_message_replace_alarm(chat_id, coin_symbol, msg)
            else:
                alarm_enter_listener[chat_id] = {"is_waiting": True, "min": 0, "max": 0, "symbol": coin_symbol}
                msg = " <b>Send me the <u>min</u> and <u>max</u> price which you want to be informed when {} ({}) will  grow up or fall down and reach the values.</b> \n" \
                      "Enter just two numbers separated by comma or whitespace (something like this\"120, 130.50\")".format(
                    coin_name, coin_symbol)
                send_message(chat_id, msg)
        elif prefix == "replace_alarm_max_num":
            remove_inline_keyboard(chat_id, message_id, text)
            pghelper.delete_alarm(chat_id, callback)
            coin_name = name_by_symbol(callback)
            # alarm_enter_listener[chat_id] = {"is_waiting": True, "min": 0, "max": 0, "symbol": callback}
            # msg = "Send me the min and max price which you want to be informed when {} ({}) will  grow up or fall down and reach the values. \n" \
            #       "Enter just two numbers separated by comma or whitespace (something like this\"120, 130.50\")".format(
            #     coin_name, callback)
            msg = "Done! Alarm for {} ({}) has been deleted. Now you can add the new one".format(coin_name,
                                                                                                     callback)
            send_message(chat_id, msg)

        elif prefix == "del_schedule":
            pghelper.delete_schedule(chat_id, callback)
            coin_name = name_by_symbol(callback)
            updaet_message_sched_alarms_settings(chat_id, message_id)
            msg = "Done! Schedule for {} ({}) has been deleted".format(coin_name, callback)
            send_message(chat_id, msg)

        elif prefix == "del_alarm":
            # remove_inline_keyboard(chat_id, message_id, text)
            pghelper.delete_alarm(chat_id, callback)
            updaet_message_sched_alarms_settings(chat_id, message_id)
            coin_name = name_by_symbol(callback)
            msg = "Done! Alarm for {} ({}) has been deleted".format(coin_name, callback)
            send_message(chat_id, msg)


def show_existing_schedule(chat_id, coin_symbol):
    schedules = pghelper.get_schedule_for_coin(chat_id, coin_symbol);
    if schedules is not None:
        schedule = schedules
        coin_name = schedule.coin_name
        coin_symbol = schedule.coin_symbol
        is_daily = schedule.is_daily
        time_daily = schedule.time_daily
        hourly_interval = schedule.hourly_interval
        msg = "<b><u>Schedule for {}:</u></b>\n<b>You will be informed about {} ({}) price ".format(coin_name,
                                                                                                    coin_name,
                                                                                                    coin_symbol)

        if is_daily > 0:
            msg += "daily at {}:00</b>".format(time_daily)
        else:
            if hourly_interval == 1:
                msg += "every hour</b>"
            else:
                msg += "every {} hours</b>".format(hourly_interval)
    else:
        msg = "<b>No schedule for {} ({}) found</b>".format(name_by_symbol(coin_symbol), coin_symbol)

    url = URL + "sendMessage"
    answer = {"chat_id": chat_id,
              "text": msg,
              "parse_mode": "html"}
    requests.post(url, json=answer)


# Handle Schedules and Alarms
def send_message_handle_schedules(chat_id):
    schedules = pghelper.get_schedules(chat_id)
    if schedules is not None:
        inline_keyboard = []
        num_sched = len(schedules)
        msg = "You can't have more than {} schedules".format(MAX_SCHED_ALARM)
        for schedule in schedules:
            coin_symbol = schedule.coin_symbol
            is_daily = schedule.is_daily
            time_daily = schedule.time_daily
            hourly_interval = schedule.hourly_interval
            if is_daily > 0:
                but = [{
                    "text": "Delete: {} every day at {}:00".format(coin_symbol, time_daily),
                    "callback_data": "del_schedule_max_num:{}".format(coin_symbol)}]
            else:
                hour_str = "hour"
                if hourly_interval > 1: hour_str += "s"
                but = [{
                    "text": "Delete: {} every {} {}".format(coin_symbol, hourly_interval, hour_str),
                    "callback_data": "del_schedule_max_num:{}".format(coin_symbol)}]
            inline_keyboard.append(but)
        inline_keyboard.append([{"text": "Cancel", "callback_data": "cancel:cancel"}])
        url = URL + "sendMessage"
        answer = {"chat_id": chat_id,
                  "text": msg,
                  "reply_markup": {
                      "inline_keyboard": inline_keyboard}}
        requests.post(url, json=answer)


def send_message_handle_alarms(chat_id):
    alarms = pghelper.get_alarms(chat_id)
    if alarms is not None:
        inline_keyboard = []
        msg = "You can't have more than {} alarms".format(MAX_SCHED_ALARM)
        for alarm in alarms:
            coin_symbol = alarm.coin_symbol
            coin_name = name_by_symbol(coin_symbol)
            but = [{
                "text": "Delete: Alarm for {} ({})".format(coin_name, coin_symbol),
                "callback_data": "replace_alarm_max_num:{}".format(coin_symbol)}]
            inline_keyboard.append(but)
        inline_keyboard.append([{"text": "Cancel", "callback_data": "cancel:cancel"}])
        url = URL + "sendMessage"
        answer = {"chat_id": chat_id,
                  "text": msg,
                  "reply_markup": {
                      "inline_keyboard": inline_keyboard}}
        requests.post(url, json=answer)


def send_message_sched_alarms_settings(chat_id):
    # Sending message
    url = URL + "sendMessage"
    msg = message_text_sched_alarm_settings(chat_id)
    inline_keyboard = inline_keyboard_for_schedules_alarms(chat_id)
    answer = {"chat_id": chat_id,
              "text": msg,
              "reply_markup": {
                  "inline_keyboard": inline_keyboard},
              "parse_mode": "html"
              }

    # print(answer)
    requests.post(url, json=answer)


def updaet_message_sched_alarms_settings(chat_id, message_id):
    url = URL + "editMessageText"
    msg = message_text_sched_alarm_settings(chat_id)
    inline_keyboard = inline_keyboard_for_schedules_alarms(chat_id)
    answer = {"chat_id": chat_id,
              "message_id": message_id,
              "text": msg,
              "parse_mode": "html",
              "reply_markup": {
                  "inline_keyboard": inline_keyboard}
              }
    requests.post(url, json=answer)


def message_text_sched_alarm_settings(chat_id):
    msg = ""
    # Schedule
    schedules = pghelper.get_schedules(chat_id)
    if schedules is not None:
        msg = "<b><u>Schedules:</u></b>\n<b>You will be informed about:</b>\n"
        for schedule in schedules:
            coin_name = schedule.coin_name
            coin_symbol = schedule.coin_symbol
            is_daily = schedule.is_daily
            time_daily = schedule.time_daily
            hourly_interval = schedule.hourly_interval
            if is_daily > 0:
                msg += " - {} ({}) price daily at {}:00\n".format(coin_name, coin_symbol, time_daily)
            else:
                if hourly_interval == 1:
                    msg += " - {} ({}) price every hour\n".format(coin_name, coin_symbol)
                else:
                    msg += " - {} ({}) price every {} hours\n".format(coin_name, coin_symbol, hourly_interval)
        msg += "\n"
    else:
        msg = "<b><u>Schedules:</u></b>\n - You don't have any schedule for any currency yet\n"

    # Alarm
    alarms = pghelper.get_alarms(chat_id)
    if alarms is not None:
        msg += "<b><u>Alarms:</u></b>\n<b>You will be informed if crypto currency price will be:</b>\n"
        for alarm in alarms:
            coin_name = alarm.coin_name
            coin_symbol = alarm.coin_symbol
            min_value = alarm.min_value
            max_value = alarm.max_value
            if min_value > 0 and max_value > 0:
                msg += " - {}: <u>under</u> {} or <u>over</u> {} usd\n".format(coin_symbol, min_value, max_value)
            elif min_value > 0:
                msg += " - {}: <u>under</u> {} usd\n".format(coin_symbol, min_value)
            elif max_value > 0:
                msg += " - {}: <u>over</u> {} usd\n".format(coin_symbol, max_value)
    else:
        msg += "<b><u>Alarms:</u></b>\n - You don't have any alarm for any currency yet\n"
    return msg


def inline_keyboard_for_schedules_alarms(chat_id):
    inline_keyboard = []
    sched_buttons = []
    schedules = pghelper.get_schedules(chat_id)
    if schedules is not None:
        for schedule in schedules:
            coin_symbol = schedule.coin_symbol
            but = [{"text": "Delete: Schedule for {}".format(coin_symbol),
                    "callback_data": "del_schedule:{}".format(coin_symbol)}]
            inline_keyboard.append(but)

    alarm_buttons = []
    alarms = pghelper.get_alarms(chat_id)
    if alarms is not None:
        for alarm in alarms:
            coin_symbol = alarm.coin_symbol
            but = [{"text": "Delete: Alarm for {}".format(coin_symbol),
                    "callback_data": "del_alarm:{}".format(coin_symbol)}]
            inline_keyboard.append(but)

    if len(inline_keyboard) > 0:
        inline_keyboard.append([{"text": "Cancel", "callback_data": "cancel:cancel"}])

    return inline_keyboard


# region Support methods
def coins_list():
    # Create message with list of coins
    message = ""
    for indx, row in df.iterrows():
        message = message + row["name"] + " - " + row["symbol"] + "\n"
    return message


def show_currency_info(symbol, chat_id):
    row = df[(df["symbol"] == symbol)]
    coin_id = row["id"].values[0]
    coin_name = row["name"].values[0]
    dataloader.load_history(coin_id, coin_name, chat_id)
    price = dataloader.load_coin(coin_id, chat_id, coin_name)
    return price, coin_name


def name_by_symbol(symbol):
    row = df[(df["symbol"] == symbol)]
    coin_name = row["name"].values[0]
    return coin_name


def symbol_by_name(name):
    row = df[(df["name"] == name)]
    coin_symbol = row["symbol"].values[0]
    return coin_symbol


def read_alarm_values(text):
    min = 0
    max = 0
    alarm = {"min": 0, "max": 0}
    values = re.findall("\d*\.*\d+", text)
    if len(values) == 1:
        if "min" in text:
            alarm["min"] = values[0]
        elif "max" in text:
            alarm["max"] = values[0]
        elif "<" in text:
            alarm["min"] = values[0]
        elif ">" in text:
            alarm["max"] = values[0]
        else:
            return None
    elif len(values) == 2:
        if values[0] < values[1]:
            alarm["min"] = values[0]
            alarm["max"] = values[1]
        else:
            alarm["min"] = values[1]
            alarm["max"] = values[0]

    else:
        return None

    return alarm


def read_tz_delta_value(text):
    # FIXME: set correctdelta
    delta = 0
    values = re.findall("\d+", text)
    now_hour = datetime.datetime.now().hour
    if len(values) > 0:
        user_hour = int(values[0])
        delta = (user_hour - now_hour)%24
        if delta < 12:
            return delta
        else:
            delta = -((now_hour - user_hour)%24)
            return delta
    else:
        return None

# endregion


# region "GET" and "POST" request handlers for Flask
@app.route("/", methods=["GET", "HEAD"])
def index():
    r = requests.get('http://httpbin.org/status/418')
    return "<h1>Hello from Crypto!</h1><br/><h1><pre>" + r.text + "</pre></h1>"


@app.route("/", methods=["POST"])
def home():
    if flask.request.method == "POST":
        resp = flask.request.get_json()
        # standard message from user
        if "message" in resp:
            message_handler(resp)

        # callback from inline keyboard
        elif "callback_query" in resp:
            inquery_handler(resp)

        return ''
    else:
        flask.abort(403)

# endregion


# region BackgroundScheduler methods

def min_to_nearest_hour():
    mins = 59 - datetime.datetime.now().minute
    secs = 60 - datetime.datetime.now().second
    return [mins, secs]


# Schedule and alarm functions
def check_for_scheduler(user):
    chat_id = user.chat_id
    current_date = datetime.datetime.now()
    current_hour = current_date.hour
    tz_delta = user.tz_delta
    scheduled_message = "<b>Scheduled info:</b>\n"

    schedules = pghelper.get_schedules(chat_id)
    if schedules is not None:
        for schedule in schedules:
            coin_symbol = schedule.coin_symbol
            coin_name = schedule.coin_name
            if schedule.is_daily > 0:
                time_daily = schedule.time_daily
                if (current_hour + tz_delta) % 24 == time_daily:
                    if coin_symbol in currently_checked_price_for_sched:
                        info = currently_checked_price_for_sched[coin_symbol]
                    else:
                        info = get_sched_coin_info(coin_symbol)
                        currently_checked_price_for_sched[coin_symbol] = info
                    scheduled_message += " - {} ({}) price: <b>{}</b>\n".format(coin_name, coin_symbol, info[0])
            else:
                last_send = schedule["last_send"]
                hourly_interval = schedule["hourly_interval"]
                if (current_hour - last_send) % 24 >= hourly_interval:
                    if coin_symbol in currently_checked_price_for_sched:
                        info = currently_checked_price_for_sched[coin_symbol]
                    else:
                        info = get_sched_coin_info(coin_symbol)
                        currently_checked_price_for_sched[coin_symbol] = info
                    scheduled_message += " - {} ({}) price: <b>{}</b>\n".format(coin_name, coin_symbol, info[0])
                    # update last_send value in database
                    last_send_ts = math.floor(current_date.timestamp())
                    pghelper.set_scheduled_last_send(chat_id, coin_symbol, last_send_ts)

        scheduled_send_price(chat_id, scheduled_message)


def check_for_alarm(user):
    chat_id = user.chat_id
    alarm_message = "<b>Alarm info:</b>\n"
    alarms = pghelper.get_alarms(chat_id)
    not_empty = False
    if alarms is not None:
        for alarm in alarms:
            coin_symbol = alarm.coin_symbol
            coin_name = alarm.coin_name
            min_value = alarm.min_value
            max_value = alarm.max_value
            if coin_symbol in currently_checked_price_for_alarm:
                info = currently_checked_price_for_alarm[coin_symbol]
            else:
                info = get_sched_coin_info(coin_symbol)
                currently_checked_price_for_alarm[coin_symbol] = info
            if min_value > 0 and info[0] < min_value:
                alarm_message += " - {} ({}) price: <b>{}</b>\n".format(coin_name, coin_symbol, info[0])
                min_value = 0
                not_empty = True
            elif max_value > 0 and info[0] > max_value:
                alarm_message += " - {} ({}) price: <b>{}</b>\n".format(coin_name, coin_symbol, info[0])
                max_value = 0
                not_empty = True

            if min_value == 0 and max_value == 0:
                pghelper.delete_alarm(chat_id, coin_symbol)
            elif min_value == 0:
                pghelper.reset_alarm_min_max(chat_id, coin_symbol, for_max=False)
            elif max_value == 0:
                pghelper.reset_alarm_min_max(chat_id, coin_symbol, for_max=True)

        if not_empty:
            scheduled_send_price(chat_id, alarm_message)
            print("alarm message is not empty")
        else:
            print("alarm message is empty")


def get_sched_coin_info(coin_symbol):
    row = df[(df["symbol"] == coin_symbol)]
    coin_id = row["id"].values[0]
    coin_name = row["name"].values[0]
    price = dataloader.load_coin_for_schedule(coin_id)
    return price, coin_name


# SCHEDULER TIMER
def scheduled_send_price(chat_id, text=""):
    url = URL + "sendMessage"
    # answer with InlineKeyboard
    answer = {"chat_id": chat_id,
              "text": text,
              "parse_mode": "html"}
    requests.post(url, json=answer)


def on_timer_schedule():
    currently_checked_price_for_sched.clear()
    users = pghelper.get_all_users()
    if users is None:
        return
    for user in users:
        check_for_scheduler(user)


def on_timer_alarm():
    currently_checked_price_for_alarm.clear()
    users = pghelper.get_all_users()
    if users is None:
        return
    for user in users:
        check_for_alarm(user)


# endregion

# Initialize application
def main():
    mins = min_to_nearest_hour()[0]
    secs = min_to_nearest_hour()[1]

    time_now = datetime.datetime.now()
    time_delta = datetime.timedelta(minutes=mins, seconds=secs)
    time_start = time_now + time_delta

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(on_timer_schedule, 'interval', hours=1, start_date=time_start)
    scheduler.start()

    ALARM_SCHEDULER = bACKGROUNDsCHEDULER(DAEMON=tRUE)
    ALARM_SCHEDULER.ADD_JOB(ON_TIMER_ALARM, "INTERVAL", MINUTES=1)
    ALARM_SCHEDULER.START()

    # Shut down the schedulers when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    atexit.register(lambda: alarm_scheduler.shutdown())


if __name__ == '__main__':
    # main()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
