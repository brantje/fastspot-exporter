import urllib.request
import logging
import json
from urllib.error import URLError, HTTPError
from prometheus_client import start_http_server, Gauge, REGISTRY, PROCESS_COLLECTOR, PLATFORM_COLLECTOR, GC_COLLECTOR, push_to_gateway, CollectorRegistry 
from time import sleep
import os
import socket
[REGISTRY.unregister(c) for c in [PROCESS_COLLECTOR, PLATFORM_COLLECTOR, GC_COLLECTOR ]]

registry = CollectorRegistry()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s — %(message)s',
                    datefmt='%Y-%m-%d_%H:%M:%S',
                    handlers=[logging.StreamHandler()])

def request(url, additional_headers = {}, data = None):
    if data:
        data = json.dumps(data)
        data = data.encode('utf-8')   # needs to be bytes

    try:
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36',
                'Content-Type': 'application/json; charset=utf-8',
                **additional_headers
            }
        )
        with urllib.request.urlopen(req) as url:
            data = json.loads(url.read())
            return data
    except HTTPError as e:
        # do something
        print(e.code)
        print('Error code: ', e.read().decode())
    except URLError as e:
        # do something
        print('Reason: ', e.reason)                


FIELDS = [
    "daily_volume" ,
    "daily_volume_quote",
    "daily_volume_usd",
    "daily_count",
    "weekly_volume",
    "weekly_volume_quote",
    "weekly_volume_usd",
    "weekly_count",
    "monthly_volume",
    "monthly_volume_quote",
    "monthly_volume_usd",
    "monthly_count",
    "total_volume",
    "total_volume_quote",
    "total_volume_usd",
    "total_count",
    "price",
    "price_usd",
    "last_price",
    "last_price_usd",
    "last_size",
    "last_size_quote",
    "last_size_usd",
    "last_time",
]


gauges = {}

for field in FIELDS:
    gauges[field] = Gauge('fastspot_'+ field, field, ['ticker'],  registry=registry)



def get_fastspot_info():
    data = request('https://stats.fastspot.io/v2/tickers')
    
    for ticker in data:
        for field in FIELDS:
                gauges[field].labels(ticker=ticker.get('ticker_id')).set(ticker[field])


if __name__ == '__main__':
    logging.info(40 * '-')
    logging.info('FastSpot Exporter')
    logging.info(40 * '-')
   
    port = int(os.environ.get('PORT', 8000))
    start_http_server(port, registry=registry)
    logging.info('Prometheus exporter running at port {}'.format(port))
    logging.info(40 * '-')
    WALLET_BALANCE = Gauge('crypto_wallet_balance','wallet_balance')
    WALLET_BALANCE.set(34)
    while True:
        get_fastspot_info()
        if(os.environ.get('PUSHGATEWAY', False)):
            push_gateway = os.environ.get('PUSHGATEWAY')
            logging.info('Pushing to gateway {}'.format(push_gateway.get('host')))
            group = {}
            group['instance'] = push_gateway.get('instance', socket.gethostname())
            try:
                push_to_gateway(push_gateway.get('host'), job=os.environ.get('PUSHGATEWAY_JOB'), grouping_key=group, registry=registry)
            except URLError:
              logging.error('Gateway is offline...')

        sleep(60)
