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

import argparse
import logging.config
import os

from os_trello import _config


DEFAULT_CONFIG_FILE = '~/.config/os-trello/os-trello.yaml'


def _cli():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config', action='store', default=DEFAULT_CONFIG_FILE,
        help='config file (defaults to: %s)' % DEFAULT_CONFIG_FILE)
    return parser.parse_args()


def init_app():
    args = _cli()
    config = _config.Config(os.path.expanduser(args.config))

    logging.basicConfig()
    if config.get('logging'):
        logging.config.dictConfig(config['logging'])

    return config
