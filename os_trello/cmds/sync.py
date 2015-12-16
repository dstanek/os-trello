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

import logging
import re

from os_trello import _gerrit
from os_trello import _launchpad
from os_trello import _trello
from os_trello.cmds import _common


logger = logging.getLogger('os_trello')


class Status:
    NEEDS_WORK = object()
    NEEDS_REVIEW = object()
    IN_PROGRESS = object()
    REVIEWED = object()
    GATING = object()
    DONE = object()


class ReviewAnalyzer(object):

    def __init__(self, review, username, email):
        self._review = review
        self._username = username
        self._email = email

    def _i_am_an_author(self):
        if self._review._data['owner'].get('username') == self._username:
            return True
        if self._review._data['owner']['email'] == self._email:
            return True
        # TODO: if i have submitted a review or am listed as the co-author
        return False

    def get_number(self):
        return 'gerrit:%s' % self._review.number

    def get_title(self):
        return '[%d] %s' % (self._review.number, self._review.subject)

    def get_description(self):
        msg = self._review.commit_message
        # NOTE: we must replace #\d+ because Trello will try to make that a
        # link to another card.
        return re.sub(r'#([\d]+)', r'\1', msg)

    def get_labels(self):
        if self._i_am_an_author():
            labels = [_trello.CODE_LABEL]
        else:
            labels = [_trello.REVIEW_LABEL]
        labels.append(self._review._data['project'].split('/')[-1])
        return labels

    def get_card_list_name(self):
        # TODO: use the date to move something back to NEEDS_WORK_LIST
        # if it hasn't had a lot of movement.
        review_status = self._get_status()
        if review_status == Status.DONE:
            return _trello.DONE_LIST
        elif review_status in (Status.NEEDS_REVIEW, Status.NEEDS_WORK):
            return _trello.NEEDS_WORK_LIST
        elif review_status == Status.REVIEWED:
            return _trello.COMPLETED_LIST
        elif review_status == Status.GATING:
            return _trello.GATING_LIST

    def get_url(self):
        return self._review.url

    def _get_status(self):
        def is_gating(label_data):
            if 'approved' in label_data['Workflow']:
                return True
            return False

        def ive_voted(label_data):
            for label in label_data['Code-Review']['all']:
                if (label.get('username') == self._username
                        and label['value'] != 0):
                    return True
            return False

        if self._review.status in ('ABANDONED', 'MERGED'):
            return Status.DONE
        elif is_gating(self._review.labels):
            return Status.GATING
        elif ive_voted(self._review.labels):
            # TODO: look for things that address me or contradict my vote!
            return Status.REVIEWED
        else:
            return Status.NEEDS_REVIEW

class BugAnalizer(object):

    def __init__(self, bug):
        self._bug = bug

    def _i_am_an_author(self):
        raise Exception
        if self._review._data['owner'].get('username') == self._username:
            return True
        if self._review._data['owner']['email'] == self._email:
            return True
        # TODO: if i have submitted a review or am listed as the co-author
        return False

    def get_number(self):
        return 'lp:' + self._bug.number

    def get_title(self):
        groups = re.match(r'Bug #(\d+) .*"(.*)"', self._bug.title).groups()
        return 'Bug #%s %s' % groups

    def get_description(self):
        return self._bug.description

    def get_labels(self):
        return [_trello.BUG_LABEL, self._bug._data['target_link'].rsplit('/')[-1]]
        raise Exception
        if self._i_am_an_author():
            return [_trello.CODE_LABEL]
        else:
            return [_trello.REVIEW_LABEL]

    def get_card_list_name(self):
        # TODO: this will probably need to be expanded once I figure out a
        # good bug workflow
        if self._bug.status in ('Fix Committed', 'Fix Released'):
            # TODO: will one of these trigger the bug to not show up in the
            # query?
            return _trello.DONE_LIST
        elif self._bug.status in ('New', 'Confirmed', 'Triaged', 'In Progress'):
            return _trello.NEEDS_WORK_LIST
        # TODO: is this a good idea
        # elif self._bug.status in ('Incomplete',):
        #     return _trello.WAITING_ON_LIST
        else:
            raise Exception('found unknown status: %r' % self._bug.status)

    def get_url(self):
        return self._bug.web_link


