from mongoengine import *


connect('projdoc', host='localhost', port=27017)


class User(DynamicDocument):
    uid = IntField()
    name = StringField(null=True)
    surname = StringField(null=True)
    email = StringField(null=True)
    password = StringField(null=True)
    cookies = StringField(null=True)
    remind_date = DateTimeField()
    chosen_time = DateTimeField()

    meta = {'collection': 'users'}
