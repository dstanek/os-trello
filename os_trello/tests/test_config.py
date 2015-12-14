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

import os
import unittest

from os_trello import _config


class BaseTestConfig(object):

    def setUp(self):
        filename = os.path.join(os.path.dirname(__file__), 'test_config.yaml')
        self.config = _config.Config(filename)


class TestConfigUsingGet(BaseTestConfig, unittest.TestCase):

    def test_getting_a_setting_that_exists(self):
        expected = 0
        actual = self.config.get('root.leaf0')
        self.assertEqual(expected, actual)

    def test_getting_a_parent_setting(self):
        expected = {'leaf1': 0}
        actual = self.config.get('root.branch1')
        self.assertEqual(expected, actual)

    def test_getting_a_setting_that_doesnt_exist(self):
        expected = None
        actual = self.config.get('root.not_there')
        self.assertEqual(expected, actual)

    def test_getting_a_setting_that_doesnt_exist_with_default(self):
        expected = object()
        actual = self.config.get('root.not_there', expected)
        self.assertEqual(expected, actual)


class TestConfigUsingGetItem(BaseTestConfig, unittest.TestCase):

    def test_getting_a_setting_that_exists(self):
        expected = 0
        actual = self.config['root.leaf0']
        self.assertEqual(expected, actual)

    def test_getting_a_parent_setting(self):
        expected = {'leaf1': 0}
        actual = self.config['root.branch1']
        self.assertEqual(expected, actual)

    def test_getting_a_setting_that_doesnt_exist(self):
        with self.assertRaises(_config.SettingNotFound):
            self.config['root.not_there']
