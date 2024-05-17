import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord import app_commands
from sqlitedict import SqliteDict as DB
import re

intents = discord.Intents().all()


class Notes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DB('db/db.sqlite', tablename='notes')
        super().__init__()

    async def add_note(self, interaction, trigger: str, response: str):
        notes_table = self.db[interaction.guild.id]
        if not notes_table['notes'][trigger]:
            notes_table['notes'][trigger.lower()] = f'!{response}!'
        # if not any(trigger in key['trigger'] for key in callbacks["triggers"]):
        #     callbacks["triggers"].append(
        #         {'trigger': trigger.lower(), 'response': response})
        #     self.db[interaction.guild.id] = callbacks
        #     self.db.commit()
        #     await interaction.response.send_message(f'Callback "{trigger}" added')
        else:
            await interaction.response.send_message(f"Error! Trigger \"{trigger}\" already exists!")

    async def list_callbacks(self, interaction):
        callbacks = self.db[interaction.guild.id]
        embedVar = discord.Embed(title="Notes", description="Saved note trigger commands")
        print(callbacks)
        for callback in callbacks["triggers"]:
            embedVar.add_field(
                name=f"{callback['trigger']}:", value=callback['response'], inline=True)
        if len(callbacks["channels"]) > 0:
            channelEmbed = discord.Embed(title="Blacklisted Channels", description="Channels where callbacks will not go off")
            for channel in callbacks["channels"]:
                channelEmbed.add_field(name="Channel:", value=channel, inline=True)
            await interaction.response.send_message(embeds=[embedVar, channelEmbed])
        else:
            await interaction.response.send_message(embed=embedVar)

    async def remove_note(self, interaction, trigger: str):
        callbacks = self.db[interaction.guild.id]
        if any(callback['trigger'] == trigger.lower() for callback in callbacks['triggers']):
            for callback in callbacks['triggers']:
                if callback['trigger'] == trigger.lower():
                    callbacks['triggers'].remove(callback)
            self.db[interaction.guild.id] = callbacks
            self.db.commit()
            await interaction.response.send_message(f'Callback "{trigger}" deleted')
        else:
            await interaction.response.send_message(f'Error! Callback "{trigger}" not found!')

    async def add_channel(self, interaction, channel: discord.TextChannel):
        callbacks = self.db[interaction.guild.id]
        if channel.name in callbacks["channels"]:
            await interaction.response.send_message(f'Error! {channel.name} is already blacklisted!')
            return
        callbacks["channels"].append(channel.name)
        self.db[interaction.guild.id] = callbacks
        self.db.commit()
        await interaction.response.send_message(f'Channel {channel.name} successfully blacklisted')

    async def remove_channel(self, interaction, channel: discord.TextChannel):
        callbacks = self.db[interaction.guild.id]
        if channel.name not in callbacks["channels"]:
            await interaction.response.send_message(f'Error! {channel.name} is not blacklisted!')
            return
        callbacks["channels"].remove(channel.name)
        self.db[interaction.guild.id] = callbacks
        self.db.commit()
        await interaction.response.send_message(f'Channel {channel.name} successfully whitelisted')


    group = app_commands.Group(name="callback", description="...")

    @group.command(name="add", description="Add new callback")
    async def add(self, interaction: discord.Interaction, trigger: str, response: str):
        await self.add_callback(interaction, trigger, response)

    @group.command(name="disable", description="Disable callbacks in specified channel")
    async def add(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.add_channel(interaction, channel)

    @group.command(name="enable", description="Enable callbacks in specified channel")
    async def add(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.remove_channel(interaction, channel)

    @group.command(name="remove", description="Remove existing callbacks")
    async def remove(self, interaction: discord.Interaction, trigger: str):
        await self.remove_callback(interaction, trigger)

    @app_commands.command(name="list", description="List all callbacks and blacklisted channels")
    async def list(self, interaction: discord.Interaction):
        await self.list_callbacks(interaction)

    @list.error
    @remove.error
    async def callbacks_error(self, interaction, error):
        await interaction.response.send_message(f'Error {error}', ephemeral=True)

    @commands.Cog.listener('on_message')
    async def send_callback(self, message):
        if message.author == self.bot.user or message.channel.name in self.db[message.guild.id]["channels"]:
            return

        callbacks = self.db[message.guild.id]
        if any(re.compile(r'\b({0})\b'.format(key['trigger']), flags=re.IGNORECASE).search(message.content) for key in callbacks["triggers"]):
            triggered = [
                callback for callback in callbacks["triggers"] if callback['trigger'] in message.content.lower()]
            for callback in triggered:
                await message.channel.send(callback["response"])


async def setup(bot: commands.Bot):
    await bot.add_cog(Notes(bot))
