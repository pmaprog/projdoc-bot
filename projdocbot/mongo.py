from mongoengine import *

connect('projdoc', host='localhost', port=27017)


class UserStatistics(EmbeddedDocument):
    correct_answers_lst = ListField(IntField(), default=list)
    notifications_count = IntField(default=0)
    success_date = DateTimeField(null=True)
    # отслеживать нажатие на ссылку
    # отслеживать нажатия кнопок студентами


class User(Document):
    uid = IntField()
    name = StringField(null=True)
    surname = StringField(null=True)
    email = StringField(null=True)
    # password = StringField(null=True)
    cookies = StringField(null=True)
    chosen_time = DateTimeField()
    group = StringField()
    seminars = MapField(EmbeddedDocumentField(UserStatistics))

    remind_date = DateTimeField()
    start_test_dt = DateTimeField()

    meta = {'collection': 'users'}


class Test(DynamicDocument):
    meta = {'collection': 'tests'}
