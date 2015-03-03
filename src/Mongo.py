
import pymongo

import R

class MongoDB(object):

    _mongo_db = None

    def __init__(self, mongo_db):
        self._mongo_db = mongo_db

    def use_collection(self, collection_name):
        return self._mongo_db[collection_name]

class Mongo(object):

    _mongo_cl = None
    _mongo_db = {}

    def __init__(self, host, port):
        self._mongo_cl = pymongo.MongoClient(host, port)

    def get(self, db_name = 'jzgps'):
        if self._mongo_db.get(db_name, None) is None:
            self._mongo_db[db_name] = MongoDB(self._mongo_cl[db_name])

        return self._mongo_db[db_name]

    def gen_uuid(self, uuid_name = 'common'):
        result = self.get().use_collection(R.collection_uuid).find_and_modify({R.uuid_name:uuid_name}, {'$inc' : {R.uuid_id : 1}}, upsert = True, new = True)
        if result.get(R.uuid_id, None) is None:
            raise 'mongo execute find_and_modify failed'

        return int(result[R.uuid_id])