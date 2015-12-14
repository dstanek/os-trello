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

import yaml


class SettingNotFound(Exception):
    """Raised when a setting is not found."""

    def __init__(self, setting, filename):
        message = '%r not in %s' % (setting, filename)
        super(SettingNotFound, self).__init__(message)


class Config(object):
    """A simple abstraction over a YAML configuration file.

    The abstraction allows the user to ask for a hierarchy of keys in single
    call, avoiding the need to manually recurse the data structure.
    """

    def __init__(self, filename):
        self._filename = filename
        self._data = yaml.load(open(filename))

    def get(self, setting, default=None):
        """C.get(setting[,default=None]) -> C[setting] if exists, else default.
        """
        try:
            return self[setting]
        except SettingNotFound:
            return default

    def __getitem__(self, setting):
        """C[setting] if exists, else raise SettingNotFound."""
        current = self._data
        for part in setting.split('.'):
            try:
                current = current[part]
            except KeyError:
                raise SettingNotFound(setting, self._filename)
        return current
