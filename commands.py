from discord.ext import commands
from discord.ui import Button, View
from commands import notes
from commands import lines

import discord
import json
import io
import math

intents = discord.Intents.all()
intents.message_content = True
client = commands.Bot(command_prefix="$", intents=intents, help_command=None)

with open('data\\whitelist.json') as whitelistFile:
    whitelist = json.load(whitelistFile)

def whitelistCheck():
    def predicate(ctx: commands.Context):
        return str(ctx.author.id) in whitelist
    return commands.check(predicate)

class YesNoButtons(View):
        def __init__(self):
            super().__init__()
            self.result = None

        @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
        async def yesButton(self, interaction: discord.Interaction):
            self.result = True
            self.stop()
        

        @discord.ui.button(label="No", style=discord.ButtonStyle.red)
        async def noButton(self, interaction: discord.Interaction):
            self.result = False
            self.stop()


@client.command()
@whitelistCheck()
async def viewNotes(ctx, userid: str = None):
    if userid is None:
        await ctx.reply(f"Incorrect use, $viewNotes 'userid'")
        return
    
    await viewNote(ctx, userid)
    
@client.hybrid_command(name="viewnotes", usage="/viewnotes", help='View notes for specified user')
@whitelistCheck()
async def viewNote(ctx, userid: str):
    s = notes.viewNote(userid)
    if s:
        msg = s.pop(next(reversed(s)))
        s = json.dumps(s, indent=4)

        await ctx.send(f'```json\n{s}```' + f'```\n{msg}```')
    else:
        await ctx.send(f'No notes for this user, use /changeInfo or /addNote to create a note')



@client.command()
@whitelistCheck()
async def addNote(ctx, userid: str | None = None, *, message: str | None = None):
    if not message or not userid:
        await ctx.send(f"Incorrect usage of the command. $addNote 'userid' 'message (multiline notes permited)'" + f'\nuserid: {userid}\nmessage: {message}')
        return
    await addNotes(ctx, userid, message)

@client.hybrid_command(name="addnote", usage="/addnote", help='Appends a note for specified user')
@whitelistCheck()
async def addNotes(ctx, userid: str, message: str):
    
    creator = whitelist.get(ctx.author.id)
    notes.addMessage(userid, message, creator=creator)
    await ctx.send(f"Added note for {userid}\nFor longer & custom notes, use $addNotes")



@client.hybrid_command(name="changeinfo", usage="/changeinfo", help='Change attributes for a specified username, age, note, etc')
@whitelistCheck()
async def changeInfo(ctx, userid: str, username: str = None, age: str = None, profilePictureRating: str = None, message: str = None):
    
    s = notes.viewNote(userid)

    if not s:
        await ctx.send(f'No notes for this user, use changeInfo or addNote to create a note')
        return

    view = YesNoButtons()
    embed = discord.Embed(
        description=f"There's already an entry for {userid}\nDo you want to overwrite?",
        color=discord.Color.purple()
    )

    message = await ctx.send(embed=embed, view=view)

    await view.wait()
    await message.delete()

    if view.result is False:
        return
    
    creator = whitelist.get(ctx.author.id)
    notes.changeInfo(userid, username, age, profilePictureRating, message, creator=creator)

    msg = s.pop(next(reversed(s)))
    s = json.dumps(s, indent=4)

    await ctx.send(f'```json\n{s}```' + f'```\n{msg}```')
        

@client.command()
@whitelistCheck()
async def showNotes(ctx, page: str = '0'):

    if page.isdigit():
        page = int(page)
    else:
        await ctx.send("Parameter isn't an integer, $showNotes 'Page Number'")
        return
    
    await showNote(ctx, page)
    
