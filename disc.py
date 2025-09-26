from discord.ext import commands
from commands import commands as myCommands

import discord
import json

intents = discord.Intents.all()
intents.message_content = True
client = commands.Bot(command_prefix="$", intents=intents, help_command=None)

with open('data\\config.json') as config_file:
    config_data = json.load(config_file)
TOKEN = config_data['token']

client.add_command(myCommands.viewNotes)
client.add_command(myCommands.viewNote)
client.add_command(myCommands.addNotes)
client.add_command(myCommands.addNote)
client.add_command(myCommands.changeInfo)
client.add_command(myCommands.showNotes)
client.add_command(myCommands.showNote)
client.add_command(myCommands.removeNotes)
client.add_command(myCommands.removeNote)

client.add_command(myCommands.findUsers)
client.add_command(myCommands.findUser)
client.add_command(myCommands.getAssets)
client.add_command(myCommands.getAsset)
client.add_command(myCommands.getCollectibles)
client.add_command(myCommands.getCollectible)
client.add_command(myCommands.extractParts)
client.add_command(myCommands.extractPart)
client.add_command(myCommands.getInfo)
client.add_command(myCommands.getInfos)

client.add_command(myCommands.help)


@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    await client.tree.sync()

client.run(TOKEN)

