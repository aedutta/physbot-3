from datetime import datetime
from random import choice
import discord
from discord.ext import commands
from discord import app_commands
import config
from helper import on_interaction
Cog = commands.Cog


class Logs(Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    @Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        try:
            embed = discord.Embed(color=config.red,description=f'**Message sent by {message.author.mention} deleted in {message.channel.mention}**')
            embed.set_author(icon_url=message.author.avatar.url,name=str(message.author))
            embed.add_field(name='Deleted Message:',value=message.content,inline=False)
            await self.bot.get_channel(config.logs).send(embed=embed)
        except:
            pass
    @Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        try:
            embed = discord.Embed(color=config.yellow,description=f'**Message sent by {after.author.mention} edited in {after.channel.mention}**')
            embed.set_author(icon_url=before.author.avatar.url,name=str(before.author))
            embed.add_field(name='Before:',value=before.content,inline=False)
            embed.add_field(name='After:',value=after.content,inline=False)
            await self.bot.get_channel(config.logs).send(embed=embed)
        except:
            pass
async def setup(bot: commands.Bot):
    await bot.add_cog(Logs(bot))
