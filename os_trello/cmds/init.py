# Copyright 2015 David Stanek <dstanek@dstanek.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import print_function
import logging
import webbrowser

import requests
import requests_oauthlib

from os_trello import _common
from os_trello import _trello


try:
    input = raw_input  # py2
except NameError:
    pass  # py3


def create_lists(trello_board):
    trello_board.lists.ensure_exists(_trello.DONE_LIST)
    trello_board.lists.ensure_exists(_trello.GATING_LIST)
    trello_board.lists.ensure_exists(_trello.COMPLETED_LIST)
    trello_board.lists.ensure_exists(_trello.IN_PROGRESS_LIST)
    trello_board.lists.ensure_exists(_trello.NEEDS_WORK_LIST)


def create_labels(trello_board, config):
    label_names = (_trello.REVIEW_LABEL, _trello.CODE_LABEL, _trello.BUG_LABEL)
    for label_name in label_names:
        trello_board.labels.ensure_exists(
            label_name, config['trello.label_colors.%s' % label_name])

    # get rid of the defaults
    for label in trello_board.labels.get_all(''):
        label.delete()


def authorize(config):
    print("It looks like you haven't setup your token yet!")
    print("Let's go get one.")
    print()
    secret = input('Paste your Trello API secret: ')

    key = config['trello.key']
    url = 'https://trello.com/1/authorize'
    auth = requests_oauthlib.OAuth1(key, secret)
    r = requests.Request(
        'GET', url, auth=requests_oauthlib.OAuth1(key, secret), params={
            'key': key,
            'name': _trello.CLIENT_NAME,
            'expiration': 'never',
            'scope': 'read,write',
            'response_type': 'token'})
    prepared = r.prepare()
    print('Your web browser is about to open so that you can authorize the '
          'os-trello application to use Trello on your behalf. Take the '
          'token that Trello gives you and put it into the config file.')
    webbrowser.open(prepared.url)


def main():
    config = _common.init_app()

    if not config.get('trello.token'):
        authorize(config)
        return 1

    t = _trello.TrelloBoard(config['trello.key'],
                            config['trello.token'],
                            config['trello.board_id'])

    create_lists(t)
    create_labels(t, config)
    return 0
