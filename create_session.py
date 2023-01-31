from telethon.sync import TelegramClient
import sys
phone = sys.argv[1]
api_id = int(sys.argv[2])
api_hash = sys.argv[3]

with TelegramClient(phone, api_id, api_hash) as client:
    client.send_message('me', "A Session was created successfully!")
