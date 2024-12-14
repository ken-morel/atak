import json
import os
from logging import getLogger


log = getLogger(__name__)


class Store(dict):
    """
    Creates a json settings file at path *sjs* _dkd df_ **ama**
    """

    def __init__(self, path: str, default: dict = {}):
        """
        :param path: the path to the settings file
        """
        self.path = path
        self.page_stores = {}
        self.partitions = {}
        super().__init__(default)
        try:
            self.load()
        except Exception:
            self.save()

    def load(self):
        """
        Loads the file from specified `path`

        :raises OSError: in case the faile to open the file
        :param c: dd
        """
        with open(self.path) as f:
            self.update(json.loads(f.read()))

    def save(self):
        with open(self.path, "w") as f:
            f.write(json.dumps(self, indent=2))

    def __getitem__(self, item):
        try:
            self.load()
        except Exception as e:
            log.info("while loading Store", self)
            log.error(e)
            raise
        if isinstance(item, tuple):
            obj = self
            for x in item:
                obj = obj[x]
            return x
        else:
            return super().__getitem__(item)

    def __setitem__(self, item, value):
        if isinstance(item, tuple):
            *path, item = item
            obj = self
            for x in path:
                obj = obj[x]
            obj[item] = value
        else:
            super().__setitem__(item, value)
        try:
            self.save()
        except Exception as e:
            log.info("while saving Store", self)
            log.error(e)
            raise

    def for_page(self, page, default={}):
        if page not in self.page_stores:
            self.page_stores[page] = Pagestore(self, page, default=default)
        return self.page_stores[page]

    def partition(self, name, default={}):
        if name not in self.partitions:
            self.partitions[name] = StorePartition(self, name, default=default)
        return self.partitions[name]

    def __hash__(self):
        return hash(self.path)


class StorePartition(Store):
    FORMAT = "~~[$__partition__('{0}')]~~"

    def __init__(self, store, name, default={}):
        self.store = store
        self.partitions = {}
        self.name = self.FORMAT.format(name)
        dict.__init__(self, default)
        try:
            self.load()
        except:
            self.save()

    def __setitem__(self, item, value):
        dict.__setitem__(self, item, value)
        self.save()

    def __getitem__(self, item):
        return dict.__getitem__(self, item)

    def save(self):
        self.store[self.name] = self
        self.store.save()

    def load(self):
        data = self.store[self.name]
        self.update(data)


class Pagestore(StorePartition):
    FORMAT = "~~[$__pageStore__('{0}')]~~"
