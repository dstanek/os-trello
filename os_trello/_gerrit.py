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

import json
import logging

import requests
from six.moves import urllib

from os_trello import _utils


logger = logging.getLogger('os_trello')


class GerritReview(object):

    id = _utils.data_property('id')
    number = _utils.data_property('_number')
    labels = _utils.data_property('labels')
    project = _utils.data_property('project')
    status = _utils.data_property('status')
    subject = _utils.data_property('subject')

    def __init__(self, review_data):
        self._data = review_data

    @property
    def commit_message(self):
        revision = self._data['revisions'].values()[0]  # we only get the last one
        return revision['commit']['message']

    @property
    def url(self):
        return 'https://review.openstack.org/%s' % self.number


class Gerrit(object):

    def __init__(self, base_url, username, password):
        self._base_url = base_url
        self.session = requests.Session()
        self.auth = requests.auth.HTTPDigestAuth(username, password)

    def _url(self, fragment):
        return urllib.parse.urljoin(self._base_url, fragment)

    def _request(self, fragment):
        resp = self.session.get(self._url(fragment), auth=self.auth)
        resp.raise_for_status()
        return json.loads(resp.text.lstrip(")]}'"))

    def run_query(self, query):
        logger.info('running Gerrit query %r', query)
        query = [
            ('q', query),
            ('o', 'CURRENT_REVISION'),
            ('o', 'CURRENT_COMMIT'),
            ('o', 'DETAILED_LABELS'),
            ('o', 'DETAILED_ACCOUNTS'),
        ]
        qs = urllib.parse.urlencode(query)
        for review_data in self._request('/a/changes/?%s' % qs):
            yield GerritReview(review_data)

    def unstar(self, change_id):
        logger.info('unstarring %s', change_id)
        resp = self.session.delete(
            self._url('/a/accounts/self/starred.changes/%s' % change_id),
            auth=self.auth)
        resp.raise_for_status()
