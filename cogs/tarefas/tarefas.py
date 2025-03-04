from discord.ext import commands, tasks
import datetime
from loaders.mongoconnect import mongoConnect
from loaders.get_json import get_json

config = get_json("config.json")

cluster = mongoConnect()
db = cluster['discord']
site = db['site']
logs = db['logs']

async def find_users():
    info = site.find_one({'_id': 0})
    staffs = info['staffs']
    boosters = info['boosters']
    return staffs, boosters

def get_updated_users(discord_users, db_users):
    updated_users = []

    for user in discord_users:

        db_user = {}
        
        for i in db_users:
            if user["id"] == i["id"]:
                db_user = i
                break
        
        if db_user:
            db_user.update(user)
            updated_users.append(db_user)
        else:
            user.update({
                'habilidades': ['Não Informado'],
                'bio': "Biografia Não Definida",
                'ocupacao': 'Ocupação não definida',
                'github': 'https://github.com/codify-community'
            })
            
            updated_users.append(user)
            
    return updated_users

class Tarefas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @tasks.loop(minutes=5)
        async def send_status():
            hr = datetime.datetime.now()
            logs.find_one_and_update({'_id': 0}, {'$set': {'last_ping': hr}})
        send_status.start()

        @tasks.loop(minutes=10)
        async def get_info(self):
            guild = self.bot.get_guild(config["guild"]["id"])
            #member quant
            member_count = int(guild.member_count)
            #channels quant
            channel_count = len(guild.channels)
            #staff quant

            db_staffs, db_boosters = await find_users()
            discord_staffs, discord_boosters = [], []

            for member in guild.members:
                if member.bot: continue

                for role in reversed(member.roles):

                    if role.id in config['guild']['roles']['staffs']:

                        user = await self.bot.fetch_user(member.id)

                        staff = {
                            'id': user.id,
                            'role': config['guild']['roles_name'][str(role.id)],
                            'name': user.name,
                            'pfp': str(user.avatar_url)
                        }

                        discord_staffs.append(staff)
                        break

                    elif role.id in config['guild']['roles']['boosters']:

                        user = await self.bot.fetch_user(member.id)

                        booster = {
                            'id': user.id,
                            'role': config['guild']['roles_name'][str(role.id)],
                            'name': user.name,
                            'pfp': str(user.avatar_url)
                        }
                        
                        discord_boosters.append(booster)
                        break
            
            updated_staffs = get_updated_users(discord_staffs, db_staffs)
            updated_boosters = get_updated_users(discord_boosters, db_boosters)
            
            # Fix
            site.find_one_and_update({'_id': 0}, {'$set': {'staffs': updated_staffs, 'boosters': updated_boosters, 'member_count': member_count, 'channel_count': channel_count, 'staff_count': len(updated_staffs)}})

        get_info.start(self)

def setup(bot):
    bot.add_cog(Tarefas(bot))
