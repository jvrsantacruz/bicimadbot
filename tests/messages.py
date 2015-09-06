import datetime

CHAT_ID = 4128581
UPDATE_ID = 987235637
LOCATION = 40.405742, -3.694103

MSG_LOCATION = {
    "message_id": 21,
    "from": {
        "id": 4128581,
        "first_name": "Javier",
        "last_name": "Santacruz"
    },
    "chat": {
        "id": CHAT_ID,
        "first_name": "Javier",
        "last_name": "Santacruz"
    },
    "date": 1439843938,
    "location": {
        "longitude": -3.694103,
        "latitude": 40.405742
    }
}

CHAT_TEXT = '/bici'
CHAT_MSG_ID = 21
CHAT_MSG_TIMESTAMP = 1439843938
CHAT_MSG_DATE = datetime.datetime.fromtimestamp(CHAT_MSG_TIMESTAMP)
CHAT_MSG_SENDER = {
    "id": 4128581,
    "first_name": "Javier",
    "last_name": "Santacruz"
}
CHAT_MSG_CHAT = {
    "id": 4128581,
    "first_name": "Javier",
    "last_name": "Santacruz"
}
CHAT_MSG_TEXT = "/bici"

MSG_CHAT = {
    "message_id": CHAT_MSG_ID,
    "from": CHAT_MSG_SENDER,
    "chat": CHAT_MSG_CHAT,
    "date": CHAT_MSG_TIMESTAMP,
    "text": CHAT_MSG_TEXT
}

UPDATE_ID = 987235637
UPDATE_CHAT = {
    "update_id": UPDATE_ID,
    "message": MSG_CHAT
}


UPDATE_LOCATION = {
    "update_id": UPDATE_ID,
    "message": MSG_LOCATION
}
