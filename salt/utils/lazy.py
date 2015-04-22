# -*- coding: utf-8 -*-

# Import Python Libs
from __future__ import absolute_import
import logging
import collections
import salt.exceptions

log = logging.getLogger(__name__)


def verify_fun(lazy_obj, fun):
    '''
    Check that the function passed really exists
    '''
    if not fun:
        raise salt.exceptions.SaltInvocationError(
            'Must specify a function to run!\n'
            'ex: manage.up'
        )
    if fun not in lazy_obj:
        # If the requested function isn't available, lets say why
        raise salt.exceptions.CommandExecutionError(lazy_obj.missing_fun_string(fun))


class LazyDict(collections.MutableMapping):
    '''
    A base class of dict which will lazily load keys once they are needed

    TODO: negative caching? If you ask for 'foo' and it doesn't exist it will
    look EVERY time unless someone calls load_all()
    As of now this is left to the class which inherits from this base
    '''
    def __init__(self):
        self.clear()

    def __nonzero__(self):
        # we are zero if dict is empty and loaded is true
        return bool(self._dict or not self.loaded)

    def __bool__(self):
        # we are zero if dict is empty and loaded is true
        return self.__nonzero__()

    def clear(self):
        '''
        Clear the dict
        '''
        # create a dict to store loaded values in
        self._dict = {}

        # have we already loded everything?
        self.loaded = False

    def _load(self, key):
        '''
        Load a single item if you have it
        '''
        raise NotImplementedError()

    def _load_all(self):
        '''
        Load all of them
        '''
        raise NotImplementedError()

    def _missing(self, key):
        '''
        Wheter or not the key is missing (meaning we know its not there)
        '''
        return False

    def __setitem__(self, key, val):
        self._dict[key] = val

    def __delitem__(self, key):
        del self._dict[key]

    def __getitem__(self, key):
        '''
        Check if the key is ttld out, then do the get
        '''
        if self._missing(key):
            raise KeyError(key)

        if key not in self._dict and not self.loaded:
            # load the item
            if self._load(key):
                log.debug('LazyLoaded {0}'.format(key))
                return self._dict[key]
            else:
                log.debug('Could not LazyLoad {0}'.format(key))
                raise KeyError(key)
        else:
            return self._dict[key]

    def __getattr__(self, name):
        '''
        Check if the name is in the dict and return it if it is
        '''
        if name not in self._dict and not self.loaded:
            # load the item
            if self._load(name):
                log.debug('LazyLoaded {0}'.format(name))
                return self._dict[name]
            else:
                log.debug('Could not LazyLoad {0}'.format(name))
                raise KeyError(name)
        elif name in self:
            return self[name]
        raise AttributeError(name)

    def __len__(self):
        # if not loaded,
        if not self.loaded:
            self._load_all()
        return len(self._dict)

    def __iter__(self):
        if not self.loaded:
            self._load_all()
        return iter(self._dict)