def create_a_card(trello_board, analyzer, config):
    list_name = analyzer.get_card_list_name()
    card_list = trello_board.lists.get(list_name)

    label_names = analyzer.get_labels()
    for label_name in label_names:
        if not trello_board.labels.get(label_name):
            trello_board.labels.add(
                label_name, config.get('trello.label_colors.project'))

    labels = [trello_board.labels.get(name) for name in label_names]
    trello_board.cards.add(
#    trello_board.create_card(
        analyzer.get_title(), analyzer.get_description(),
        analyzer.get_url(), card_list, labels=labels)


def apply_labels_to_card(trello_board, card, label_names, config):
    for label_name in label_names:
        label = trello_board.labels.get(label_name)
        if not label:
            label = trello_board.labels.add(
                label_name, config.get('trello.label_colors.project'))

        card.add_label(label)


def move_existing_card_to_list(trello_board, card, list_name):
    card_list = trello_board.lists.get(list_name)
    trello_board.move_card(card, card_list)


def sync_thing(analyzer, trello_board, config):
    logger.info('syncing %s', analyzer.get_number())

    card = trello_board.cards.get(analyzer.get_number())
    if not card:
        create_a_card(trello_board, analyzer, config)
        return

    # TODO: maybe update with a new title if needed?

    apply_labels_to_card(trello_board, card, analyzer.get_labels(), config)
    move_existing_card_to_list(
        trello_board, card, analyzer.get_card_list_name())


def sync_reviews(query, gerrit, trello_board, config):
    touched_change_numbers = set()
    for review in gerrit.run_query(query):
        analyzer = ReviewAnalyzer(review, 'dstanek', 'dstanek@dstanek.com')
        logger.debug('Processing %s', analyzer.get_number())
        touched_change_numbers.add(analyzer.get_number())
        sync_thing(analyzer, trello_board, config)

        if review.status == Status.DONE:
            gerrit.unstar(review.id)

    return touched_change_numbers


def sync_bugs(bugs, trello_board, config):
    touched_bug_numbers = set()
    for bug in bugs:
        analyzer = BugAnalizer(bug)
        logger.debug('Processing %s', analyzer.get_number())
        touched_bug_numbers.add(analyzer.get_number())
        sync_thing(analyzer, trello_board, config)

    return touched_bug_numbers


def main():
    config = _common.init_app()

    g = _gerrit.Gerrit(config['gerrit.base_url'],
                       config['gerrit.username'],
                       config['gerrit.password'])
    t = _trello.TrelloBoard(config['trello.key'],
                            config['trello.token'],
                            config['trello.board_id'])
    l = _launchpad.LaunchPad(config['launchpad.username'])

    touched_change_numbers = set()
    for query in config['gerrit.queries']:
        touched_change_numbers.update(sync_reviews(query, g, t, config))

    touched_bug_numbers = set()
    touched_bug_numbers.update(sync_bugs(l.get_my_bugs(), t, config))
    touched_bug_numbers.update(sync_bugs(l.get_bugs_i_commented_on(), t, config))
    touched_bug_numbers.update(sync_bugs(l.get_subscribed_bugs(), t, config))

    # any extra Trello cards to get rid of?
    all_trello_cards = set(card.number for card in t)
    orphaned_card_numbers = (all_trello_cards -
                             touched_change_numbers -
                             touched_bug_numbers)
    if None in orphaned_card_numbers:
        # NOTE: None is the result of adding a card by hand that doesn't
        # conform to the naming conventions used by the Gerrit and
        # Launchpad cards. We manually added these so we should also manually
        # delete them.
        orphaned_card_numbers.remove(None)
    for number in orphaned_card_numbers:
        logger.info('removing orphaned Trello card: %s', number)
        t.cards.get(number).delete()

    return 0
