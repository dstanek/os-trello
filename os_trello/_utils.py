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

import weakref

from six.moves import urllib


class data_property(object):

    def __init__(self, key):
        self._key = key

    def __get__(self, obj, objtype=None):
        if obj is None:
            # called on a class object
            return self
        return obj._data[self._key]


class memoized_property(property):

    def __init__(self, func):
        self._cache = weakref.WeakKeyDictionary()
        super(memoized_property, self).__init__(func)

    def __get__(self, obj, objtype):
        if not obj:
            return self
        if obj not in self._cache:
            self._cache[obj] = (
                super(memoized_property, self).__get__(obj, objtype))
        return self._cache[obj]


def urljoin(base, *parts):
    for part in parts:
        base = urllib.parse.urljoin(base + '/', part)
    return base


class Entity(object):

    def __init__(self, data, session=None):
        self._data = data
        self._session = session

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            cls_name = self.__class__.__name__
            raise AttributeError(
                '%r object has no attribute %r' % (cls_name, name))

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)
