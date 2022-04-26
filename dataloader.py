import requests, json
import pandas as pd
import matplotlib.pyplot as plt
import math
import statistics

url_coins = "https://coinranking1.p.rapidapi.com/coin/"
headers_coins = {
    'x-rapidapi-key': "<< your key here >>",
    'x-rapidapi-host': "coinranking1.p.rapidapi.com"
}

url_history_base = "https://coinranking1.p.rapidapi.com/coin/"
url_history_last = "/history/7d"
headers_history = {
    'x-rapidapi-host': "coinranking1.p.rapidapi.com",
    'x-rapidapi-key': "<< your key here >>"
}

# history = dict()
# timestamps = []
# coins = dict()
# current_coin = dict()


def load_coin(coin_id, chat_id, coin_name):
    url = url_coins + str(coin_id)
    response = requests.request("GET", url, headers=headers_coins)
    data = json.loads(response.text)
    coin = data["data"]["coin"]
    price = str(round(float(coin["price"]), 2)) + " usd"
    changes = data["data"]["coin"]["history"]
    create_plot_for_changes(changes, coin_name, chat_id)
    print(coin["name"], " price: ", price)
    return price


def load_coin_for_schedule(coin_id):
    url = url_coins + str(coin_id)
    response = requests.request("GET", url, headers=headers_coins)
    data = json.loads(response.text)
    coin = data["data"]["coin"]
    price = round(float(coin["price"]), 2)
    print(coin["name"], " price: ", price)

    return price


def load_history(coin_id, coin_name, chat_id):
    url = url_history_base + str(coin_id) + url_history_last
    response = requests.request("GET", url, headers=headers_history)
    data = json.loads(response.text)
    history = data["data"]["history"]
    create_plot(history, coin_name, chat_id)


def create_plot(data, coin_name, chat_id, fname="_plot.png"):
    df = pd.DataFrame(data)
    x = df["timestamp"].astype(str).str[:-3].astype(int)
    y = pd.to_numeric(df["price"])
    y_list = y.tolist()
    plt.style.use('seaborn-darkgrid')
    # ax = plt.axes()
    plt.figure()
    ax = plt.subplot()

    # ax.yaxis.set_major_locator(plt.NullLocator())
    ax.xaxis.set_major_formatter(plt.NullFormatter())

    plt.title(coin_name)
    plt.xlabel("Last 7 days")
    plt.ylabel("Price, usd")

    m = statistics.mean(y_list)
    if y_list[-1] > y_list[0] and y_list[-1] > m:
        color = "green"
    else:
        color = "red"

    plt.plot(x, y, color=color)
    # plt.plot(x, y)
    filename = str(chat_id)+fname
    plt.savefig(filename)
    # plt.show()


def create_plot_for_changes(data, coin_name, chat_id, fname="_changes.png"):
    # df = pd.DataFrame(data)
    x = range(0,len(data))
    y_data = data # pd.to_numeric(df["price"])
    y = []
    for indx, item in enumerate(data):
        value = float(item)
        y.append(value)
    # print("Y:\n", y, "\n")
    plt.style.use('seaborn-darkgrid')
    # ax = plt.axes()
    plt.figure()
    ax = plt.subplot()

    # ax.yaxis.set_major_locator(plt.NullLocator())
    ax.xaxis.set_major_formatter(plt.NullFormatter())

    plt.title(coin_name)
    plt.xlabel("Last day")
    plt.ylabel("Price, usd")

    m = statistics.mean(y)
    if y[-1] > y[0] and y[-1] > m:
        color = "green"
    else:
        color = "red"

    print("Y[0]: {}\nY[-1]: {},\nmean: {}".format(y[0], y[-1], m))
    plt.plot(x, y, color=color)
    filename = str(chat_id) + fname
    plt.savefig(filename)
    plt.show()
