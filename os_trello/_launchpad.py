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

import cachecontrol
import requests

from os_trello import _utils


class Bug(_utils.Entity):

    @property
    def number(self):
        return self._data['bug_link'].rsplit('/')[-1]

    @property
    def description(self):
        resp = self._session.get(self._data['bug_link'])
        return resp.json()['description']


class LaunchPad(object):
    """Search Launchpad for relevant bugs and specs.

    Reference:
        https://api.launchpad.net/1.0/#person-searchTasks
    """

    def __init__(self, username):
        self._user_url = 'https://api.launchpad.net/1.0/~%s' % username
        self._session = cachecontrol.CacheControl(requests.Session())

    def _search(self, query_name):
        url = '{user_url}?ws.op=searchTasks&{query_name}={user_url}'.format(
            user_url=self._user_url, query_name=query_name)
        resp = self._session.get(url)
        for bug_data in resp.json()['entries']:
            yield Bug(bug_data, self._session)

    def get_my_bugs(self):
        return self._search('assignee')

    def get_subscribed_bugs(self):
        return self._search('bug_subscriber')

    def get_bugs_i_commented_on(self):
        #return self._search('bug_commenter')
        return []

# TODO: maybe reporter?
