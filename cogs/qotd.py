from datetime import datetime,time
from random import choice
import discord
from discord.ext import commands,tasks
from discord import app_commands
from helper import worksheet, on_interaction
import numpy as np
import config
import os
Cog = commands.Cog
sheets = worksheet('QOTD', all_=True)
sheet = sheets.worksheet('Sheet1')
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
WEEKDAY = ['Monday', 'Tuesday', 'Wednesday',
           'Thursday', 'Friday', 'Saturday', 'Sunday']
A1, a1, B1, b1 = 8.90125, -0.0279323, 24.6239, -0.402639


class Menu(discord.ui.View):
    def __init__(self, to_append: list):
        super().__init__(timeout=None)
        self.to_append = to_append

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = sheet.get()
        num = self.to_append[0] = len(data)
        sheet.append_row(self.to_append)
        await interaction.response.edit_message(content=f"Uploaded as QoTD {num}. Accepted by {interaction.user}", view=None)
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"Cancelled uploading...", view=None)
        self.stop()


class Qotd(Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.qost.start()
    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or isinstance(message.author, discord.Member):
            return
        if "qotd" in message.content:
            await message.channel.send("To submit your solution of a qotd type /qotd submit and click on the command. As shown below.",file=discord.File(os.getcwd()+r"/images/submit.png"))
            await message.channel.send("Then type number and respective answer to question which you want to submit. As shown below",file=discord.File(os.getcwd()+r"/images/qotd.png"))
            await message.channel.send("The bot will soon let you know if your answer is correct of wrong as shown below",file=discord.File(os.getcwd()+r"/images/verdict.png"))
    def grade(self, correct_ans, tolerance, submission):
        totalatt = 0
        weigting = {}
        for sub in submission:
            user, *attp = sub
            totalatt += len(attp)
            score = 1/0.8
            for ans in attp[:6]:
                score *= 0.8
                if abs(float(ans)-correct_ans) <= abs(correct_ans*tolerance):
                    break
            else:
                score = 0
            weigting[user] = score
        weightsolve = sum(weigting.values())
        numsolved = len(list(filter(lambda k: weigting[k], weigting)))
        base = A1 * np.exp(a1 * weightsolve) + B1 * np.exp(b1 * weightsolve)
        points = {user: weigting[user]*base for user in weigting}
        return points, base, weightsolve, numsolved, totalatt
    
    group = app_commands.Group(name="qotd", description="...")
    
    @tasks.loop(time=time(0,0))
    async def qost(self):
        msg = await self.bot.get_channel(config.qotd_planning).fetch_message(config.qotd_toggle)
        if "101" in msg.content:
            return
        data = sheet.get()
        now = datetime.now()
        for num in range(len(data)-1,1,-1):
            if data[num][12] == 'pending' and data[num-1][12] != 'pending':
                if data[num-1][12] != "done":
                    data[num-1][12] = 'done'
                    a, b = data[num-1][10:12]
                    points: dict = self.grade(float(a), float(
                        b)/100, sheets.worksheet(f"qotd {num-1}").get())[0]
                    leader = sheets.worksheet('Leaderboard')
                    update = [['users', 'points']]
                    for user, point in leader.get()[1:]:
                        try:
                            point = float(point)
                            point += points[user]
                            del points[user]
                        except KeyError:
                            pass
                        update.append([user, point])
                    for user, point in points.items():
                        update.append([user, point])
                    leader.update(update)
                sheet_data = sheets.worksheet("data")
                sheet_data.update_acell(
                    'B2', 1+int(p) if (p := sheet_data.acell('B2').value) else 1)
                sheets.add_worksheet(f"qotd {num}", rows=100, cols=50)
                data[num][12] = 'live'
                data[num][1] = f'{now.day} {MONTHS[now.month-1]} {now.year}'
                data[num][2] = WEEKDAY[now.weekday()]
                post = f'**QOTD {data[num][0]}**\n**{data[num][1]}**\n{data[num][6]}'
                post2 = f'QOTD Creator: **{data[num][3]}**\n' if data[num][3] else ""
                post4 = f'Difficulty: {data[num][8]}\n' if data[num][8] else ""
                post6 = f'{self.bot.get_guild(config.phods).get_role(config.qotd_role).mention} to submit your answer use /qotd submit command in my({self.bot.user.mention}) DM.'
                msg1 = await self.bot.get_channel(config.question_of_the_day).send(post)
                msg2 = await self.bot.get_channel(config.question_of_the_day).send(post2+post4)
                msg3 = await self.bot.get_channel(config.question_of_the_day).send(post6)
                await msg1.publish()
                await msg2.publish()
                await msg3.publish()
                phods = self.bot.get_guild(config.phods)
                role = phods.get_role(config.qotd_solver)
                for member in role.members:
                    await member.remove_roles(role)
                embed = discord.Embed(
                    title=f"Live Statistics for QoTD {num}")
                embed.set_footer(text=f"Creator: {data[num][3]}")
                if data[num][8]:
                    embed.add_field(name="Difficulty",
                                    value=str(data[num][8]))
                base = A1 + B1
                embed.add_field(name="Base Points", value=f'{base:.3f}')
                embed.add_field(name="Weighted Solves",
                                value='0', inline=False)
                embed.add_field(name="Solves (official)",
                                value=str(0), inline=False)
                embed.add_field(name="Total attempts",
                                value=str(0), inline=False)
                stats = await self.bot.get_channel(config.question_of_the_day).send(embed=embed)
                data[num].append(str(stats.id))
                constrains = sheets.worksheet("data").get_all_records()[0]
                constrains['qotd'] = num
                leaderboard = sheets.worksheet("Leaderboard").get()
                hold = [f'{str(i+1)+".":4}{str(await self.bot.fetch_user(int(person[0])))[:26]:27}{float(person[1]):.3f}' for i, person in enumerate(sorted(leaderboard[1:], key=lambda per:-float(per[1])))]
                to_send = "**" + \
                    constrains['Message'].format(
                        **constrains)+"**"+"\n```"+"\n".join(hold[:30])+"```"
                led = await self.bot.get_channel(config.leaderboard).send(to_send)
                data[num].append(str(led.id))
                try:
                    sheets.del_worksheet(sheets.worksheet(f"qotd {num-3}"))
                except:
                    pass
                sheet.update(data)
                
                break
        else:
            await self.bot.get_channel(config.question_of_the_day).send("Sorry we dont have any QOTD today.")
    
    @group.command(name="fetch", description="to fetch qotd by num")
    @on_interaction
    async def fetch(self, interaction: discord.Interaction, num: int):
        data = sheet.get()
        now = datetime.now()
        if len(data) <= num:
            await interaction.response.send_message("Sorry no such qotd.")
            return True
        else:
            if interaction.channel_id == config.question_of_the_day:
                await interaction.response.send_message("Depreciated",ephemeral=True)
                return True
            else:
                if data[num][6] and (data[num][12] == 'done' or interaction.channel_id in (config.qotd_planning, config.qotd_botspam)):
                    post = f'**QOTD {data[num][0]}**\n**{data[num][1]}**\n{data[num][6]}'
                    post2 = f'QOTD Creator: **{data[num][3]}**\n' if data[num][3] else ""
                    post3 = f'Source: ||{data[num][4]}||\n' if data[num][4] else ""
                    post4 = f'Points: {data[num][5]}\n' if data[num][5] else ""
                    post5 = f'Difficulty: {data[num][8]}\n' if data[num][8] else ""
                    post6 = f'Category: {data[num][7]}\n' if data[num][7] else ""
                    await interaction.channel.send(post)
                    await interaction.channel.send(post2+post3+post4+post5+post6)
                    await interaction.response.send_message("Posted succefully", ephemeral=True)
                else:
                    await interaction.response.send_message("Qotd yet to release.")
                    return True
        sheet.update(data)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if not isinstance(error, app_commands.CommandOnCooldown):
            await self.bot.get_channel(config.log2).send((await self.bot.fetch_user(config.proelectro)).mention,embed=discord.Embed(color=config.red, title=str(interaction.user), description=str(error)))

    @group.command(name="solution", description="To get solution and answer of a particular qotd")
    @on_interaction
    async def solution(self, interaction: discord.Interaction, num: int, link: str = ""):
        data = sheet.get()
        if link and (interaction.user.get_role(config.admin) or interaction.user.get_role(config.qotd_creator)):
            data[num][9] = link
            await interaction.response.send_message("Successfully updated the solution to the sheet.")
            sheet.update(data)
            return
        else:
            if data[num][12] == "done":
                post = f"**QOTD {num} Solution**\nQOTD Creator: **{data[num][3]}**\nAnswer: {data[num][10]}\nSource: {data[num][4]}\n{data[num][9]}"
                await interaction.response.send_message(post)
            else:
                await interaction.response.send_message("Qotd not yet done", ephemeral=True)
                return True
    @group.command(name="submit", description="Only works on DM.")
    @app_commands.checks.cooldown(1, 60)
    @on_interaction
    async def submit(self, interaction: discord.Interaction, num: int, answer: str):
        try:
            float(answer)
        except ValueError:
            await interaction.response.send_message("Answer must be a decimal.")
            return True
        data = sheet.get()
        phods = self.bot.get_guild(config.phods)
        error = ""
        if isinstance(interaction.user, discord.Member):
            error = "This command only works in DM"
        elif len(data) <= num or data[num][12] == "pending":
            error = "Qotd yet to come."
        elif data[num][12] != "live" or phods.get_member(interaction.user.id).get_role(config.qotd_creator) or phods.get_member(interaction.user.id).get_role(config.admin):
            answer = float(answer)
            data = sheet.get()[num]
            correct_ans, tolerance = data[10:12]
            correct_ans, tolerance = float(correct_ans), float(tolerance)/100
            if abs(correct_ans-answer) <= abs(correct_ans*tolerance):
                embed = discord.Embed(
                    description=f"**Submission to QOTD {num} made by {interaction.user}**", colour=config.green, timestamp=datetime.utcnow())
                embed.set_author(
                    name=f"{interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.display_avatar.url)
                embed.add_field(name="Submitted Answer:",
                                value=answer, inline=False)
                embed.add_field(name="Verdict:", value="Correct", inline=False)
            else:
                embed = discord.Embed(
                    description=f"**Submission to QOTD {num} made by {interaction.user}**", colour=config.red, timestamp=datetime.utcnow())
                embed.set_author(
                    name=f"{interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.display_avatar.url)
                embed.add_field(name="Submitted Answer:",
                                value=answer, inline=False)
                embed.add_field(name="Verdict:",
                                value="Incorrect", inline=False)
            await interaction.response.send_message(embed=embed)
            return 
        if error:
            await interaction.response.send_message(error)
            return True
        else:
            answer = float(answer)
            data = sheet.get()[num]
            correct_ans, tolerance = data[10:12]
            correct_ans, tolerance = float(correct_ans), float(tolerance)/100
            if abs(correct_ans-answer) <= abs(correct_ans*tolerance):
                embed = discord.Embed(
                    description=f"**Submission to QOTD {num} made by {interaction.user}**", colour=config.green, timestamp=datetime.utcnow())
                embed.set_author(
                    name=f"{interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.display_avatar.url)
                embed.add_field(name="Submitted Answer:",
                                value=answer, inline=False)
                embed.add_field(name="Verdict:", value="Correct", inline=False)
                try:
                    await phods.get_member(interaction.user.id).add_roles(phods.get_role(config.qotd_solver))
                except:
                    pass
            else:
                embed = discord.Embed(
                    description=f"**Submission to QOTD {num} made by {interaction.user}**", colour=config.red, timestamp=datetime.utcnow())
                embed.set_author(
                    name=f"{interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.display_avatar.url)
                embed.add_field(name="Submitted Answer:",
                                value=answer, inline=False)
                embed.add_field(name="Verdict:",
                                value="Incorrect", inline=False)
            await interaction.response.send_message(embed=embed)
            await self.bot.get_channel(config.qotd_botspam).send(embed=embed)
            qotd_sheet = sheets.worksheet(f"qotd {num}")
            submission = qotd_sheet.get()
            for yum in submission:
                if str(interaction.user.id) == yum[0]:
                    yum.append(float(answer))
                    break
            else:
                submission.append([str(interaction.user.id), float(answer)])
            qotd_sheet.update(submission)
            points, base, weightsolve, numsolved, totalatt = self.grade(
                correct_ans, tolerance, submission)
            leader = sheets.worksheet('Leaderboard')
            update = [['users', 'points']]
            for user, point in leader.get()[1:]:
                try:
                    point = float(point)
                    point += points[user]
                    del points[user]
                except KeyError:
                    pass
                update.append([user, point])
            for user, point in points.items():
                update.append([user, point])
            constrains = sheets.worksheet("data").get_all_records()[0]
            constrains['qotd'] = num
            hold = [f'{str(i+1)+".":4}{str(await self.bot.fetch_user(int(person[0])))[:26]:27}{float(person[1]):.3f}' for i, person in enumerate(sorted(update[1:], key=lambda per:-float(per[1])))]
            to_send = "**" + \
                constrains['Message'].format(
                    **constrains)+"**"+"\n```"+"\n".join(hold[:30])+"```"
            leader_msg = await self.bot.get_channel(config.leaderboard).fetch_message(int(data[14]))
            await leader_msg.edit(content=to_send)
            embed = discord.Embed(title=f"Live Statistics for QoTD {num}")
            embed.set_footer(text=f"Creator: {data[3]}")
            if data[8]:
                embed.add_field(name="Difficulty", value=str(data[8]))
            embed.add_field(name="Base Points", value=str(round(base, 3)))
            embed.add_field(name="Weighted Solves", value=str(
                round(weightsolve, 3)), inline=False)
            embed.add_field(name="Solves (official)",
                            value=str(numsolved), inline=False)
            embed.add_field(name="Total attempts",
                            value=str(totalatt), inline=False)
            stats_msg = await self.bot.get_channel(config.question_of_the_day).fetch_message(int(data[13]))
            await stats_msg.edit(embed=embed)

    @submit.error
    async def on_submit_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(str(error), ephemeral=True)

    @group.command(name="upload", description="Only for curators.")
    @app_commands.describe(tolerance="In %", question_links="Image attachement links for more then one link each link should be in newline.", points="Deprecated currently just for compability issues.")
    @on_interaction
    async def upload(self, interaction: discord.Interaction, question_links: str, topic: str, answer: str, tolerance: str = "1", source: str = "", points: int = None,  difficulty: str = None):
        if not all("attachments" in k for k in question_links.splitlines()):
            await interaction.response.send_message("You need an attachemnt link. mobile: link on share ; pc: open image in newtab and copy url.")
            return
        try:
            float(answer)
            float(tolerance)
        except ValueError:
            await interaction.response.send_message("Invalid answer or tolerance")
            return True
        data = sheet.get()
        now = datetime.now()
        channel = self.bot.get_channel(config.qotd_planning)
        if interaction.channel_id in (config.qotd_planning, config.qotd_botspam):
            msg = "Are you sure you want to upload this can't be reversed."
            await interaction.response.send_message("Processing your querry....")
        else:
            await interaction.response.send_message("You are not authorize to upload qotd.", ephemeral=True)
            return True
        num = len(data)
        to_append = [len(data), f'{now.day} {MONTHS[now.month-1]} {now.year}', WEEKDAY[now.weekday()],
                     interaction.user.name, source, points, question_links, topic, difficulty, "", answer, tolerance, "pending"]
        data.append(to_append)
        post = f'**QOTD {data[num][0]}**\n**{data[num][1]}**\n{data[num][6]}'
        # if data[num][3] else ""
        post2 = f'QOTD Creator: **{data[num][3]}**\n'
        post3 = f'Source: ||{data[num][4]}||\n'  # if data[num][4] else ""
        post4 = f'Points: {data[num][5]}\n'  # if data[num][5] else ""
        post5 = f'Difficulty: {data[num][8]}\n'  # if data[num][8] else ""
        post6 = f'Category: {data[num][7]}\n'
        post7 = f'Answer: {data[num][10]} Tolerance: {data[num][11]}'
        await channel.send(post)
        await channel.send(post2+post3+post4+post5+post6+post7)
        await channel.send(view=Menu(to_append), content=msg)


async def setup(bot):
    await bot.add_cog(Qotd(bot))
