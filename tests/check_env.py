import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

print('EXAM_MASTER_KEY', bool(os.environ.get('EXAM_MASTER_KEY')))
print('FLASK_SECRET_KEY', bool(os.environ.get('FLASK_SECRET_KEY')))
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
    client.server_info()
    print('MONGO_OK')
except ServerSelectionTimeoutError as e:
    print('MONGO_FAIL', str(e))