@client.hybrid_command(name="shownote", usage="/shownotes", help='Shows all the created notes')
@whitelistCheck()
async def showNote(ctx, page: int = 0):
    ENTRY_PER_PAGE = 10

    s1, s2 = notes.viewNotes()

    NUMPAGES = math.ceil(len(s1) / ENTRY_PER_PAGE)

    if page > NUMPAGES:
        pageStart = NUMPAGES

    if page == 0:
        pageStart = 1
    else:
        pageStart = page


    class Page(View):
        currPage: int

        def __init__(self, currPage = 0):
            super().__init__(timeout=30)
            self.currPage = currPage

        async def getPageEntries(self):
            pageEntriesIds = list()
            pageEntriesUsernames = list()

            start = self.currPage * ENTRY_PER_PAGE

            for i, x in enumerate(s1[start:]):
                if i >= ENTRY_PER_PAGE:
                    break
                pageEntriesIds.append(x)
                pageEntriesUsernames.append(s2[i+start])

            
            return pageEntriesIds, pageEntriesUsernames
        
        async def getEmbed(self):

            ids, usernames = await self.getPageEntries()

            embed = discord.Embed(
                title="List of notes",
                description=f"Page {self.currPage+1}/{NUMPAGES}",
                color=discord.Color.from_rgb(10, 10, 10)
            )

            embed.add_field(
                name = '',
                value=f"{':\n'.join(ids) + ':'}",
                inline=True
            )
            embed.add_field(
                name = '',
                value=f"{'\n'.join(usernames)}",
                inline=True
            )

            return embed
        
        def updateButtons(self):

            self.prevButton.disabled = (self.currPage == 0)
            self.nextButton.disabled = (self.currPage == NUMPAGES - 1)
        
        @discord.ui.button(label='<', style=discord.ButtonStyle.secondary)
        async def prevButton(self, interaction: discord.Interaction, button: Button):
            self.currPage -= 1

            self.updateButtons()

            embed = await self.getEmbed()

            await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(label='>', style=discord.ButtonStyle.secondary)
        async def nextButton(self, interaction: discord.Interaction, button: Button):
            self.currPage += 1

            self.updateButtons()

            embed = await self.getEmbed()

            await interaction.response.edit_message(embed=embed, view=self)
        
        @discord.ui.button(label='First', style=discord.ButtonStyle.secondary)
        async def firstButton(self, interaction: discord.Interaction, button: Button):
            self.currPage = 0

            self.updateButtons()

            embed = await self.getEmbed()

            await interaction.response.edit_message(embed=embed, view=self)
        
        @discord.ui.button(label='Last', style=discord.ButtonStyle.secondary)
        async def lastButton(self, interaction: discord.Interaction, button: Button):
            self.currPage = NUMPAGES - 1

            self.updateButtons()

            embed = await self.getEmbed()

            await interaction.response.edit_message(embed=embed, view=self)

    p = Page(pageStart-1)
    p.updateButtons()
   
    embed = await p.getEmbed()

    await ctx.send(embed=embed, view=p)



@client.command()
@whitelistCheck()
async def removeNote(ctx, userid: str | None = None):
    if not userid:
        await ctx.send(f"Incorrect usage of the command. $removeNote 'userid'" + f'\nuserid: {userid}')
        return
    
    await removeNotes(ctx, userid)

@client.hybrid_command(name="removenote", usage="/removenote", help='Remove all notes from specified user')
@whitelistCheck()
async def removeNotes(ctx, userid: str):
    
    if notes.removeNote(userid) == True:
        await ctx.send(f"Removed note for {userid}")
    else:
        await ctx.send(f"There is no note for {userid}")



@client.command()
@whitelistCheck()
async def findUser(ctx, username: str = None):
    if username is None:
        await ctx.reply(f"Incorrect use, $findUser 'username'")
        return
    
    await findUsers(ctx, username)

@client.hybrid_command(name="findusers", usage="/finduser", help="Shows a list of userids based on given username")
@whitelistCheck()
async def findUsers(ctx, username: str):
    s = lines.findUser(username.lower())

    if not s:
        embed = discord.Embed(
        title='No userids found',
        color=0x2F3136
        )
    else:
        embed = discord.Embed(
            title='List of userids found:',
            description=f"{s}",
            color=discord.Color.purple()
            )
    
    embed.set_footer(text="Note: Usernames change, they can also be wrongly scraped\nUse 'userid' whenever possible at all times\nThis ensures the data you have is correct")

    await ctx.send(embed=embed)



@client.command()
@whitelistCheck()
async def getAssets(ctx, asset: str = None, verified:bool | None = None):
    if asset is None:
        await ctx.reply(f"Improper use, $getAssets 'asset' 'verified (yes/no)'")
        return
    
    await getAsset(ctx, asset, verified)

@client.hybrid_command(name="getasset", usage="/getassets", help='List users with a specified asset')
@whitelistCheck()
async def getAsset(ctx, asset: str, verified:bool | None = None):
    users = lines.findLimiteds(asset, verified)
    s = lines.getLines(users)

    buf = io.BytesIO(s.encode("utf-8"))
    buf.seek(0)
    discord_file = discord.File(buf, filename="assets.txt")
    await ctx.send(file=discord_file)



@client.command()
@whitelistCheck()
async def getCollectibles(ctx, collectible: str = None, verified:bool | None = None):
    if collectible is None:
        await ctx.reply(f"Improper use, $getCollectibles 'collectible' 'verified (yes/no)'")
        return
    
    await getCollectible(ctx, collectible, verified)

@client.hybrid_command(name="getcollectible", usage="/getcollectible", help="List users with the specified collectible, collectible name can't be an acronym")
@whitelistCheck()
async def getCollectible(ctx, collectible: str, verified:bool | None = None):
    users = lines.findCollectibles(collectible, verified)
    s = lines.getLines(users)

    buf = io.BytesIO(s.encode("utf-8"))
    buf.seek(0)
    discord_file = discord.File(buf, filename="collectibles.txt")
    await ctx.send(file=discord_file)



