import asyncio
import random
from discord.ext import commands
from googletrans import Translator
from discord import default_permissions
import discord

deltime = 5


class misc(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('misc active')

    @commands.slash_command(name="embed", description="Creates embed message.")
    @default_permissions(manage_messages=True)
    async def embed(self, ctx, title: str = None, description: str = None, foot: str = None):
        await ctx.respond("Creating embed", delete_after=1)
        embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
        # embed.add_field(name="field 1", value="test", inline=False)
        if foot is not None:
            embed.set_footer(text=foot)
        await ctx.send(embed=embed)

    @commands.slash_command(name="translate", description='Translates text.')
    async def translate(self, ctx, message: str, lang: str = "en"):
        trans = Translator()
        trans = trans.translate(message, dest=lang)
        await ctx.respond(f'Translated from [{trans.src}] to [{trans.dest}] by {ctx.author}: {trans.text}')

    @commands.slash_command(name="ping", description='Shows current ping in miliseconds.')
    async def ping(self, ctx):
        latency = int(self.client.latency * 1000)
        await ctx.respond(f'Pong! {latency} ms')

    @commands.slash_command(name="say", description='Allows you to say something in the name of the bot.')
    @default_permissions(manage_messages=True)
    async def say(self, ctx, msg: str):
        await ctx.respond("Starting...", delete_after=1)
        await ctx.channel.send(msg)

    @commands.slash_command(name="countdown", description="Counts down.")
    @default_permissions(manage_messages=True)
    async def countdown(self, ctx, amount: int, delay: int = 1, end_point: int = 0):
        while amount >= end_point:
            if amount < 0:
                await ctx.respond("I don't count in negatives.")
                break
            if float(delay - self.client.latency) >= 0:
                await asyncio.sleep(float(delay - self.client.latency))
            if amount > end_point + 1000 and 0 == amount % 1000:
                await ctx.respond(amount)
            elif end_point + 100 < amount <= end_point + 1000 and 0 == amount % 100:
                await ctx.respond(amount)
            elif end_point + 10 < amount <= end_point + 100 and 0 == amount % 10:
                await ctx.respond(amount)
            elif amount <= end_point + 10:
                await ctx.respond(amount)
            print(amount)
            amount = amount - 1
        if end_point > amount + 1:
            await ctx.respond(
                f"I won't count that. If you want to count up use: count {end_point} {delay} {amount}")

    @commands.slash_command(name="count", description="Counts up.")
    @default_permissions(manage_messages=True)
    async def count(self, ctx, amount: int, delay: int = 1, start_point: int = 0):
        limit = 20
        if start_point + limit < amount:
            print(ctx)
            await ctx.respond(f"The limit is set to {limit}")
        else:
            while start_point <= amount:
                if float(delay - self.client.latency) >= 0:
                    await asyncio.sleep(float(delay - self.client.latency))
                await ctx.respond(start_point)
                print(start_point)
                start_point = start_point + 1
            if start_point > amount + 1:
                await ctx.respond(
                    f"I won't count that. If you want to count down use: countdown {start_point} {delay} {amount}")

    @commands.slash_command(name="random", description="Generates pseudo-random numbers")
    async def random(self, ctx, range_end: int, range_start: int = 0, amount: int = 1):
        limit = 10
        range_end -= range_start
        while amount > 0:
            if amount > limit:
                await ctx.respond(f'Limit is set to {limit}')
                break
            amount = amount - 1
            await ctx.respond(random.randrange(range_end) + range_start)

    @commands.slash_command(name="stats", description="shows channel statistics")
    async def channel_stats(self, ctx):
        await ctx.respond('# Starting counting', delete_after=deltime)
        channel = ctx.channel
        messages = await channel.history(limit=None).flatten()

        total_messages = len(messages)
        media_count = 0

        for message in messages:
            if message.attachments or message.embeds:
                media_count += 1

        await ctx.respond(f'# Messages: {total_messages - 1} files: {media_count}.', delete_after=60)


def setup(bot):
    bot.add_cog(misc(bot))
