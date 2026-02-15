import requests
from django.conf import settings


def _push_line_message(payload):
    if not settings.LINE_OA_CHANNEL_ACCESS_TOKEN:
        raise RuntimeError('LINE OA access token is not configured.')

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


def send_line_text_message(line_user_id, text):
    payload = {
        'to': line_user_id,
        'messages': [
            {
                'type': 'text',
                'text': text,
            }
        ],
    }
    return _push_line_message(payload)


def send_line_flex_message(line_user_id, alt_text, bubble):
    payload = {
        'to': line_user_id,
        'messages': [
            {
                'type': 'flex',
                'altText': alt_text,
                'contents': bubble,
            }
        ],
    }
    return _push_line_message(payload)
