import math
import random

import sqlite3

from asyncio import sleep

from datetime import datetime, timedelta

import pymorphy2
import requests

from discord.ext import commands
from discord_components import Button, ButtonStyle

from pokemon_class import Pokemon
from user_class import User
from config import CITY, WEATHER_API_KEY


class PokemonCommands(commands.Cog):
    def __init__(self, bot, u_command):
        self.bot = bot
        self.u_command = u_command
        self.info_channel = None

        self.weather_id = 1
        self.connection = sqlite3.connect('pokemon.db')
        self.cursor = self.connection.cursor()
        self.map = self.upload_map()
        self.actions = {}
        self.giveaway = {}
        self.trains = {}
        self.cursor.execute(f"""update users
                                set action = 'default'""")
        self.connection.commit()
        self.weather_check = None
        self.weather_list = {('Clouds',): ['1-', '13', '8-', '7-'], ('Clear',): ['10', '5-', '2-', '9-'],
                             ('Mist', 'Smoke', 'Haze', 'Fog'): ['14', '8-', '11'],
                             ('Sand', 'Dust'): ['9-'], ('Squall', 'Tornado'): ['7-', '15'], ('Snow',): ['6-', '16'],
                             ('Rain', 'Drizzle', 'Thunderstorm'): ['3-', '12', '4-']}
        self.weather_href = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}"

    def upload_map(self):
        st = list(map(lambda x: eval(x[0]), self.cursor.execute(f"""select pokemons_stack from map""").fetchall()))
        for i in range(len(st)):
            for j in range(len(st[i])):
                if type(st[i][j]) is list:
                    st[i][j] = Pokemon(*st[i][j])
        return st

    def update_map(self):
        bd_map = [[y for y in x] for x in self.map]
        for i in range(len(bd_map)):
            for j in range(len(bd_map[i])):
                if type(bd_map[i][j]) is Pokemon:
                    bd_map[i][j] = eval(bd_map[i][j].get())
        for i in range(len(bd_map)):
            self.cursor.execute(f"""update map set pokemons_stack = \"{bd_map[i]}\" where bio_id = {i + 1}""")
        self.connection.commit()

    def get_action(self, ctx):
        return self.cursor.execute("""select action from users
                                      where ds_id = ?""", (str(ctx.author.id),)).fetchone()[0]

    def get_bio_id(self, ctx):
        return self.cursor.execute("""select bio_id from users
                                      where ds_id = ?""", (str(ctx.author.id),)).fetchone()[0]

    def get_inventory(self, ctx):
        return eval(self.cursor.execute("""select inventory from users
                                      where ds_id = ?""", (str(ctx.author.id),)).fetchone()[0])

    def get_information(self, ctx):
        return eval(self.cursor.execute("""select information from users
                                           where ds_id = ?""", (str(ctx.author.id),)).fetchone()[0])

    def get_pokedex(self, ctx):
        return self.cursor.execute("""select pokedex from users
                                      where ds_id = ?""", (str(ctx.author.id),)).fetchone()[0]

    def get_bag(self, ctx):
        res = self.cursor.execute("""select bag from users
                                      where ds_id = ?""", (str(ctx.author.id),)).fetchone()[0]
        if res is None:
            return ''
        return res

    def get_pokemons(self, ctx):
        bag = self.get_bag(ctx).lstrip().split(']')[:-1]
        return [eval(p + ']') for p in bag]

    def change_action(self, ctx, new_action):
        self.cursor.execute(f"""update users
                                set action = '{new_action}'
                                where ds_id = ?""", (str(ctx.author.id),))
        self.connection.commit()

    def change_inventory(self, ctx, new_inventory):
        self.cursor.execute(f"""update users
                                set inventory = "{new_inventory}"
                                where ds_id = ?""", (str(ctx.author.id),))
        self.connection.commit()

    def change_information(self, ctx, new_information):
        self.cursor.execute(f"""update users
                                set information = "{new_information}"
                                where ds_id = ?""", (str(ctx.author.id),))
        self.connection.commit()

    def change_bag(self, ctx, new_bag):
        self.cursor.execute(f"""update users
                                set bag = "{new_bag}"
                                where ds_id = ?""", (str(ctx.author.id),))
        self.connection.commit()

    def is_weather_boost(self, *p_types):
        for p_type in p_types:
            for weather, types in self.weather_list.items():
                if self.weather in weather and p_type in types:
                    return True
        return False

    def update_weather(self):
        """try:
            response = requests.get(self.weather_href).json()
            return response['weather'][0]['main']
        except Exception:
            return 'Error'"""

        return 'Clouds'

    async def start_world(self):
        await self.info_channel.send('Мир запустился, удачной охоты')

        while True:
            await sleep(1)

            bio_id = random.randint(1, len(self.map))
            str_bio_id = str(bio_id)
            if len(str_bio_id) == 1:
                str_bio_id += '-'

            cel = random.randint(0, len(self.map[bio_id - 1]) - 1)
            if self.map[bio_id - 1][cel] is not None:
                self.map[bio_id - 1][cel] = None
                self.update_map()
                continue

            result = self.cursor.execute(f"""select id, rare from pokemons
                                             where bio_id like '%{str_bio_id}%'""").fetchall()
            pokemons_chances_st = []
            for x in result:
                pokemons_chances_st.extend([x[0]] * x[1])

            chosen_pokemon_id = random.choice(pokemons_chances_st)

            p = self.cursor.execute("""select id, name, type, at, hp, de, fl, ca, ev, min_lv, max_lv from pokemons
                                        where id = ?""", (str(chosen_pokemon_id),)).fetchone()

            sh = random.randint(1, 400) // 400
            lv = random.randint(p[9], p[10])

            p = Pokemon(p[0], p[1], p[2], 0, lv, p[3], p[4], p[5], p[6], p[7], p[8], sh,
                        random.randint(90, 110) / 100, random.randint(90, 110) / 100,
                        random.randint(90, 110) / 100)

            self.map[bio_id - 1][cel] = p
            self.update_map()

            msg = f'---------------------------------\n'
            if p.sh:
                msg += f'***✨Шайни✨***\n'
            msg += f'{p.get_emoji()} **Имя** {p.name} **Тип** {", ".join(p.types_st)}' \
                   f' **Сила** {p.cp}\n' \
                   f'**Уровень** {p.lv} **Опыт** {p.ex}/{p.lv * 5}\n' \
                   f'---------------------------------\n'

            await self.info_channel.send(msg)

            now = datetime.now()

            if self.weather_check is None:
                self.weather = self.update_weather()
                await self.info_channel.send(self.weather)
                self.weather_check = now

            if now >= self.weather_check + timedelta(hours=2):
                self.weather = self.update_weather()
                await self.info_channel.send(self.weather)
                self.weather_check = now

            D = self.trains.copy()
            for id, train in D.items():
                if train['datetime'] + timedelta(seconds=0) <= now:
                    ctx = train['ctx']
                    pokemon_id = train['pokemon_id']
                    bag = self.get_pokemons(ctx)
                    p = bag[int(pokemon_id) - 1]
                    p = Pokemon(*p)
                    u = User(ctx.author.id, self.get_information(ctx))

                    await self.stop_train(ctx)

                    up = random.randint(500, 1000)
                    start_lv = p.lv
                    p.upgrade(up)
                    u.upgrade(up)

                    self.change_information(ctx, u.info)

                    bag[int(pokemon_id) - 1] = eval(p.get())
                    self.change_bag(ctx, f'{"".join(list(map(lambda x: f"{x}", bag)))}')
                    msg = f'**тренировка с покемоном {p.name} завершилась**\n' \
                          f'ваш {p.name} получил {up} опыта\n'

                    if p.lv - start_lv != 0:
                        word = pymorphy2.MorphAnalyzer().parse('уровень')[0].make_agree_with_number(
                            p.lv - start_lv).word
                        msg += f"и повысил тем самым {p.lv - start_lv} {word}\n"

                    msg += f"{p.name}| Уровень:{p.lv} Опыт:{p.ex}/{p.lv * 5}\n"

                    if p.lv == 30:
                        msg += f"**Ваш покемон достиг максимального уровня**\n"

                    if p.ev is not None:
                        if p.lv >= p.ev:
                            msg += f'**Вы можете проэволюционировать своего покемона**'

                    await ctx.send(msg)

    @commands.command(name='phelp')
    async def phelp(self, ctx):
        await ctx.send("0| Привет, я бот Руби, я тренер покемонов и готов погрузить тебя в этот прекрасный мир\n"
                       "1| Введи >start для начала\n"
                       "2| Затем нужно зарегестрироваться (Профиль -> Регистрация, там же можно и удалить/изменить "
                       "аккаунт)\n"
                       "3| Тебе дадут стартовые 5 покеболов, теперь ты можешь забрать подарок (Разное -> Подарок) и "
                       "отправится в путь\n"
                       "4| Выбери биом себе по душе (Приключение -> Все биомы) и следуй туда (Начать путешествие ->"
                       " Перейти в другой биом), там можно ловить покемонов (Начать путешествие -> Искать покемонов)\n"
                       "5| После охоты можешь оценить результат (Профиль -> Хранилище покемонов/Инвентарь)\n"
                       "6| С тем покемоном, который тебе понравился больше всего можешь начать тренировку (Тренировка "
                       "покемонов -> Начать тренировку) она займёт 5 минут и даст опыт твоему покемону\n"
                       "7| После усердных тренировок ты можешь совершить эволюцию своего покемона (Профиль ->"
                       " Хранилище покемонов -> Проволюционировать покемона) это усилит его и изменит его внешний вид\n"
                       "8| И помни, главное - собрать их всех!!!")

    @commands.command(name='start')
    async def start(self, ctx):
        msg = await ctx.send(components=[[Button(style=ButtonStyle.grey, label="Профиль", emoji='👤'),
                                          Button(style=ButtonStyle.grey, label="Разное", emoji='🗳'),
                                          Button(style=ButtonStyle.grey, label="Начать путешествие", emoji='🧭'),
                                          Button(style=ButtonStyle.grey, label="Тренировка покемонов", emoji='🎯')]])

        while True:
            response = await self.bot.wait_for("button_click", check=lambda m: m.channel == ctx.channel and \
                                                                               m.author.id == ctx.author.id)
            if response.channel == ctx.channel:
                if response.component.label == "Профиль":
                    await response.respond(content="Сдесь вы можете выбрать действия, связанные с вашим профилем")
                    await msg.delete()
                    await self.profile(ctx)

                elif response.component.label == "Разное":
                    await response.respond(content="Сдесь вы можете поделать разное...")
                    await msg.delete()
                    await self.different(ctx)

                elif response.component.label == "Начать путешествие":
                    await response.respond(content="Сдесь вы можете начать охоту")
                    await msg.delete()
                    await self.journey(ctx)

                elif response.component.label == "Тренировка покемонов":
                    await response.respond(content="Сдесь вы можете начать тренировку")
                    await msg.delete()
                    await self.training(ctx)

    async def profile(self, ctx):
        msg = await ctx.send(components=[[Button(style=ButtonStyle.green, label="Регестрация", emoji='🌐'),
                                          Button(style=ButtonStyle.red, label="Удалить аккаунт", emoji='🗑'),
                                          Button(style=ButtonStyle.blue, label="Изменить ваше имя", emoji='👥'),
                                          Button(style=ButtonStyle.grey, label="Мой профиль", emoji='ℹ')],
                                         [Button(style=ButtonStyle.grey, label="Инвентарь", emoji='🎒'),
                                          Button(style=ButtonStyle.grey, label="Хранилище покемонов", emoji='📠'),
                                          Button(style=ButtonStyle.grey, label="Покедекс", emoji='📕'),
                                          Button(style=ButtonStyle.grey, label="Назад", emoji='🔙')]
                                         ])

        while True:
            response = await self.bot.wait_for("button_click", check=lambda m: m.channel == ctx.channel and \
                                                                               m.author.id == ctx.author.id)
            if response.channel == ctx.channel:
                if response.component.label == "Регестрация":
                    await response.respond(content="Напишите желаемое имя")
                    msg2 = await self.bot.wait_for('message', check=lambda m: m.channel == ctx.channel and \
                                                                              m.author.id == ctx.author.id)
                    if msg2.content.lower() == 'отмена':
                        await ctx.send('действие отмененно')
                    else:
                        await self.u_command.registration(ctx, msg2.content)

                elif response.component.label == "Покедекс":
                    await response.respond(content="Тут можно посмотреть чего вам не хватает для коллекции")
                    await self.pokedex(ctx)

                elif response.component.label == "Удалить аккаунт":
                    await response.respond(content="Вы уверены? Напишите точное имя аккаунта для подтверждения или "
                                                   "отмена")
                    msg2 = await self.bot.wait_for('message', check=lambda m: m.channel == ctx.channel and \
                                                                              m.author.id == ctx.author.id)
                    user = self.cursor.execute("""select name from users
                                                          where ds_id = ?""", (str(ctx.author.id),)).fetchone()

                    if user is None:
                        await response.respond(content="Вы не зарегестрированы")

                    else:
                        if msg2.content.lower() == 'отмена':
                            await ctx.send('действие отмененно')
                        elif msg2.content.lower() == user[0].replace(' ', '').lower():
                            await self.u_command.delete_account(ctx)
                        else:
                            await ctx.send('Неверное имя аккаунта')

                elif response.component.label == "Изменить ваше имя":
                    user = self.cursor.execute("""select name from users
                                                  where ds_id = ?""", (str(ctx.author.id),)).fetchone()

                    if user is None:
                        await response.respond(content="Вы не зарегестрированы")

                    else:
                        await response.respond(content="Напишите желаемое имя или отмена")
                        msg2 = await self.bot.wait_for('message', check=lambda m: m.channel == ctx.channel and \
                                                                                  m.author.id == ctx.author.id)

                        if msg2.content.lower() == 'отмена':
                            await ctx.send('действие отмененно')
                        else:
                            await self.u_command.change_account(ctx, msg2.content)

                elif response.component.label == "Мой профиль":
                    name = self.cursor.execute("""select name from users
                                                               where ds_id = ?""", (str(ctx.author.id),)).fetchone()
                    if name is not None:
                        await response.respond(content="Сдесь вы можете посмотреть информацию о своём профиле")
                        await self.profile_information(ctx, name[0])
                    else:
                        await response.respond(content="Вы не зарегестрированы")

                elif response.component.label == "Инвентарь":
                    await response.respond(content="Это ваш инвентарь")
                    await self.inventory(ctx)

                elif response.component.label == "Хранилище покемонов":
                    await response.respond(content="Сдесь вы можете взаимодействовать с вашими покемонами")
                    await msg.delete()
                    await self.pokemon_storage(ctx)

                elif response.component.label == "Покедекс":
                    await response.respond(content="Сдесь вы можете посмотреть чего каких покемонов не хватает")
                    await self.pokedex(ctx)

                elif response.component.label == "Назад":
                    await response.respond(content="Выберите категорию")
                    await msg.delete()
                    await self.start(ctx)
                    break

    async def pokemon_storage(self, ctx):
        page, bag, msg0, msg1 = (0, [], '', '')
        msg11, pic, msg21, msg01, p_id = ('', '', '', '', 0)
        key = ''

        msg = await ctx.send(components=[[Button(style=ButtonStyle.grey, label="Список ваших покемонов", emoji='📃'),
                                          Button(style=ButtonStyle.green, label="Выбрать покемона", emoji='📌'),
                                          Button(style=ButtonStyle.blue, label="Проэволюционировать покемона",
                                                 emoji='🧬'),
                                          Button(style=ButtonStyle.grey, label="Назад", emoji='🔙')]
                                         ])

        while True:
            response = await self.bot.wait_for("button_click", check=lambda m: m.channel == ctx.channel and \
                                                                               m.author.id == ctx.author.id)
            if response.channel == ctx.channel:
                if response.component.label == "Список ваших покемонов":
                    await response.respond(content="Вот список всех ваших покемонов")
                    try:
                        page, bag, msg0, msg1 = await self.bag(ctx)
                        key = 'pokemon list'
                    except Exception:
                        pass

                elif response.component.label == "Вперёд" and key == 'pokemon list':
                    if page == math.ceil(len(bag) / 5):
                        await response.respond(content="=")
                        continue
                    await response.respond(content=">")
                    page += 1
                    await msg0.delete()
                    await msg1.delete()
                    msg0 = await ctx.send(await self.get_page(ctx, page))
                    msg1 = await ctx.send(components=[[Button(style=ButtonStyle.grey, label="Назад", emoji='◀'),
                                                       Button(style=ButtonStyle.grey, label="Вперёд", emoji='▶')
                                                       ]])

                elif response.component.label == "Назад" and response.component.emoji.name == '◀' and \
                        key == 'pokemon list':
                    if page == 1:
                        await response.respond(content="=")
                        continue
                    await response.respond(content="<")
                    page -= 1
                    await msg0.delete()
                    await msg1.delete()
                    msg0 = await ctx.send(await self.get_page(ctx, page))
                    msg1 = await ctx.send(components=[[Button(style=ButtonStyle.grey, label="Назад", emoji='◀'),
                                                       Button(style=ButtonStyle.grey, label="Вперёд", emoji='▶')
                                                       ]])

                elif response.component.label == "Вперёд" and key == 'choose pokemon':
                    if int(p_id) >= len(self.get_bag(ctx)):
                        await response.respond(content="=")
                        continue
                    await response.respond(content=">")
                    p_id = str(int(p_id) + 1)
                    await msg11.delete()
                    await pic.delete()
                    await msg21.delete()
                    await msg01.delete()
                    msg11, pic, msg21, msg01 = await self.choose(ctx, p_id)

                elif response.component.label == "Назад" and response.component.emoji.name == '◀' and \
                        key == 'choose pokemon':
                    if int(p_id) == 1:
                        await response.respond(content="=")
                        continue
                    await response.respond(content="<")
                    p_id = str(int(p_id) - 1)
                    await msg11.delete()
                    await pic.delete()
                    await msg21.delete()
                    await msg01.delete()
                    msg11, pic, msg21, msg01 = await self.choose(ctx, p_id)

                elif response.component.label == "Выбрать покемона":
                    await response.respond(content="Напишите порядковый номер нужного покемона или отмена")
                    msg2 = await self.bot.wait_for('message', check=lambda m: m.channel == ctx.channel and \
                                                                              m.author.id == ctx.author.id)
                    if msg2.content.lower() == 'отмена':
                        await ctx.send('действие отмененно')
                    else:
                        try:
                            msg11, pic, msg21, msg01 = await self.choose(ctx, msg2.content)
                            if msg11 is not None:
                                key = 'choose pokemon'
                                p_id = msg2.content
                        except Exception:
                            pass

                elif response.component.label == "Проэволюционировать покемона":
                    await response.respond(content="Напишите порядковый номер нужного покемона или отмена")
                    msg2 = await self.bot.wait_for('message', check=lambda m: m.channel == ctx.channel and \
                                                                              m.author.id == ctx.author.id)
                    if msg2.content.lower() == 'отмена':
                        await ctx.send('действие отмененно')
                    else:
                        await self.evolution(ctx, msg2.content)

                elif response.component.label == "Назад":
                    await response.respond(content="Можете выбрать действие, связанное с вашим профилем")
                    await msg.delete()
                    await self.profile(ctx)
                    break

    async def journey(self, ctx):
        msg = await ctx.send(components=[[Button(style=ButtonStyle.blue, label="Перейти в другой биом", emoji='🚶‍♂️'),
                                          Button(style=ButtonStyle.grey, label="Все биомы", emoji='🗺'),
                                          Button(style=ButtonStyle.green, label="Искать покемонов", emoji='🔎'),
                                          Button(style=ButtonStyle.grey, label="Назад", emoji='🔙')]
                                         ])

        while True:
            response = await self.bot.wait_for("button_click", check=lambda m: m.channel == ctx.channel and \
                                                                               m.author.id == ctx.author.id)
            if response.channel == ctx.channel:
                if response.component.label == "Перейти в другой биом":
                    await response.respond(content="Выберите биом")
                    await self.choose_bio(ctx)

                elif response.component.label == "Все биомы":
                    await response.respond(content="Вот список всех биомов")
                    await self.bios(ctx)

                elif response.component.label == "Искать покемонов":
                    await response.respond(content="Теперь надо подождать")
                    await self.search(ctx)

                elif response.component.label == "Назад":
                    await response.respond(content="Выберите категорию")
                    await msg.delete()
                    await self.start(ctx)
                    break

    async def choose_bio(self, ctx):
        all_bios = self.cursor.execute("""select id, name from bios""").fetchall()
        bios = []

        for bio in all_bios:
            bios.append(Button(style=ButtonStyle.blue, label=bio[1]))
        bios.append(Button(style=ButtonStyle.grey, label="Назад", emoji="🔝"))

        msgs = []
        st = []
        for bio in bios:
            st.append(bio)
            if len(st) == 5:
                msgs.append(await ctx.send(components=[st]))
                st = []
        if st:
            msgs.append(await ctx.send(components=[st]))

        while True:
            response2 = await self.bot.wait_for("button_click", check=lambda m: m.channel == ctx.channel and \
                                                                                m.author.id == ctx.author.id)

            if response2.component.label == "Назад" and response2.component.emoji.name == "🔝":
                await response2.respond(content="Выберите действие")
                for msg in msgs:
                    await msg.delete()
                break

            elif response2.component.label in list(map(lambda x: x[1], all_bios)):
                await response2.respond(content=f"Вы идёте в биом {response2.component.label}")
                for msg in msgs:
                    await msg.delete()
                await self.move_over(ctx, str(list(map(lambda x: x[1], all_bios)).index(response2.component.label) + 1))
                break

    async def different(self, ctx):
        msg = await ctx.send(components=[[Button(style=ButtonStyle.green, label="Забрать подарок", emoji='🎁'),
                                          Button(style=ButtonStyle.grey, label="Назад", emoji='🔙')]
                                         ])

        while True:
            response = await self.bot.wait_for("button_click", check=lambda m: m.channel == ctx.channel and \
                                                                               m.author.id == ctx.author.id)
            if response.channel == ctx.channel:
                if response.component.label == "Забрать подарок":
                    await response.respond(content="Вы просите подарок")
                    await self.get_gift(ctx)

                elif response.component.label == "Назад":
                    await response.respond(content="Выберите категорию")
                    await msg.delete()
                    await self.start(ctx)
                    break

    async def training(self, ctx):
        msg = await ctx.send(components=[[Button(style=ButtonStyle.green, label="Начать тренировку с покемоном",
                                                 emoji='🎯'),
                                          Button(style=ButtonStyle.red, label="Закончить тренировку с покемоном",
                                                 emoji='✋'),
                                          Button(style=ButtonStyle.grey, label="Назад", emoji='🔙')]
                                         ])

        while True:
            response = await self.bot.wait_for("button_click", check=lambda m: m.channel == ctx.channel and \
                                                                               m.author.id == ctx.author.id)
            if response.channel == ctx.channel:
                if response.component.label == "Начать тренировку с покемоном":
                    await response.respond(content="Напишите порядковый номер покемона для тренировки или отмена")
                    msg2 = await self.bot.wait_for('message', check=lambda m: m.channel == ctx.channel and \
                                                                              m.author.id == ctx.author.id)
                    if msg2.content.lower() == 'отмена':
                        await ctx.send('действие отмененно')
                    else:
                        await self.start_train(ctx, msg2.content)

                elif response.component.label == "Закончить тренировку с покемоном":
                    await response.respond(content="Вы решаете закончить тренировку с вашим покемоном")
                    await self.stop_train(ctx)

                elif response.component.label == "Назад":
                    await response.respond(content="Выберите категорию")
                    await msg.delete()
                    await self.start(ctx)
                    break

    @commands.command(name='bios')
    async def bios(self, ctx):
        msg = ''
        user_bio_id = self.get_bio_id(ctx)

        for bio_id in range(1, len(self.map) + 1):
            str_bio_id = str(bio_id)
            if len(str_bio_id) == 1:
                str_bio_id += '-'
            bio = self.cursor.execute("""select name from bios
                                         where id = ?""", (str(bio_id),)).fetchone()[0]

            result = self.cursor.execute(f"""select name from pokemons
                                             where bio_id like '%{str_bio_id}%'""").fetchall()
            if user_bio_id == bio_id:
                msg += f'***{bio_id}| Название {bio} Покемоны*** ||{", ".join(list(map(lambda x: x[0], result)))}||\n'
            else:
                msg += f'{bio_id}| **Название** {bio} **Покемоны** ||{", ".join(list(map(lambda x: x[0], result)))}||\n'
        await ctx.send(msg)

    @commands.command(name='profile_information')
    async def profile_information(self, ctx, name):
        info = self.get_information(ctx)
        await ctx.send(f"**----- Тренер {name} -----**\n"
                       f"- *Пойманно покемонов* {info['Catch']}\n"
                       f"- *Эволюционировано покемонов* {info['Evolved']}\n"
                       f"- *Уровень* {info['Level']}\n"
                       f"- *Общий опыт* {info['Total_experience']}/{info['Level'] * 5}\n")

    async def pokedex(self, ctx):
        pass

    @commands.command(name='inventory')
    async def inventory(self, ctx):
        if self.cursor.execute("""select name from users
                                  where ds_id = ?""", (str(ctx.author.id),)).fetchone() is None:
            await ctx.send('сначала зарегестрируйиесь')
            return

        inventory = self.get_inventory(ctx)

        if set(inventory.values()) == {0} or set(inventory.values()) == set():
            await ctx.send('У вас пусто в инвентаре, ждите бесплатных подарков')
            return

        msg = '-------------------\n'
        for key, val in inventory.items():
            if val != 0:
                k = self.cursor.execute("""select k from items
                                           where name = ?""", (str(key),)).fetchone()[0]
                msg += f'**Название** {key} **Число** {val} **Коэффициент** {k}\n' \
                       f'-------------------\n'
        await ctx.send(msg)

    @commands.command(name='get_gift')
    async def get_gift(self, ctx):
        if self.cursor.execute("""select name from users
                                  where ds_id = ?""", (str(ctx.author.id),)).fetchone() is None:
            await ctx.send('сначала зарегестрируйиесь')
            return

        now = datetime.now()
        if now - self.giveaway.get(ctx.author.id, now) > timedelta(hours=2) or \
                now - self.giveaway.get(ctx.author.id, now) == timedelta(seconds=0):
            self.giveaway[ctx.author.id] = now
            result = self.cursor.execute("""select id, rare from items""").fetchall()
            items_chances_st = []
            for x in result:
                items_chances_st.extend([x[0]] * x[1])

            chosen_item_id = random.choices(items_chances_st, k=random.randint(1, 5))
            items = [self.cursor.execute("""select name from items where id = ?""", (str(x),)).fetchone()[0]
                     for x in chosen_item_id]

            inventory = self.get_inventory(ctx)
            for item in items:
                inventory[item] = inventory.get(item, 0) + 1
            self.change_inventory(ctx, inventory)

            await ctx.send(f'**вы получили: {", ".join(items)}**')
        else:
            left = ":".join(
                (str(timedelta(hours=2) - (datetime.now() - self.giveaway.get(ctx.author.id)))).split(".")[:-1]
            )
            await ctx.send(f'вы недавно получали свой подарок, подождите ещё {left}')

    async def get_page(self, ctx, page):
        bag = self.get_pokemons(ctx)

        msg = f'---------------------------------\n'
        for i, p in enumerate(bag[(page - 1) * 5:page * 5]):
            p = Pokemon(*p)
            if p.sh:
                msg += f'***✨Шайни✨***\n'
            msg += f'{p.get_emoji()} {i + ((page - 1) * 5) + 1}| **Имя** {p.name} **Тип** {", ".join(p.types_st)}' \
                   f' **Сила** {p.cp}\n' \
                   f'**Уровень** {p.lv} **Опыт** {p.ex}/{p.lv * 5}\n' \
                   f'---------------------------------\n'
        return msg

    @commands.command(name='bag')
    async def bag(self, ctx):
        if self.cursor.execute("""select name from users
                                  where ds_id = ?""", (str(ctx.author.id),)).fetchone() is None:
            await ctx.send('сначала зарегестрируйиесь')
            return

        bag = self.get_pokemons(ctx)

        if not bag:
            await ctx.send('У вас пока что нет покемонов, скорее отправляйтесь на охоту')
            return

        page = 1

        msg0 = await ctx.send(await self.get_page(ctx, page))
        msg1 = await ctx.send(components=[[Button(style=ButtonStyle.grey, label="Назад", emoji='◀'),
                                           Button(style=ButtonStyle.grey, label="Вперёд", emoji='▶')
                                           ]])

        return page, bag, msg0, msg1

    @commands.command(name='choose')
    async def choose(self, ctx, pokemon_id=None):
        if self.cursor.execute("""select name from users
                                  where ds_id = ?""", (str(ctx.author.id),)).fetchone() is None:
            await ctx.send('сначала зарегестрируйиесь')
            return
        if self.get_action(ctx) == 'train':
            await ctx.send('вы сейчас тренеруетесь, можете закончить тренировку командой stop_train')
            return
        if self.get_action(ctx) != 'default':
            await ctx.send('вы сейчас ловите покемона, если захотите, можете в любой момент уйти командой leave')
            return

        if pokemon_id is None:
            await ctx.send('вместе с командой следует написать id покемона из вашей сумки')
            return

        try:
            p = self.get_pokemons(ctx)[int(pokemon_id) - 1]
            p = Pokemon(*p)

            msg1 = f'---------------------------------------------\n'
            if p.sh == 1:
                msg1 += f'***✨Шайни✨***\n'
            msg1 += f'**{p.name}||Пойманный Покéмон**\n'
            msg1 = await ctx.send(msg1)
            pic = await ctx.send(p.get_img())
            msg2 = await ctx.send(f'**Имя** {p.name}\n'
                                  f'**Тип** {", ".join(p.types_st)}\n'
                                  f'**Сила** {p.cp}\n'
                                  f'**Атака** {p.at} **Здоровье** {p.hp}'
                                  f' **Защита** {p.de}\n'
                                  f'**Уровень** {p.lv} **Опыт** {p.ex}/{p.lv * 5}\n'
                                  f'---------------------------------------------\n')
            msg0 = await ctx.send(components=[[Button(style=ButtonStyle.grey, label="Назад", emoji='◀'),
                                               Button(style=ButtonStyle.grey, label="Вперёд", emoji='▶')
                                               ]])
            return msg1, pic, msg2, msg0

        except Exception:
            await ctx.send('такого id покемона не существует')
            return None, None, None, None

    @commands.command(name='evolution')
    async def evolution(self, ctx, pokemon_id=None):
        if self.cursor.execute("""select name from users
                                  where ds_id = ?""", (str(ctx.author.id),)).fetchone() is None:
            await ctx.send('сначала зарегестрируйиесь')
            return
        if self.get_action(ctx) == 'train':
            await ctx.send('вы сейчас тренеруетесь, можете закончить тренировку командой stop_train')
            return
        if self.get_action(ctx) != 'default':
            await ctx.send('вы сейчас ловите покемона, если захотите, можете в любой момент уйти командой leave')
            return

        if pokemon_id is None:
            await ctx.send('вместе с командой следует написать id покемона из вашей сумки')
            return

        try:
            p = self.get_pokemons(ctx)[int(pokemon_id) - 1]
            p = Pokemon(*p)
            if p.ev is None:
                await ctx.send('Выбранный покемон не имеет следуещей формы')
                return
            if p.lv >= p.ev:
                p.evolution()

                info = self.get_information(ctx)
                info['Evolved'] += 1
                self.change_information(ctx, info)

                await ctx.send(
                    f'**Ничего себе, твой покемон эволюционировал, теперь это {p.name}, поздравляю!!!**')

                bag = self.get_pokemons(ctx)
                bag[int(pokemon_id) - 1] = eval(p.get())
                bag = ''.join(list(map(lambda x: str(x), bag)))
                self.change_bag(ctx, bag)
            else:
                await ctx.send(f'Сожалею, но твой покемон сможет эволюционировать только на {p.ev} уровне')

        except Exception:
            await ctx.send('такого id покемона не существует')

    @commands.command(name='start_train')
    async def start_train(self, ctx, pokemon_id=None):
        if self.cursor.execute("""select name from users
                                  where ds_id = ?""", (str(ctx.author.id),)).fetchone() is None:
            await ctx.send('сначала зарегестрируйиесь')
            return
        if self.get_action(ctx) != 'default' and self.get_action(ctx) != 'train':
            await ctx.send('вы сейчас ловите покемона, если захотите, можете в любой момент уйти командой leave')
            return
        if pokemon_id is None:
            await ctx.send('вместе с командой следует написать id покемона из вашей сумки')
            return

        if self.get_action(ctx) != 'train':
            try:
                bag = self.get_pokemons(ctx)
                p = bag[int(pokemon_id) - 1]
                p = Pokemon(*p)
                await ctx.send(f'**тренировка с покемоном {p.name} началась**')
                self.change_action(ctx, 'train')
                self.trains[ctx.author.id] = {'datetime': datetime.now(), 'pokemon_id': pokemon_id, 'ctx': ctx}

            except Exception:
                await ctx.send('такого id покемона не существует')

        else:
            pokemons = self.get_pokemons(ctx)
            in_training_pokemon_id = int(self.trains[ctx.author.id]['pokemon_id'])
            left = ":".join(
                (str(timedelta(seconds=0) -
                     (datetime.now() - self.trains[ctx.author.id]['datetime'])).split(".")[:-1])
            )
            await ctx.send(f"Вы уже тренируетесь с покемоном "
                           f"{pokemons[in_training_pokemon_id - 1][1]}, "
                           f"осталось {left}")

    @commands.command(name='stop_train')
    async def stop_train(self, ctx):
        if self.cursor.execute("""select name from users
                                  where ds_id = ?""", (str(ctx.author.id),)).fetchone() is None:
            await ctx.send('сначала зарегестрируйиесь')
            return
        if self.get_action(ctx) == 'train':
            self.change_action(ctx, 'default')
            del self.trains[ctx.author.id]
        else:
            await ctx.send('вы итак не тренировались')

    @commands.command(name='search')
    async def search(self, ctx):
        if self.cursor.execute("""select name from users
                                  where ds_id = ?""", (str(ctx.author.id),)).fetchone() is None:
            await ctx.send('сначала зарегестрируйиесь')
            return
        if self.get_action(ctx) == 'train':
            await ctx.send('вы сейчас тренеруетесь, можете закончить тренировку командой stop_train')
            return
        if self.get_action(ctx) != 'default':
            await ctx.send('вы сейчас ловите покемона, если захотите, можете в любой момент уйти командой leave')
            return

        bio_id = self.cursor.execute("""select bio_id from users
                                        where ds_id = ?""", (str(ctx.author.id),)).fetchone()[0]
        if bio_id is None:
            await ctx.send('Сначала зарегистрируйтесь')
            return

        t0 = random.randint(5, 15)
        msg = await ctx.send(f'Вы отпраляетесь в путь, осталось {t0} секунд')
        for t in range(t0 - 1, 0, -1):
            await sleep(1)
            await msg.edit(content=f'Вы отпраляетесь в путь, осталось {t} секунд')
        await msg.delete()

        await ctx.send('Вы что-то заметили')
        await sleep(0.4)

        found_pokemon = self.map[bio_id - 1][random.randint(0, len(self.map[bio_id - 1]) - 1)]
        if found_pokemon is None:
            await ctx.send('**Показалось**')
            return

        await ctx.send(f'**Да это же {found_pokemon.name}**')
        if found_pokemon.sh == 1:
            await ctx.send(f'***✨Шайни✨***')
        await ctx.send('---------------------------------------------')
        await ctx.send(f'**{found_pokemon.name}||Дикий Покéмон**')
        if self.is_weather_boost(*found_pokemon.type.split(',')):
            found_pokemon.lv += random.randint(1, 5)
            await ctx.send(f'***💪Погодное услиление💪***')
        await ctx.send(found_pokemon.get_img())
        await ctx.send(f'**Имя** {found_pokemon.name}\n'
                       f'**Тип** {", ".join(found_pokemon.types_st)}\n'
                       f'**Сила** {found_pokemon.cp} **Уровень** {found_pokemon.lv}\n'
                       f'||**Атака** {found_pokemon.at} **Здоровье** {found_pokemon.hp}'
                       f' **Защита** {found_pokemon.de}||')
        await ctx.send('---------------------------------------------')

        key = random.randint(1000, 9999)
        while key in self.actions:
            key = random.randint(1000, 9999)

        self.change_action(ctx, key)
        self.actions[key] = [found_pokemon, bio_id]

        await ctx.send(components=[[Button(style=ButtonStyle.blue, label="Поймать", emoji='👏'),
                                    Button(style=ButtonStyle.green, label="Покормить", emoji='🍇'),
                                    Button(style=ButtonStyle.grey, label="Инвентарь", emoji='🎒'),
                                    Button(style=ButtonStyle.red, label="Уйти", emoji='🏃‍♂️')]])

        while self.actions[key] == [found_pokemon, bio_id]:
            response = await self.bot.wait_for("button_click", check=lambda m: m.channel == ctx.channel and \
                                                                               m.author.id == ctx.author.id)
            if response.channel == ctx.channel:
                if response.component.label == "Поймать":
                    await response.respond(content="Выберите вид бола")
                    is_catch_or_run_away = await self.choose_ball(ctx, (key, found_pokemon, bio_id))
                    if is_catch_or_run_away:
                        await self.journey(ctx)

                elif response.component.label == "Покормить":
                    await response.respond(content="Выберите вид ягоды")
                    await self.choose_berry(ctx, (key, found_pokemon, bio_id))

                elif response.component.label == "Инвентарь":
                    await response.respond(content="Это ваш инвентарь")
                    await self.inventory(ctx)

                elif response.component.label == "Уйти":
                    await response.respond(content='Вы выбрали действие "уйти"')
                    await self.leave(ctx)
                    await self.journey(ctx)

    async def choose_ball(self, ctx, info):
        key, found_pokemon, bio_id = info

        inventory = self.get_inventory(ctx)
        pokeballs = []

        for key1, value in inventory.items():
            if value == 0 or self.cursor.execute("""select type from items
                                                    where name = ?""", (str(key1),)).fetchone()[0] != 1:
                continue
            pokeballs.append(Button(style=ButtonStyle.blue, label=key1))
        pokeballs.append(Button(style=ButtonStyle.grey, label="Назад", emoji="🔝"))

        msg = await ctx.send(components=[pokeballs])
        while self.actions[key] == [found_pokemon, bio_id]:
            response2 = await self.bot.wait_for("button_click", check=lambda m: m.channel == ctx.channel and \
                                                                                m.author.id == ctx.author.id)
            if response2.component.label == "Назад":
                await response2.respond(content="Выберите действие")
                await msg.delete()
                return 0
            elif 'ball' in response2.component.label:
                await response2.respond(content=f"Вы кидаете {response2.component.label}")
                catch = await self.catch(ctx, response2.component.label)
                if catch:
                    return 1

    async def choose_berry(self, ctx, info):
        key, found_pokemon, bio_id = info
        inventory = self.get_inventory(ctx)
        berries = []

        for key1, value in inventory.items():
            if value == 0 or self.cursor.execute("""select type from items
                                                    where name = ?""", (str(key1),)).fetchone()[0] != 2:
                continue
            berries.append(Button(style=ButtonStyle.blue, label=key1))
        berries.append(Button(style=ButtonStyle.grey, label="Назад", emoji="🔝"))

        msg = await ctx.send(components=[berries])
        while self.actions[key] == [found_pokemon, bio_id]:
            response2 = await self.bot.wait_for("button_click", check=lambda m: m.channel == ctx.channel and \
                                                                                m.author.id == ctx.author.id)
            if response2.component.label == "Назад":
                await response2.respond(content="Выберите действие")
                await msg.delete()
                break
            elif 'berry' in response2.component.label:
                await response2.respond(content=f"Вы используете {response2.component.label}")
                await self.feed(ctx, response2.component.label)
                await msg.delete()
                break

    @commands.command(name='move_over')
    async def move_over(self, ctx, new_bio=None):
        if self.cursor.execute("""select name from users
                                  where ds_id = ?""", (str(ctx.author.id),)).fetchone() is None:
            await ctx.send('сначала зарегестрируйиесь')
            return
        if self.get_action(ctx) == 'train':
            await ctx.send('вы сейчас тренеруетесь, можете закончить тренировку командой stop_train')
            return
        if self.get_action(ctx) != 'default':
            await ctx.send('вы сейчас ловите покемона, если захотите, можете в любой момент уйти командой leave')
            return

        bio_id = self.cursor.execute("""select bio_id from users
                                        where ds_id = ?""", (str(ctx.author.id),)).fetchone()[0]
        if bio_id is None:
            await ctx.send('Сначала зарегистрируйтесь')
            return

        try:
            found_bio = self.cursor.execute("""select name from bios
                                                where id = ?""", (new_bio,)).fetchone()
            if found_bio is not None:
                if bio_id != int(new_bio):

                    t0 = random.randint(15, 25)
                    await sleep(1)
                    msg = await ctx.send(f'Вы отпраляетесь в путь, осталось {t0} секунд')
                    for t in range(t0 - 1, 0, -1):
                        await sleep(1)
                        await msg.edit(content=f'Вы отпраляетесь в путь, осталось {t} секунд')
                    await msg.delete()
                    await ctx.send(f'**Вы дошли до биома {found_bio[0]}**')

                    bio_id = int(new_bio)
                    self.cursor.execute(f"""update users
                                            set bio_id = '{bio_id}'
                                            where ds_id = ?""", (str(ctx.author.id),))

                else:
                    await ctx.send(f'Вы и так в этом биоме')
            else:
                await ctx.send('Вы ввели несуществующий ID, проверьте всё ещё раз')

        except Exception:
            await ctx.send('Похоже вы неверно поняли эту команду, введите вместе с ней номер биома')

    @commands.command(name='catch')
    async def catch(self, ctx, pokeball='Pokeball'):
        pokeball = pokeball.capitalize()
        if self.cursor.execute("""select name from users
                                  where ds_id = ?""", (str(ctx.author.id),)).fetchone() is None:
            await ctx.send('сначала зарегестрируйиесь')
            return
        if self.get_action(ctx) == 'default' or self.get_action(ctx) == 'train':
            await ctx.send('вы сейчас не ловите покемона')
            return

        inventory = self.get_inventory(ctx)

        try:
            type = self.cursor.execute("""select type from items
                                          where name = ?""", (str(pokeball),)).fetchone()[0]

            if type != 1:
                await ctx.send('Выбранный предмет не является шаром')
                return

            if pokeball.capitalize() in inventory:
                if inventory[pokeball] > 0:
                    await ctx.send(f'вы кидаете {pokeball}')
                    inventory[pokeball] = inventory[pokeball] - 1
                    self.change_inventory(ctx, inventory)
                    p = self.actions[self.get_action(ctx)][0]
                    self.actions[self.get_action(ctx)][0].ca = int(p.ca * self.cursor.execute("""select k from items 
                                                   where name = ?""", (str(pokeball),)).fetchone()[0])

                    bio_id = self.cursor.execute("""select bio_id from users
                                          where ds_id = ?""", (str(ctx.author.id),)).fetchone()[0]

                    if random.randint(1, 100) <= p.ca:
                        await ctx.send(f'**{p.name} был успешно пойман!**')

                        info = self.get_information(ctx)
                        info["Catch"] += 1
                        self.change_information(ctx, info)

                        self.map[bio_id - 1][self.actions[self.get_action(ctx)][1]] = None
                        self.update_map()
                        self.change_bag(ctx, self.get_bag(ctx) + str(p.get()))
                        self.change_action(ctx, 'default')
                        return 1

                    elif random.randint(1, 100) <= p.fl:
                        await ctx.send(f'**{p.name} сбежал!**')
                        self.map[bio_id - 1][self.actions[self.get_action(ctx)][1]] = None
                        self.update_map()
                        self.change_action(ctx, 'default')
                        return 1

                    else:
                        await ctx.send(f'**{p.name} выбрался из покебола!**')
                        p.fl, p.ca = self.cursor.execute("""select fl, ca from pokemons 
                                                            where id = ?""", (str(p.id),)).fetchone()

                else:
                    await ctx.send('У вас в инвентаре нету такого предмета')
                    return
            else:
                await ctx.send('У вас в инвентаре нету такого предмета')
                return

        except Exception:
            await ctx.send('К сожалению такого предмета пока что не существует')
            return

    @commands.command(name='feed')
    async def feed(self, ctx, *berry):
        berry = ' '.join(list(berry)).capitalize()
        if berry == '':
            berry = 'Nanab berry'
        if self.cursor.execute("""select name from users
                                  where ds_id = ?""", (str(ctx.author.id),)).fetchone() is None:
            await ctx.send('сначала зарегестрируйиесь')
            return
        if self.get_action(ctx) == 'default' or self.get_action(ctx) == 'train':
            await ctx.send('вы сейчас не ловите покемона')
            return

        inventory = self.get_inventory(ctx)

        try:
            type = self.cursor.execute("""select type from items
                                                  where name = ?""", (str(berry),)).fetchone()[0]

            if type != 2:
                await ctx.send('Выбранный предмет не является ягодой')
                return

            p = self.actions[self.get_action(ctx)][0]

            if p.ca > self.cursor.execute("""select ca from pokemons where id = ?""", (str(p.id),)).fetchone()[0]:
                await ctx.send("Вы уже давали этому покемону ягоду")
                return

            if berry in inventory:
                if inventory[berry] > 0:
                    await ctx.send(f'вы подкармливаете покемона с помощью {berry}')
                    inventory[berry] = inventory[berry] - 1
                    self.change_inventory(ctx, inventory)

                    p.ca *= self.cursor.execute("""select k from items where name = ?""", (str(berry),)).fetchone()[0]

                else:
                    await ctx.send('У вас в инвентаре нету такого предмета')
                    return
            else:
                await ctx.send('У вас в инвентаре нету такого предмета')
                return

        except Exception:
            await ctx.send('К сожалению такого предмета пока что не существует')
            return

    @commands.command(name='leave')
    async def leave(self, ctx):
        if self.cursor.execute("""select name from users
                                  where ds_id = ?""", (str(ctx.author.id),)).fetchone() is None:
            await ctx.send('сначала зарегестрируйиесь')
            return
        if self.get_action(ctx) == 'default' or self.get_action(ctx) == 'train':
            await ctx.send('вы сейчас не ловите покемона')
            return

        await ctx.send(f'Вы прошли мимо {self.actions[self.get_action(ctx)][0].name}')
        del self.actions[self.get_action(ctx)]
        self.change_action(ctx, 'default')
