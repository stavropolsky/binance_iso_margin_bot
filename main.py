from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
from config import api_key, api_secret, quantity, price_buy, price_sell, stop_buy, stop_sell, symbol, channel, token
import requests
from binance import ThreadedWebsocketManager
import logging
import time
import threading

# Инициализация клиента
client = Client(api_key, api_secret)

# Лог файл, создается автоматически в той же директории где лежит файл скрипта
logging.basicConfig(filename='script_logs.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Счётчик ордеров
counter_orders = 0
# Количество попыток выставить ордер в случае недостаточного баланса
max_retries = 3


# Telegram
def send_messages(order, type_order, counter):
    if type_order == "Error":
        res = requests.get('https://api.telegram.org/bot{}/sendMessage'.format(token),
                           params=dict(chat_id=channel, text=f'Ошибка при выставлении ордера, {order}'))

        if res.status_code != 200:
            raise ValueError("Failed to send message")

    elif type_order == 'BUY':
        res = requests.get('https://api.telegram.org/bot{}/sendMessage'.format(token),
                           params=dict(chat_id=channel, text=f'Выставлен лимитный ордер на покупку {counter},'
                                                             f' Order ID: {order["orderId"]}'))
        if res.status_code != 200:
            raise ValueError("Failed to send message")

    elif type_order == 'SELL':
        res = requests.get('https://api.telegram.org/bot{}/sendMessage'.format(token),
                           params=dict(chat_id=channel, text=f'Выставлен лимитный ордер на продажу {counter},'
                                                             f' Order ID: {order["orderId"]}'))
        if res.status_code != 200:
            raise ValueError("Failed to send message")

    elif type_order == 'BUY_MARKET':
        res = requests.get('https://api.telegram.org/bot{}/sendMessage'.format(token),
                           params=dict(chat_id=channel, text=f'Выставлен рыночный ордер на покупку {counter},'
                                                             f' Order ID: {order["orderId"]}'))
        if res.status_code != 200:
            raise ValueError("Failed to send message")

    elif type_order == 'SELL_MARKET':
        res = requests.get('https://api.telegram.org/bot{}/sendMessage'.format(token),
                           params=dict(chat_id=channel, text=f'Выставлен рыночный ордер на продажу {counter},'
                                                             f' Order ID: {order["orderId"]}'))
        if res.status_code != 200:
            raise ValueError("Failed to send message")

    elif type_order == 'e':
        res = requests.get('https://api.telegram.org/bot{}/sendMessage'.format(token),
                           params=dict(chat_id=channel, text=f'Ошибка подключения к сокету, {order}'))

        if res.status_code != 200:
            raise ValueError("Failed to send message")


# def check_balance():
#     # Получение информации о свойствах торговой пары
#     symbol_info = client.get_symbol_info(symbol)
#
#     # Определение используемой валюты
#     base_asset = symbol_info['baseAsset']
#     quote_asset = symbol_info['quoteAsset']
#
#     # Получение текущего баланса базовой валюты
#     base_asset_balance = client.get_asset_balance(asset=base_asset)
#     base_balance = float(base_asset_balance)
#
#     # Получение текущего баланса котируемой валюты
#     quote_asset_balance = client.get_asset_balance(asset=quote_asset)
#     quote_balance = float(quote_asset_balance)
#     # Определение текущей цены тикера
#     ticker = client.get_ticker(symbol=symbol)
#     price = float(ticker['lastPrice'])


# Размещение ордера на покупку по рынку
def place_order_buy_market():
    global counter_orders
    try:
        order = client.create_margin_order(
            isIsolated=True,
            symbol=symbol,
            type=ORDER_TYPE_MARKET,
            side=SIDE_BUY,
            quantity=quantity)
        counter_orders += 1
        send_messages(order, 'BUY_MARKET', counter_orders)
        logging.info(order)
        print(order)
        print('Размещение рыночного ордера на покупку')
    except Exception as e:
        send_messages(e, "Error", counter_orders)
        logging.error(e)


# Размещение ордера на продажу по рынку
def place_order_sell_market():
    global counter_orders
    try:
        order = client.create_margin_order(
            isIsolated=True,
            symbol=symbol,
            type=ORDER_TYPE_MARKET,
            side=SIDE_SELL,
            quantity=quantity)
        counter_orders += 1
        send_messages(order, 'SELL_MARKET', counter_orders)
        logging.info(order)
        print(order)
        print('Размещение рыночного ордера на продажу')
    except Exception as e:
        send_messages(e, "Error", counter_orders)
        logging.error(e)


# Размещение лимитного ордера на покупку
def place_order_buy():
    retries = 0
    global counter_orders
    while retries < max_retries:
        try:
            order_type = ORDER_TYPE_STOP_LOSS_LIMIT
            order = client.create_margin_order(
                isIsolated=True,
                symbol=symbol,
                stopPrice=stop_buy,
                price=price_buy,
                type=order_type,
                timeInForce=TIME_IN_FORCE_GTC,
                side=SIDE_BUY,
                quantity=quantity)
            counter_orders += 1
            send_messages(order, 'BUY', counter_orders)
            logging.info(order)
            print(order)

        except Exception as e:
            if isinstance(e, BinanceAPIException) and e.code == -2010 and 'insufficient balance' in e.message:
                retries += 1
                logging.error(e)
                print('Недостаточно баланса')
                send_messages(e, "Error", counter_orders)
                time.sleep(3)

            else:
                place_order_buy_market()
                send_messages(e, "Error", counter_orders)
                logging.error(e)
                break


# Размещение лимитного ордера на продажу
def place_order_sell():
    retries = 0
    global counter_orders

    while retries < max_retries:
        try:
            order_type = ORDER_TYPE_STOP_LOSS_LIMIT
            order = client.create_margin_order(
                isIsolated=True,
                symbol=symbol,
                stopPrice=stop_sell,
                price=price_sell,
                type=order_type,
                timeInForce=TIME_IN_FORCE_GTC,
                side=SIDE_SELL,
                quantity=quantity)
            counter_orders += 1
            send_messages(order, 'SELL', counter_orders)
            logging.info(order)
            print(order)
            break

        except Exception as e:
            if isinstance(e, BinanceAPIException) and e.code == -2010 and 'insufficient balance' in e.message:
                retries += 1
                logging.error(e)
                print('Недостаточно баланса')
                send_messages(e, "Error", counter_orders)
                time.sleep(3)

            else:
                place_order_sell_market()
                send_messages(e, "Error", counter_orders)
                logging.error(e)
                break


# Основной код программы
def main():
    # Проверяем есть ли открытые ордера, если есть то выводим их на экран
    open_orders = client.get_open_margin_orders(symbol=symbol, isIsolated='TRUE')
    print(open_orders)

    # Если открытых ордеров нет, то выставляем ордер на покупку
    if len(open_orders) == 0:
        print('Размещение лимитного ордера на покупку')
        place_order_buy()

    # Иницииализация сокета
    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    twm.start()

    # Функция для обработки событий с биржи
    def handle_socket_message(message):

        # Если проихсодит какое-то событие на бирже и оно относится к исполнению ордеров,
        # то выводим эти сообщения на экран
        if 'e' in message and message['e'] == 'executionReport':
            logging.info(message)

            # Если ордер на покупку исполнен, то размещаем ордер на продажу
            if message['X'] == 'FILLED' and message['S'] == 'BUY':
                place_order_sell()
                print("Размещение лимитного ордера на продажу")

            # Иначе, если ордер на продажу исполнен, то размещаем ордер на покупку
            elif message['X'] == 'FILLED' and message['S'] == 'SELL':
                place_order_buy()
                print("Размещение лимитного ордера на покупку")

        elif message['e'] == 'error':
            print('error')
            logging.error(message)
            send_messages(message, "Error", counter_orders)
            twm.stop()
            twm.start()

    twm.start_isolated_margin_socket(callback=handle_socket_message, symbol=symbol)
    twm.join()


# Периодическая отправка сообщений в телеграмм, для проверки состояния работы скрипта
def send_status_message():
    while True:
        time.sleep(5)
        open_orders = client.get_open_margin_orders(symbol=symbol, isIsolated='TRUE')
        num_open_orders = len(open_orders)
        order_id_list = []
        for orders in range(num_open_orders):
            order_id_list.append(open_orders[orders]['orderId'])
        order_id_ = ", ".join(map(str, order_id_list))

        if num_open_orders > 0:
            message = f"Скрипт запущен, количество открытых ордеров - {num_open_orders}" \
                      f"\nOrder ID: {order_id_}"
            res = requests.get('https://api.telegram.org/bot{}/sendMessage'.format(token),
                               params=dict(chat_id=channel, text=message))
            if res.status_code != 200:
                raise ValueError("Failed to send message")

        else:
            message = f"Скрипт запущен, но количество открытых ордеров - {num_open_orders}\n" \
                      f"Если с момента исполнения последнего ордера прошло относительно много времени, " \
                      f"рекомендуется проверить лог файлы на наличие ошибок и перезапустить скрипт"
            res = requests.get('https://api.telegram.org/bot{}/sendMessage'.format(token),
                               params=dict(chat_id=channel, text=message))
            if res.status_code != 200:
                raise ValueError("Failed to send message")

        time.sleep(300)


thread = threading.Thread(target=send_status_message)
thread.start()

if __name__ == "__main__":
    main()
