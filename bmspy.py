#!/usr/bin/env python3

# StdLib
import argparse
import asyncio
import dotenv
import logging
import os
import sys
from urllib.parse import urljoin, urlparse
import yaml

# Internal deps
from bmspy import BMSConsumer, Router, SlackBot

# External deps
from pythonjsonlogger import jsonlogger

dotenv.load_dotenv()

# Do work.
if __name__ == '__main__':
    # TODO: Setup argparse for these
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--alert-channel', default=os.environ.get('BMSPY_ALERT_CHANNEL', None), metavar='CHANNEL', help='Slack channel to send health updates to')
    parser.add_argument('-c', '--config', default='settings.yaml', metavar='CONFIG_FILE', help='config file to use')
    parser.add_argument('--log-format', choices=['json', 'text'], default='text', help='format for log messages')
    parser.add_argument('-l', '--log-level', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], default='WARNING', help='level to show log messages')
    parser.add_argument('-s', '--source', nargs='+', help='bms url(s) to monitor/query')
    args = parser.parse_args()

    # Setup logging
    if args.log_format == 'json':
        logHandler = logging.StreamHandler(stream=sys.stdout)
        formatter = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s')
        logHandler.setFormatter(formatter)
        logging.basicConfig(handlers=[logHandler], level=args.log_level)
    else:
        logging.basicConfig(level=args.log_level)

    # Load config file
    if os.path.exists(args.config):
        try:
            with open(args.config, 'r') as config_file:
                config_values = yaml.safe_load(config_file)
        except Exception:
            logging.error('failed to parse config_file as yaml')
            raise
    else:
        logging.warning(f'config file not found. running with sane defaults.')

    loop = asyncio.get_event_loop()
    try:
        # SlackBot
        logging.info('Initiating slack bot...')
        slackbot = SlackBot(os.environ.get('SLACK_BOT_TOKEN'), args.source)
        loop.create_task(slackbot.start())
        logging.info('Slack bot initialized.')

        # Routing
        router = Router(slackbot)
        if 'routes' in config_values.keys():
            router.add_routes(config_values['routes'])
        else:
            logging.info('no routes defined in config_file')

        # BMS websocket consumer
        if args.alert_channel:
            # Add a default alert channel
            router.add_route({'channel': args.alert_channel, 'namespaces': '/.*/'})
        logging.info('Initiating BMS websocket consumer...')
        parse_result = urlparse(args.source[0])
        if parse_result.scheme == 'https':
            parse_result = parse_result._replace(scheme='wss')
        else:
            parse_result = parse_result._replace(scheme='ws')
        url = urljoin(parse_result.geturl(), '/ws/ns')
        bms = BMSConsumer(url, slackbot, router)
        loop.create_task(bms.start())
        logging.info('BMS websocket consumer initialized.')

        # Away we go...
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info('Received keyboard interrupt signal. Closing down event loop and exiting...')
    finally:
        logging.info('Shutting down event loop and exiting...')
        loop.close()
        logging.info('Shutdown complete. Sayounara señoras y señores.')
