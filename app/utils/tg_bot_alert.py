import requests
import time
from typing import List, Dict, Optional, Union

from app.config import get_settings


settings = get_settings()


class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.timeout = 10

    def _make_request(self, method: str, params: dict = None) -> Optional[Dict]:
        """
        Внутренний метод для выполнения запросов к API

        Args:
            method: метод API (sendMessage, getUpdates и т.д.)
            params: параметры запроса

        Returns:
            ответ от API или None в случае ошибки
        """
        url = f"{self.base_url}/{method}"

        try:
            response = requests.post(
                url,
                json=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            if data.get('ok'):
                return data.get('result')
            else:
                print(f"Ошибка API: {data.get('description')}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса: {e}")
            return None

    def get_chat_ids(self, limit: int = 100) -> List[Dict]:
        """
        Получение списка всех chat_id, которые писали боту

        Args:
            limit: максимальное количество обновлений для получения

        Returns:
            список словарей с информацией о чатах
        """
        params = {
            'limit': limit,
            'timeout': 0
        }

        updates = self._make_request('getUpdates', params)

        if not updates:
            print("Нет новых сообщений. Напишите что-нибудь боту и попробуйте снова.")
            return []

        # Собираем уникальные чаты
        chats = {}
        for update in updates:
            if 'message' in update:
                chat = update['message']['chat']
                chat_id = chat['id']

                # Сохраняем только уникальные чаты с последней информацией
                chats[chat_id] = {
                    'chat_id': chat_id,
                    'type': chat.get('type'),
                    'title': chat.get('title'),
                    'first_name': chat.get('first_name'),
                    'last_name': chat.get('last_name'),
                    'username': chat.get('username'),
                    'last_message': update['message'].get('text'),
                    'last_message_time': update['message'].get('date')
                }

        result = list(chats.values())

        return result

    def send_message(
            self,
            chat_id: Union[int, str],
            text: str,
            disable_notification: bool = False,
    ) -> Optional[Dict]:
        """
        Отправка сообщения в чат

        Args:
            chat_id: ID чата получателя
            text: текст сообщения
            disable_notification: отключить уведомление

        Returns:
            информация об отправленном сообщении или None
        """
        params = {
            'chat_id': chat_id,
            'text': text,
            'disable_notification': disable_notification
        }

        result = self._make_request('sendMessage', params)

        if result:
            print(f"✓ Сообщение отправлено в чат {chat_id}")
        else:
            print(f"✗ Ошибка отправки в чат {chat_id}")

        return result



# Использование
notifier = TelegramBot(settings.TG_TOKEN)
print(notifier.get_chat_ids())
notifier.send_message(925869845, "hueta")
