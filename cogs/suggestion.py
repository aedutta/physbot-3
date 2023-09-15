from datetime import datetime
from random import choice
import discord
from discord.ext import commands
from discord import app_commands
import config
from helper import worksheet, on_interaction
Cog = commands.Cog
sheet = worksheet('PHODS', 'suggestions')


def find_color(status):
    mapping = {'Approved': config.green,
               'Denied': config.red, 'Dropped': config.black}
    try:
        color = mapping[status]
    except KeyError:
        color = config.yellow
    return color


class Suggestion(Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id == config.suggestion_channel:
            data = sheet.get()
            await message.add_reaction('\U0001F44D')
            await message.add_reaction('🤷‍♂️')
            await message.add_reaction('\U0001F44E')
            embed = discord.Embed(
                title=f"{message.author.display_name}'s Suggestion", colour=config.yellow)
            embed.set_thumbnail(url=message.author.display_avatar.url)
            embed.add_field(name="Suggestion",
                            value=message.content, inline=False)
            embed.add_field(name="Suggestion Status",
                            value="Pending", inline=False)
            msg = await self.bot.get_channel(config.status).send(embed=embed)
            data.insert(1, [str(message.id), str(msg.id), str(message.author.id),
                        message.content, 'Pending', ''])
            sheet.update(data)

    @Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.channel.id == config.suggestion_channel:
            await after.add_reaction('\U0001F44D')
            await after.add_reaction('🤷‍♂️')
            await after.add_reaction('\U0001F44E')
            data = sheet.get()
            for sug in data[1:]:
                if before.id == int(sug[0]):
                    embed = discord.Embed(title=f"{after.author.display_name}'s Suggestion", colour=find_color(sug[4]))
                    embed.set_thumbnail(url=after.author.display_avatar.url)
                    sug[3] = after.content
                    embed.add_field(name="Suggestion",value=after.content, inline=False)
                    embed.add_field(name="Suggestion Status",value=sug[4], inline=False)
                    try:
                        embed.add_field(name="Reason for Status",value=sug[5], inline=False)
                    except IndexError:
                        pass
                    msg = await self.bot.get_channel(config.status).fetch_message(str(sug[1]))
                    await msg.edit(embed=embed)
                    break
            sheet.update(data)
    @Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.channel.id == config.suggestion_channel:
            data = sheet.get()
            index = 0
            for i,sug in enumerate(data[1:].copy(),start=1):
                if message.id == int(sug[0]):
                    msg = await self.bot.get_channel(config.status).fetch_message(str(sug[1]))
                    await msg.delete()
                    index = i
                    break
            if index:
                del data[index]
            sheet.update(data)
    @app_commands.command(name="update_suggestion", description="Only works in #suggestion_status")
    @app_commands.describe(status="Approved:green|Denied:red|Dropped:black|Other:yellow")
    @on_interaction
    async def update_suggestion(self, interaction: discord.Interaction, og_message_id: str, status: str, reason: str = ''):
        data = sheet.get()
        if interaction.channel_id != config.status:
            interaction.response.send_message("Only works on #suggestion-status")
            return True
        for sug in data[1:]:
            sug: list
            if int(sug[1]) == int(og_message_id):
                await interaction.response.send_message("working on it...", ephemeral=True)
                sug[4] = status
                if len(sug) == 5:
                    sug.append("")
                sug[5] = reason
                user = await self.bot.fetch_user(int(sug[2]))
                embed = discord.Embed(
                    title=f"{user.display_name}'s Suggestion", colour=find_color(sug[4]))
                embed.set_thumbnail(url=user.display_avatar)
                embed.add_field(name="Suggestion", value=sug[3], inline=False)
                embed.add_field(name="Suggestion Status",
                                value=sug[4], inline=False)
                try:
                    assert sug[5]
                    embed.add_field(name="Reason for Status",
                                    value=sug[5], inline=False)
                except AssertionError:
                    pass
                msg = await self.bot.get_channel(config.status).send(embed=embed)
                og_msg = await self.bot.get_channel(config.status).fetch_message(int(sug[1]))
                await og_msg.delete()
                sug[1] = str(msg.id)
                sheet.update(data)
                break
        else:
            await interaction.response.send_message(
                "Suggestion not found in DB plz try the suggestion posted on or after 1st oct.", ephemeral=True)
    async def cog_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        await self.bot.get_channel(config.log_channel).send((await self.bot.fetch_user(config.proelectro)).mention,config.log_channel).send(embed=discord.Embed(color=config.red,title=str(interaction.user),description=str(error)))



async def setup(bot: commands.Bot):
    await bot.add_cog(Suggestion(bot))
