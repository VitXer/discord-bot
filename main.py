import datetime
import shutil
import time
from dotenv import load_dotenv
import discord
from discord.ext import commands
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='sudo ', intents=intents)

maintenance = os.getenv("MAINTENANCE")


def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')


@bot.event
async def on_ready():
    print('main active')
    print(f'Logged in as {bot.user.name}')
    print("Servers:")
    for guild in bot.guilds:
        print(f"- {guild.name}")

    try:
        shutil.rmtree(f'servers')
    except Exception as E:
        print(E)
    # load_cogs()



@bot.event
async def on_message(message):
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    server = message.guild.name if message.guild else "Direct Message"
    channel = message.channel.name if message.guild else "Direct Message"
    author = message.author.name
    log_message = f"<{st}> Server: {server} | Channel: {channel} | Author: {author} | Message: {message.content}"

    guild_dir = f"logs/{str(message.guild.id)}"
    os.makedirs(guild_dir, exist_ok=True)

    with open(f"{guild_dir}/{str(channel)}.txt", "a") as text_file:
        print(log_message, file=text_file)

    with open(f"logs.txt", "a") as text_file:
        print(log_message, file=text_file)

    print(log_message)

    await bot.process_commands(message)


@bot.slash_command()
@commands.is_owner()
async def load(ctx, extension: str):
    bot.load_extension(f'cogs.{extension}')
    await ctx.respond(f'Loaded {extension}')


@bot.slash_command()
@commands.is_owner()
async def unload(ctx, extension: str):
    bot.unload_extension(f'cogs.{extension}')
    await ctx.respond(f'Unloaded {extension}')


@bot.slash_command()
@commands.is_owner()
async def reload(ctx, extension: str):
    bot.reload_extension(f'cogs.{extension}')
    await ctx.respond(f'Reloaded {extension}')


if __name__ == '__main__':
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(TOKEN)
