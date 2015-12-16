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

import collections
import logging
import re

import requests

from os_trello import _utils


logger = logging.getLogger('os_trello')

CLIENT_NAME = 'os-trello'
NEEDS_WORK_LIST = 'Needs Work'
IN_PROGRESS_LIST = 'In Progress'
COMPLETED_LIST = 'Completed'
GATING_LIST = 'Gating'
DONE_LIST = 'Done'
REVIEW_LABEL = 'review'
CODE_LABEL = 'code'
BUG_LABEL = 'bug'


class DuplicateCard(Exception):

    def __init__(self, card_number):
        message = 'duplicate Trello card found [%s]' % card_number
        super(DuplicateCard, self).__init__(message)


class CardEntity(_utils.Entity):
    base_url = 'https://trello.com/1/cards'

    @property
    def number(self):
        # TODO: move me
        match = re.match(r'^\[(\d+)\].*', self._data['name'])
        if match:
            return 'gerrit:' + match.groups()[0]
        match = re.match(r'^Bug #(\d+).*', self._data['name'])
        if match:
            return 'lp:' + match.groups()[0]
        # TODO: maybe we need to do somethings smarter?
        # raise Exception('unmanaged card? %s' % self._data['name'])

    @property
    def label_ids(self):
        url = _utils.urljoin(self.base_url, self.id, 'idLabels')
        resp = self._session.get(url)
        resp.raise_for_status()
        return resp.json()

    def delete(self):
        logger.info('deleting card %r', self.name)
        self._session.delete(_utils.urljoin(self.base_url, self.id))
        # TODO: maybe remove from the collection?

    def add_label(self, label):
        url = _utils.urljoin(self.base_url, self.id, 'idLabels')
        if label.id not in self.label_ids:
            resp = self._session.post(url, data=dict(value=label.id))
            resp.raise_for_status()


class LabelEntity(_utils.Entity):
    base_url = 'https://trello.com/1/labels'

    def delete(self):
        logger.info('deleting label %r', self.name)
        self._session.delete(_utils.urljoin(self.base_url, self.id))
        # TODO: maybe remove from the collection?


class ListEntity(_utils.Entity):

    def __contains__(self, card):
        return card.idList == self.id


class EagerCollection(object):
    entity_class = _utils.Entity
    indexed_property = 'name'

    def __init__(self, session, base_url, board_id):
        self._session = session
        self._base_url = base_url
        self._board_id = board_id
        self._loaded = False
        self._data = {}  # indexed by name
        self._index = collections.defaultdict(list)

    def _add_entity(self, entity):
        indexed_value = getattr(entity, self.indexed_property)

        #if self._index[indexed_value]:
        ##    # TODO: ??
        ##    #     entity.delete()
        #    raise DuplicateCard(indexed_value)

        self._data[entity.id] = entity
        self._index[indexed_value].append(entity)
        return entity

    def _load_if_needed(self):
        if self._loaded:
            return

        resp = self._session.get(self._base_url)
        resp.raise_for_status()
        for data in resp.json():
            entity = self.entity_class(data, self._session)
            self._add_entity(entity)

        self._loaded = True

    def get(self, name, default=None):
        self._load_if_needed()
        entities = self._index[name]
        if len(entities) == 0:
            return default
        elif len(entities) > 1:
            raise Exception('too many rows found for %r' % name)
        return entities[0]

    def get_all(self, name):
        self._load_if_needed()
        return self._index[name]

    def __len__(self):
        self._load_if_needed()
        return len(self._data)

    def __iter__(self):
        for entity in self._data.values():
            yield entity


class CardCollection(EagerCollection):
    entity_class = CardEntity
    indexed_property = 'number'

    def add(self, name, description, source_url, card_list, labels=None):
        logger.info('creating card %r', name)
        card_list_id = card_list.id if card_list else None
        label_ids = [label.id for label in (labels or [])]
        data = dict(name=name, desc=description, idList=card_list_id,
                    idLabels=label_ids, urlSource=source_url)
        resp = self._session.post(CardEntity.base_url, data=data)
        resp.raise_for_status()
        return self._add_entity(CardEntity(resp.json(), self._session))


class LabelCollection(EagerCollection):
    entity_class = LabelEntity

    def add(self, name, color):
        url = _utils.urljoin(self._base_url, '/1/labels')
        data = dict(name=name, color=color, idBoard=self._board_id)
        resp = self._session.post(url, data=data)
        resp.raise_for_status()
        return self._add_entity(LabelEntity(resp.json()))

    def ensure_exists(self, name, color):
        return self.get(name) or self.add(name, color)


class ListCollection(EagerCollection):
    entity_class = ListEntity

    def add(self, name):
        url = _utils.urljoin(self._base_url, '/1/lists')
        data = dict(name=name, idBoard=self._board_id)
        resp = self._session.post(url, data=data)
        resp.raise_for_status()
        return self._add_entity(self.entity_class(resp.json()))

    def ensure_exists(self, name):
        return self.get(name) or self.add(name)
        card_list = self.get(name)
        if not card_list:
            card_list = self.add(name)
        return card_list


class TrelloBoard(object):
    base_url = 'https://trello.com'

    def __init__(self, key, token, board_id):
        self._session = requests.Session()
        self._session.params = {'key': key, 'token': token}

        board_id = self._get_real_board_id(board_id)

        self.labels = LabelCollection(self._session, _utils.urljoin(
            self.base_url, '/1/boards/%s/labels/' % board_id), board_id)
        self.lists = ListCollection(self._session, _utils.urljoin(
            self.base_url, '/1/boards/%s/lists/' % board_id), board_id)
        self.cards = CardCollection(self._session, _utils.urljoin(
            self.base_url, '/1/boards/%s/cards/' % board_id), board_id)

    def _get_real_board_id(self, board_id):
        """Return the real board_id for the configured board_id.

        The config file can either have the GUID or the short id
        (the one found in the URL of the browser). This will look
        up the actual GUID because that is what most of the API
        calls require.
        """
        resp = self._session.get(self.base_url + '/1/boards/%s' % board_id)
        resp.raise_for_status()
        return resp.json()['id']

    def __len__(self):
        return len(self.cards)

    def __iter__(self):
        return iter(self.cards)

    def create_card(self, name, description, source_url, card_list,
                    label_names=None):
        logger.info('creating card %r', name)
        card_list_id = card_list.id if card_list else None
        label_ids = [self.labels.get(n).id for n in (label_names or [])]
        data = dict(name=name, desc=description, idList=card_list_id,
                    idLabels=label_ids, urlSource=source_url)
        resp = self._session.post(CardEntity.base_url, data=data)
        resp.raise_for_status()
        return CardEntity(resp.json(), self._session)

    def move_card(self, card, card_list):
        logger.info('moving %r to %r', card, card_list)
        if card.idList != card_list.id:
            url = _utils.urljoin(CardEntity.base_url, card.id, 'idList')
            self._session.put(url, data=dict(value=card_list.id))
