import requests
import time
import random
import json
from loguru import logger

logger.add("log.txt", format="{time} {level} {message}", level="ERROR", rotation="50 MB")


class MessageGenerator:
    def __init__(self):
        self.phrases = self._get_phrases()
        self.messages = self.phrases.copy()

    def _get_phrases(self):
        with open('messages.txt', encoding='utf-8') as f:
            phrases = f.read().splitlines()
        return phrases

    def get_random_message(self):
        if len(self.messages) <= 1:
            self.messages = self.phrases.copy()
        random_message = random.randint(0, len(self.messages) - 1)
        return self.messages.pop(random_message)


class Discord:
    def __init__(self, config):
        self.session = requests.Session()
        self.token = config['token']
        self.config = config
        self._get_headers()
        if self.config['enable_proxy'] == 'y' or self.config['enable_proxy'] == 'Y':
            self.proxy = config['proxy']
            self.setup_proxy()

    def _get_headers(self):
        self.session.headers = {
            'authorization': self.token,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',
        }

    def setup_proxy(self):
        if self.config['proxy_type'] == 1:

            proxies = {
                "http": f"http://{self.proxy}",
                "https": f"https://{self.proxy}"
            }
            self.session.proxies = proxies
        elif self.config['proxy_type'] == 2:
            proxies = {"http": f"socks5h://{self.proxy}"}
            self.session.proxies = proxies

    def send_message(self, word):
        url = f'https://discord.com/api/v9/channels/{self.config["channel_id"]}/messages'
        response = self.session.post(url, data=
        {
            'content': word
        }, verify=False)
        return response

    def delete_message(self, message_id):
        url = f'https://discord.com/api/v9/channels/{self.config["channel_id"]}/messages/{message_id}'
        response = self.session.delete(url, verify=False)
        return response


def set_up():
    try:
        file = open('config.json', encoding='utf-8')
    except IOError as e:
        pass
    else:
        use_config = int(input('Найден сохраненый конфиг, использовать данные с прошлого запуска?\n1. Да\n2. Нет\n'))
        if use_config == 1:
            with file:
                config = json.load(file)
            return config

    config = {}
    config['token'] = input('Введите токен пользователя\n')
    config['enable_proxy'] = input('Использовать прокси? Введите y или n\n')
    print(config['enable_proxy'])
    if config['enable_proxy'] == 'y' or config['enable_proxy'] == 'Y':
        config['proxy_type'] = int(input('Выберите тип прокси (1 или 2):\n1. http/https\n2. socks\n'))
        config['proxy'] = input('Введите прокси\n')
    config['channel_id'] = input('Введите ид канала\n')
    config['wait_time'] = float(input('Заддержка между смс\n'))
    config['delete_messages'] = int(input('Удалять смс после отправки?(1 или 2)\n1. Да\n2. Нет\n'))
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f)
    return config


@logger.catch()
def main():
    message = MessageGenerator()
    config = set_up()
    bot = Discord(config)
    while True:
        word = message.get_random_message()
        response = bot.send_message(word)
        if response.status_code != 200:
            logger.warning(f'Ошибка, код ответа: {response.text}')
            if response.json()['code'] == 20028:
                continue
            if response.json()['code'] == 20016:
                time.sleep(response.json()['retry_after'] + 1)
        else:
            logger.success(f'Успешно отправлено: {word}')
            if config['delete_messages'] == 1:
                resp = bot.delete_message(response.json()["id"])
                if resp.status_code == 204:
                    logger.success('Успешно удалено')
        time.sleep(config['wait_time'])


if __name__ == '__main__':
    main()
