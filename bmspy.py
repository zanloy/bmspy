#!/usr/bin/env python3

# StdLib
import argparse
import asyncio
import dotenv
import logging
import os
import sys
from urllib.parse import urljoin, urlparse

# Internal deps
from bmspy import BMSConsumer, SlackBot

# External deps
from pythonjsonlogger import jsonlogger

dotenv.load_dotenv()

# Do work.
if __name__ == '__main__':
    # TODO: Setup argparse for these
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--alert-channel', default=os.environ.get('BMSPY_ALERT_CHANNEL', None), help='Slack channel to send health updates to')
    parser.add_argument('--log-format', choices=['json', 'text'], default='text', help='format for log messages')
    parser.add_argument('-l', '--log-level', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], default='WARNING', help='level to show log messages')
    parser.add_argument('-s', '--source', nargs='+', help='bms url(s) to monitor/query')
    args = parser.parse_args()

    if args.log_format == 'json':
        logHandler = logging.StreamHandler(stream=sys.stdout)
        formatter = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s')
        logHandler.setFormatter(formatter)
        logging.basicConfig(handlers=[logHandler], level=args.log_level)
    else:
        logging.basicConfig(level=args.log_level)

    loop = asyncio.get_event_loop()
    try:
        # Start Slack bot
        logging.info('Initiating slack bot...')
        slackbot = SlackBot(os.environ.get('SLACK_BOT_TOKEN'), args.source)
        loop.create_task(slackbot.start())
        logging.info('Slack bot initialized.')
        # Start BMS websocket consumer
        if args.alert_channel:
            logging.info('Initiating BMS websocket consumer...')
            parse_result = urlparse(args.source[0])
            if parse_result.scheme == 'https':
                parse_result = parse_result._replace(scheme='wss')
            else:
                parse_result = parse_result._replace(scheme='ws')
            url = urljoin(parse_result.geturl(), '/ws/ns')
            bms = BMSConsumer(url, slackbot, args.alert_channel)
            loop.create_task(bms.start())
            logging.info('BMS websocket consumer initialized.')
        else:
            logging.info('Skipping BMS websocket consumer because no alert_channel set.')
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info('Received keyboard interrupt signal. Closing down event loop and exiting...')
    finally:
        logging.info('Shutting down event loop and exiting...')
        loop.close()
        logging.info('Shutdown complete. Sayounara señoras y señores.')
