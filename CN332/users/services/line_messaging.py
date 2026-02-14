import requests
from django.conf import settings


def send_line_text_message(line_user_id, text):
    if not settings.LINE_OA_CHANNEL_ACCESS_TOKEN:
        raise RuntimeError('LINE OA access token is not configured.')

    payload = {
        'to': line_user_id,
        'messages': [
            {
                'type': 'text',
                'text': text,
            }
        ],
    }

    response = requests.post(
        'https://api.line.me/v2/bot/message/push',
        json=payload,
        headers={
            'Authorization': f'Bearer {settings.LINE_OA_CHANNEL_ACCESS_TOKEN}',
            'Content-Type': 'application/json',
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json() if response.content else {}
