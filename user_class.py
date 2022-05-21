import sqlite3

class User:
    def __init__(self, ds_id, info):
        self.ds_id = ds_id
        self.info = info

    def upgrade(self, up):
        self.info['Total_experience'] += up
        while self.info['Total_experience'] >= self.info['Level'] * 5:
            self.level_up()

    def level_up(self):
        self.info['Total_experience'] -= self.info['Level'] * 5
        self.info['Level'] += 1