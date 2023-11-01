import openai
import os
import disnake
import json
import config
from disnake.ext import commands
from typing import Optional

cnfg = open('cnfg.json','r')
cfg = json.load(cnfg)

bot = commands.Bot(config.PREFIX, intents=disnake.Intents.all())

openai.api_key = config.TOKEN_OPENAI
CENSORED_WORDS = config.CENS

@bot.event
async def on_ready():
    print(f'{bot.user} is ready')

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id == config.ROLE_ON_REACTION_MSG:
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = disnake.utils.get(message.guild.members, id=payload.user_id)
        emoji = str(payload.emoji)
        try:
            role = disnake.utils.get(message.guild.roles, id=config.ROLES_LIST[emoji])
            if len([i for i in user.roles if i.id not in config.USER_ROLES_LIST]) <= config.MAX_ROLES:
                    await user.add_roles(role)
            else:
                await message.remove_reaction(payload.emoji, user)
        except Exception as _ex:
            print(repr(_ex))

@bot.event
async def on_raw_reaction_remove(payload):
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = disnake.utils.get(message.guild.members, id=payload.user_id)
    try:
        emoji = str(payload.emoji)
        role = disnake.utils.get(message.guild.roles, id=config.ROLES_LIST[emoji])
        await user.remove_roles(role)
    except Exception as _ex:
        print(repr(_ex))

@bot.event
async def on_member_join(member):
    role = disnake.utils.get(member.guild.roles, name=config.ROLE_ON_JOIN)
    await member.add_roles(role)

class Confirm(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=60.0)
        self.value = Optional[bool]

    @disnake.ui.button(label='Sanctum builds', style=disnake.ButtonStyle.red)
    async def confirm(self, button: disnake.ui.button, inter: disnake.MessageInteraction):
        view = Sanctum()
        await inter.response.send_message('Билды под санктум:', view=view, delete_after=config.MSG_DEL_TIME)

    @disnake.ui.button(label='MF builds', style=disnake.ButtonStyle.blurple)
    async def cancel(self, button: disnake.ui.button, inter: disnake.MessageInteraction):
        view = MF()
        await inter.response.send_message('MF билды:', view=view, delete_after=config.MSG_DEL_TIME)

class Sanctum(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=60.0)
        self.value = Optional[bool]
   
    @disnake.ui.button(label='Icicle mine', style=disnake.ButtonStyle.blurple)
    async def confirm(self, button: disnake.ui.button, inter: disnake.MessageInteraction):
        await inter.response.send_message(config.pob1, delete_after=config.MSG_DEL_TIME)

    @disnake.ui.button(label='Shockwave totems', style=disnake.ButtonStyle.blurple)
    async def cancel(self, button: disnake.ui.button, inter: disnake.MessageInteraction):
        await inter.response.send_message(config.pob2, delete_after=config.MSG_DEL_TIME)

class MF(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=60.0)
        self.value = Optional[bool]
   
    @disnake.ui.button(label='BV', style=disnake.ButtonStyle.blurple)
    async def confirm(self, button: disnake.ui.button, inter: disnake.MessageInteraction):
        await inter.response.send_message('поба бв', delete_after=config.MSG_DEL_TIME)

    @disnake.ui.button(label='TS', style=disnake.ButtonStyle.blurple)
    async def cancel(self, button: disnake.ui.button, inter: disnake.MessageInteraction):
        await inter.response.send_message(config.pob4, delete_after=config.MSG_DEL_TIME)

@bot.command(name='pob')
async def ask_pob(ctx):
    channel = bot.get_channel(config.POB_CHANNEL)
    view = Confirm()
    message = await channel.send(f'{ctx.author.mention} Выбери интересующий билд', view=view, delete_after=config.MSG_DEL_TIME)

    await view.wait()
    if view.value is None:
        await message.edit(content='время выбора истекло')

@bot.command(name="clear")
async def clear(ctx, amount: int):
    if not ctx.author.guild_permissions.administrator :
        embed = disnake.Embed(description=f'❌ {ctx.author.mention} Команду может использовать только модерация!', color=0xc80005)
        return await ctx.send(embed=embed, delete_after=config.MSG_DEL_TIME)
    else:
        await ctx.channel.purge(limit=amount+1)
        embed = disnake.Embed(
        description=f"{ctx.author.mention}  {amount} messages deleted")
        await ctx.send(embed=embed, delete_after=config.MSG_DEL_TIME)

@bot.event
async def on_message(message: disnake.Message):
    if not message.author.bot:
        await bot.process_commands(message)
        for censored_word in CENSORED_WORDS:
            if censored_word in message.content:
                await message.delete()
                await message.channel.send(f"{message.author.mention} без обсуждения политики", delete_after=config.MSG_DEL_TIME)
                return

        if not message.content.startswith(cfg['prefix']):
            if bot.user.mentioned_in(message):
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    max_tokens=1500,
                    temperature=0.7,
                    messages=[{'role': 'user', 'content': message.content}]
                )
                response_txt = response['choices'][0]['message']['content']
                if len(response_txt) > 2000:
                    with open("Ответ.txt", "w") as file:
                        file.write(response_txt)
                    await message.reply("Ответ содержит больше 2000 символов, поэтому я поместил его в файл, вот он:", file=disnake.File("Ответ.txt"))
                    os.unlink("Ответ.txt")
                else:
                    await message.reply(response['choices'][0]['message']['content'])

bot.run(config.TOKEN_DS)