@client.command()
@whitelistCheck()
async def extractParts(ctx, char_to_seperate: str = None, index: int = None):
    if not char_to_seperate or not index:
        await ctx.send(f"Incorect usage of the command. $extractParts 'Character To Seperate' 'Index'" + f'\nuserid: {char_to_seperate}\nmessage: {index}')
        return
    
    if not ctx.message.attachments:
        await ctx.send("No attachments found.")
        return
    
    file: discord.Attachment = ctx.message.attachments[0]
    await extractParts(ctx, char_to_seperate, index, file)

@client.hybrid_command(name="extractpart", usage="/extractparts", help='Extract a specified part from an attached file')
@whitelistCheck()
async def extractPart(ctx, char_to_seperate: str, index: int, file: discord.Attachment):
    
    view = YesNoButtons()
    embed = discord.Embed(
        description="Does your char have a space after?",
        color=discord.Color.purple()
    )

    message = await ctx.send(embed=embed, view=view) # Slash commands in discord don't read spaces found after a string

    await view.wait()
    await message.delete()

    if view.result is True:
        char_to_seperate = char_to_seperate + " "

    data = await file.read()
    
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        text = None
    

    s = lines.extractParts(text.splitlines(), char_to_seperate, index)
    buf = io.BytesIO(s.encode("utf-8"))
    buf.seek(0)
    discord_file = discord.File(buf, filename="extractedParts.txt")
    await ctx.send(f"Character to seperate by: `{char_to_seperate}`\nColumn #: `{index}`", file=discord_file)



@client.command()
@whitelistCheck()
async def getInfo(ctx, userid: str = None):
    if not userid:
        await ctx.send('No userid provided')
        return
    
    await getInfos(ctx, userid)
    
@client.hybrid_command(name="getinfos", usage="/getinfo", help='Shows all info for specified userid')
@whitelistCheck()
async def getInfos(ctx, userid: str):
    data = lines.getInfo(userid)
    if not data:
        await ctx.send(f'No such user in db')
        return
    
    s = json.dumps(data, indent=4)
    buf = io.BytesIO(str(s).encode("utf-8"))
    buf.seek(0)
    discord_file = discord.File(buf, filename="info.txt")
    await ctx.send(file=discord_file)



@client.command()
@whitelistCheck()
async def help(ctx):
    embed = discord.Embed(
        description="List of commands.",
        color=0x2F3136
    )

    embed.add_field(
        name = '',
        value="• /viewnotes — View notes for the user\n" \
        "‒ `userid`\n" \
        "‒ `$viewNotes`",
        inline=False
    )

    embed.add_field(
        name = '',
        value="• /addnote — Add a note to the user\n" \
        "‒ `userid`, `message`\n" \
        "‒ `$addNotes`",
        inline=False
    )

    embed.add_field(
        name = '',
        value="• /removenote — Removed note for specified user\n" \
        "‒ `userid`\n" \
        "‒ `$removeNote`",
        inline=False
    )

    embed.add_field(
        name = '',
        value="• /changeinfo — Edit user attributes\n" \
        "‒ `userid`\n" \
        "‒ `Optional: username, age, profilePictureRating, message`",
        inline=False
    )

    embed.add_field(
        name = '',
        value="• /getassets — List users with an asset\n" \
        "‒ `asset`\n" \
        "‒ `Optional: verified`\n" \
        "‒ `$getAssets`",
        inline=False
    )

    embed.add_field(
        name = '',
        value="• /getCollectibles — List users with a collectible\n" \
        "‒ `collectible`\n" \
        "‒ `Optional: verified`\n" \
        "‒ `$getCollectibles`",
        inline=False
    )

    embed.add_field(
        name = '',
        value="• /extractparts — Extract parts from attached file\n" \
        "‒ `Character To Seperate By`, `Index`, `Attached File`\n" \
        "‒ `$extractParts`",
        inline=False
    )

    embed.add_field(
        name = '',
        value="• /shownotes — Shows all the created notes\n"\
            "‒ `Optional: Page Number`"\
            "‒ `$showNotes`",
        inline=False
    )

    embed.add_field(
        name = '',
        value="• /finduser — Shows a list of userids based on given username\n"\
            "‒ `username`\n" \
            "‒ `$findUser`",
        inline=False
    )

    embed.add_field(
        name = '',
        value="• /getinfo — Shows all info for specified userid\n" \
        "‒ `userid`\n"\
        "‒ `$getInfo`\n",
        inline=False
    )

    embed.add_field(
        name = '',
        value="• /help — Show a list of commands",
        inline=False
    )

    embed.set_footer(text="Use slash commands or $-prefix where supported.")
    embed.timestamp = discord.utils.utcnow()

    await ctx.send(embed=embed)
    

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        embed = discord.Embed(description="Whitelist only")
        await ctx.send(embed=embed)
        await ctx.send("https://tenor.com/view/i-love-you-i-love-you-so-much-gif-10862015092269957633")
        return
    raise error