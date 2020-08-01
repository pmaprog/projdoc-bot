from mongoengine import *


connect('projdoc', host='localhost', port=27017)


class User(Document):
    uid = IntField()
    name = StringField(null=True)
    surname = StringField(null=True)
    email = StringField(null=True)
    password = StringField(null=True)
    cookies = StringField(null=True)
    when_to_remind = IntField()

    meta = {'collection': 'users'}