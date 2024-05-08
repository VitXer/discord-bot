import discord
from discord.ext import commands
from discord import default_permissions

deltime = 5


class admin(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('admin active')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel is not None and after.channel != before.channel:

            with open("HELPCHANNELS.txt") as file:
                channels = [int(i) for i in file]

            with open("HELPROLES.txt") as file:
                roles = [int(i) for i in file]

            for channel, role in zip(channels, roles):
                if after.channel.id == channel:
                    guild = member.guild
                    role = guild.get_role(role)
                    if role is not None:
                        await after.channel.send(
                            f"{role.mention}, {member.display_name} has just joined <#{after.channel.id}>!")

    @commands.slash_command(name="waiting_room_add",
                            description="adds selected channel and selected role to autoping list")
    @commands.is_owner()
    async def waiting_room_add(self, ctx, channel: discord.VoiceChannel, role: discord.Role):

        with open("HELPCHANNELS.txt", "a") as text_file:
            print(channel.id, file=text_file)
        with open("HELPROLES.txt", "a") as text_file:
            print(role.id, file=text_file)

        await ctx.respond(f"channel <#{channel.id}> and role {role.mention} have been added to the list")

    @commands.slash_command(name="clear", description="Clears messages")
    @default_permissions(manage_messages=True)
    async def clear_messages(self, ctx, amount: int):
        """
        Clear messages
        """
        if amount <= 0:
            await ctx.respond("Amount must be a positive number.")
            return

        channel = ctx.channel
        await ctx.respond(f"Clearing {amount} messages in {channel.name}...")

        try:
            await channel.purge(limit=amount + 1)
            await ctx.send(f"Cleared {amount} messages in {channel.name}.", delete_after=deltime)
        except discord.Forbidden:
            await ctx.send("I don't have the necessary permissions to manage messages in this channel.")
        except discord.HTTPException:
            await ctx.send("Failed to clear messages.")

    @commands.slash_command(name="kick", description="Kicks a person out of the server and inform them about it on dm.")
    @default_permissions(kick_members=True)
    async def kick(self, ctx, user: discord.Member, reason: str = "reason not given"):

        try:
            await user.send(f'You got kicked out of the server, reason:')
            await user.send(reason)
        except Exception as e:
            print(e)

        await user.kick(reason=reason)
        await ctx.respond(f"{user} got kicked. reason: " + reason)


def setup(bot):
    bot.add_cog(admin(bot))
