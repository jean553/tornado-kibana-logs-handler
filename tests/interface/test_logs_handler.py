'''
Tests for POST logs
'''
import os
import time
from datetime import datetime

import requests

from elasticsearch import Elasticsearch

from elasticsearch_client import remove_all_data_indices

BASE_URL = 'http://localhost:8000/api/1/service/1'
ELASTICSEARCH_HOSTNAME = os.getenv('ELASTICSEARCH_HOSTNAME')
WAIT_TIME = 1


def test_post_log():
    '''
    Checks that post logs returns 200 and
    that the log is inserted into elasticsearch
    '''
    es_client = Elasticsearch([ELASTICSEARCH_HOSTNAME])
    remove_all_data_indices(es_client)
    time.sleep(WAIT_TIME)

    # August 9, 2017 06:56:12 pm
    log_timestamp = 1502304972

    json = {
        'logs': [
            {
                'message': 'a first log message',
                'level': 'a low level',
                'category': 'a first category',
                'date': str(log_timestamp),
            }
        ]
    }

    response = requests.post(
        BASE_URL + '/logs',
        json=json,
    )
    assert response.status_code == 200
    time.sleep(WAIT_TIME)

    date = datetime.utcfromtimestamp(log_timestamp)

    # format data-1-YYYY-MM-DD
    index = 'data-1-%04d-%02d-%02d' % (
        date.year,
        date.month,
        date.day,
    )

    result = es_client.search(
        index=index,
        body={
            'query': {
                'bool': {
                    'must': {
                        'match': {
                            'service_id': '1'
                        },
                        'match': {
                            'date': date
                        }
                    },
                }
            }
        }
    )

    logs_amount = result['hits']['total']
    assert logs_amount == 1, \
        'unexpected logs amount, got %s, expected 1' % logs_amount


def test_get_logs():
    '''
    Checks that get logs returns 200 and the expected log content
    '''
    es_client = Elasticsearch([ELASTICSEARCH_HOSTNAME])
    remove_all_data_indices(es_client)
    time.sleep(WAIT_TIME)

    log_message = 'a second log message'
    log_level = 'a second low level'
    log_category = 'a second category'

    log_datetime = datetime.utcfromtimestamp(1502885498)
    log_date = log_datetime.strftime('%Y-%m-%dT%H:%M:%S')

    es_client.create(
        index='data-1-2017-08-16',
        doc_type='logs',
        id='1',
        body={
            'service_id': '1',
            'message': log_message,
            'level': log_level,
            'category': log_category,
            'date': log_datetime,
        }
    )
    time.sleep(WAIT_TIME)

    response = requests.get(
        BASE_URL + '/logs/2017-08-16-10-00-00/2017-08-16-16-00-00',
    )
    assert response.status_code == 200

    assert len(response.json()['logs']) == 1

    log = response.json()['logs'][0]
    assert log['message'] == log_message
    assert log['level'] == log_level
    assert log['category'] == log_category
    assert log['date'] == log_date
