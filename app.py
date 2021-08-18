#!/usr/bin/env python3

import dotenv
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

dotenv.load_dotenv()

# Init app with bot token
app = App(token=os.environ.get('SLACK_BOT_TOKEN'))

# Listen to incoming messages that contain "hello"
# To learn available listener arguments,
# visit https://slack.dev/bolt-python/api-docs/slack_bolt/kawrgs_injection/args.html
@app.message('hello')
def message_hello(message, say):
    # say() sends a message to the channel where the event was triggered.
    say(f"Hey there <@{message['user']}>!")

# Do work.
if __name__ == '__main__':
    SocketModeHandler(app, os.environ['SLACK_APP_TOKEN']).start()
