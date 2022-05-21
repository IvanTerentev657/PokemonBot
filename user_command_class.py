import sqlite3

from discord.ext import commands

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.connection = sqlite3.connect('pokemon.db')
        self.cursor = self.connection.cursor()

    @commands.command(name='registration')
    async def registration(self, ctx, name):
        is_register = self.cursor.execute("""select id from users
                                             where ds_id = ?""", (str(ctx.author.id),)).fetchone()
        if is_register is not None:
            await ctx.send('Вы уже зарегистрированы, если хотите, можете изменить учётную запись или удалить её')
            return

        inventory = '{"Pokeball": 5}'
        information = '{"Catch": 0, "Evolved": 0, "Level": 1, "Total_experience": 0}'
        self.cursor.execute(f"""insert into users(ds_id, name, action, bio_id, inventory, information)
                                values('{ctx.author.id}', '{name}', 'default', 1, '{inventory}', '{information}')""")
        self.connection.commit()
        await ctx.send(f'Удачи, {name}, поймай их всех!')

    @commands.command(name='delete_account')
    async def delete_account(self, ctx):
        self.cursor.execute(f"""delete from users
                                where ds_id = ?""", (str(ctx.author.id),))
        self.connection.commit()
        await ctx.send('Надеюсь, вы вернётесь, прощай')

    @commands.command(name='change_account')
    async def change_account(self, ctx, name):
        self.cursor.execute(f"""update users
                                set name = '{name}'
                                where ds_id = ?""", (str(ctx.author.id),))
        self.connection.commit()
        await ctx.send(f'Теперь ты {name}, поздравляю')
