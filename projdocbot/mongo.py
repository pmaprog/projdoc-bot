from mongoengine import *

connect('projdoc', host='localhost', port=27017)


class UserStatistics(EmbeddedDocument):
    correct_answers = ListField(IntField(), default=list)
    notifications_count = IntField(default=0)
    success_date = DateTimeField(null=True)
    # отслеживать нажатие на ссылку
    # отслеживать нажатия кнопок студентами
    # запоминать количество баллов в каждой попытке


class User(Document):
    uid = IntField()
    name = StringField(null=True)
    surname = StringField(null=True)
    email = StringField(null=True)
    password = StringField(null=True)
    cookies = StringField(null=True)
    remind_date = DateTimeField()
    chosen_time = DateTimeField()
    group = StringField()
    seminars = MapField(EmbeddedDocumentField(UserStatistics))

    meta = {'collection': 'users'}


class Test(DynamicDocument):
    meta = {'collection': 'tests'}
