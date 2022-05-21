import sqlite3

class Pokemon:
    def __init__(self, id, name, types, ex, lv, at, hp, de, fl, ca, ev, sh, iv_at, iv_hp, iv_de):
        self.id, self.name, self.type, self.lv, self.ex = id, name, str(types), lv, ex

        self.connection = sqlite3.connect('pokemon.db')
        self.cursor = self.connection.cursor()

        self.types_st = []
        for str_type_id in self.type.split(','):
            self.types_st.append(self.cursor.execute("""select name from types
                                                        where id = ?""", (str_type_id,)).fetchone()[0])

        self.basic_at, self.basic_hp, self.basic_de = at, hp, de
        self.iv_at, self.iv_hp, self.iv_de = iv_at, iv_hp, iv_de
        self.at, self.hp, self.de = int(self.basic_at * self.iv_at * lv / 10), \
                                    int(self.basic_hp * self.iv_hp * lv / 10), int(self.basic_de * self.iv_de * lv / 10)

        self.cp = self.at + self.hp + self.de
        self.fl, self.ca, self.ev, self.sh = fl, ca, ev, sh

    def get(self):
        return f"[{self.id}, '{self.name}', '{self.type}', {self.ex}, {self.lv}, {self.basic_at}, {self.basic_hp}, " \
               f"{self.basic_de}, {self.fl}, {self.ca}, {self.ev}, {self.sh}, {self.iv_at}, {self.iv_hp}, {self.iv_de}]"

    def get_img(self):
        if self.sh:
            return self.cursor.execute("""select href2 from pictures where id = ?""", (str(self.id),)).fetchone()[0]
        return self.cursor.execute("""select href from pictures where id = ?""", (str(self.id),)).fetchone()[0]

    def get_emoji(self):
        return self.cursor.execute("""select emoji from pictures where id = ?""", (str(self.id),)).fetchone()[0]

    def upgrade(self, up):
        self.ex += up
        while self.ex >= self.lv * 5 and self.lv <= 29:
            self.level_up()

    def level_up(self):
        self.ex -= self.lv * 5
        self.lv += 1
        self.at, self.hp, self.de = int(self.basic_at * self.iv_at * self.lv / 10), \
                                    int(self.basic_hp * self.iv_hp * self.lv / 10), \
                                    int(self.basic_de * self.iv_de * self.lv / 10)
        self.cp = self.at + self.hp + self.de

    def evolution(self):
        p = self.cursor.execute("""select id, name, type, at, hp, de, ev from pokemons
                              where id = ?""", (str(self.id + 1),)).fetchone()
        self.id, self.name, self.type, self.basic_at, self.basic_hp, self.basic_de, self.ev = p[0], p[1], p[2], p[3], \
                                                                                              p[4], p[5], p[6]
        self.at, self.hp, self.de = int(self.basic_at * self.iv_at * self.lv / 10), \
                                    int(self.basic_hp * self.iv_hp * self.lv / 10), \
                                    int(self.basic_de * self.iv_de * self.lv / 10)
        self.cp = self.at + self.hp + self.de
