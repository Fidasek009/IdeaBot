#! /usr/bin/python

import random
import logging
# Discord
import discord
from discord import app_commands
# dotenv
from dotenv import load_dotenv
from os import getenv
# MySQL
import mysql.connector
from prettytable import PrettyTable


# -------------------------DOTENV stuff-------------------------
load_dotenv()
TOKEN = getenv("DISCORD_TOKEN")
GUILD_ID = getenv("GUILD_ID")
# Add the guild ids in which the slash command will appear.
# If it should be in all, remove the argument, but note that it will take some time (up to an hour) to register the command if it's for all guilds.
CATEGORY_NAME = getenv("CATEGORY_NAME")
SQL_USR = getenv("SQL_USR")
SQL_PWD = getenv("SQL_PWD")

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s     %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


# -------------------------Discord bot stuff-------------------------
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# -------------------------MySQL stuff-------------------------
DB = None
CURSOR = None

async def sql_init():
    global DB, CURSOR
    DB = mysql.connector.connect(
        host='127.0.0.1',
        user=SQL_USR,
        password=SQL_PWD,
        database='IdeaBot',
        auth_plugin='mysql_native_password'
    )
    CURSOR = DB.cursor()


async def sql_execute(query: str):
    try:
        CURSOR.execute(query)
        DB.commit()
    except:
        await sql_init()
        CURSOR.execute(query)
        DB.commit()


async def sql_fetch(query: str):
    try:
        CURSOR.execute(query)
        rows = CURSOR.fetchall()
    except:
        await sql_init()
        CURSOR.execute(query)
        rows = CURSOR.fetchall()

    columns = [col[0] for col in CURSOR.description]  # extract row headers
    return [dict(zip(columns, row)) for row in rows]


def table(data: list):
    t = PrettyTable(['name', 'subject', 'creator', 'difficulty'])
    for row in data:
        t.add_row([row['name'], row['subject'], row['creator'], row['difficulty']])
    return t


# -------------------------AUTOCOMPLETE-------------------------
async def name_autocomplete(interaction: discord.Interaction, currnet: str):
    result = await sql_fetch(f"SELECT name FROM ideas WHERE name LIKE '%{currnet}%'")
    names = []
    for row in result:
        names.append(app_commands.Choice(name=row['name'], value=row['name']))
    return names


# -------------------------ON READY-------------------------
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    await sql_init()
    logging.info("READY!") # LOG


# ===================================IDEAS===================================
# -------------------------ADD-------------------------
@tree.command(name="add", description="Create an idea", guild=discord.Object(id=GUILD_ID))
async def add_cmd(interaction, name: str, subject: str, difficulty: int, description: str):
    creator = interaction.user.name

    logging.info(f"Creating idea `{name}` with values: `subject={subject}, difficulty={difficulty}, description={description}`") # LOG

    name = name.lower()
    result = await sql_fetch(f"SELECT * FROM ideas WHERE LOWER(name) = '{name}'")

    if len(result) == 0:
        add_sql = ("INSERT INTO ideas (name, subject, creator, difficulty, description) "
                    f"VALUES ('{name}', '{subject}', '{creator}', {difficulty}, '{description}')")
        await sql_execute(add_sql)

        await interaction.response.send_message(f"Created a new idea `{name}`")
    else:
        await interaction.response.send_message(f"Your idea `{result[0]['name']}` already exists and was created by **{result[0]['creator']}**")


# -------------------------EDIT-------------------------
@tree.command(name="edit", description="Edit an idea", guild=discord.Object(id=GUILD_ID))
@app_commands.autocomplete(name=name_autocomplete)
async def edit_cmd(interaction, name: str, rename: str = None, subject: str = None, difficulty: str = None, description: str = None):
    name = name.lower()
    vars = ""
    if rename is not None:
        vars += f"name='{rename}', "
    if subject is not None:
        vars += f"subject='{subject}', "
    if difficulty is not None:
        vars += f"difficulty={difficulty}, "
    if description is not None:
        vars += f"description='{description}', "

    logging.info(f"Editing idea `{name}` to `{vars[:-2]}`") # LOG

    if vars != '':
        await sql_execute(f"UPDATE ideas SET {vars[:-2]} WHERE name='{name}'")

    await interaction.response.send_message(f"Edited `{name}`")


# -------------------------DELETE-------------------------
@tree.command(name="del", description="Delete an idea", guild=discord.Object(id=GUILD_ID))
@app_commands.autocomplete(name=name_autocomplete)
async def delete_cmd(interaction, name: str):
    logging.info(f"Deleting idea `{name}`") # LOG
    name = name.lower()
    chan = await sql_fetch(f"SELECT * FROM ideas WHERE name='{name}'")
    channel = client.get_channel(chan[0]["project"])
    if channel is not None: await channel.delete()

    await sql_execute(f"DELETE FROM ideas WHERE LOWER(name)='{name}'")

    await interaction.response.send_message(f"Deleted `{name}`")


# -------------------------SHOW-------------------------
@tree.command(name="show", description="Show a specific idea", guild=discord.Object(id=GUILD_ID))
@app_commands.autocomplete(name=name_autocomplete)
async def show_cmd(interaction, name: str):
    logging.info(f"Showing idea `{name}`") # LOG
    name = name.lower()
    result = await sql_fetch(f"SELECT * FROM ideas WHERE LOWER(name)='{name}'")
    result = result[0]
    msg = (f"**Showing idea** `{name}`"
        f"\n**Subject:** `{result['subject']}`"
        f"\n**Creator:** `{result['creator']}`"
        f"\n**Difficulty:** `{result['difficulty']}`"
        f"\n**Description:** `{result['description']}`")
    await interaction.response.send_message(msg)


# -------------------------LIST-------------------------
@tree.command(name="list", description="List all ideas", guild=discord.Object(id=GUILD_ID))
async def list_cmd(interaction):
    logging.info(f"Listing all ideas") # LOG
    result = await sql_fetch("SELECT * FROM ideas")
    msg = "**A list of ideas:**\n"
    await interaction.response.send_message(msg + f"```\n{table(result)}```")


# ===================================PROJECTS===================================
# -------------------------RANDOM-------------------------
@tree.command(name="random", description="Pick a random project", guild=discord.Object(id=GUILD_ID))
async def random_cmd(interaction, difficulty: int = None):
    logging.info(f"Picking random project") # LOG
    if difficulty is None:
        result = await sql_fetch(f"SELECT * FROM ideas WHERE project IS NOT NULL")
    else:
        result = await sql_fetch(f"SELECT * FROM ideas WHERE difficulty={difficulty} AND project IS NOT NULL")
    
    if result != []:
        rnm = random.randint(1, len(result))-1
        await interaction.response.send_message(f"```\n{table([result[rnm]])}```")
    else:
        await interaction.response.send_message("**Project with this difficulty doesn't exist**")


# -------------------------CREATE PROJECT-------------------------
@tree.command(name="create_project", description="Creates a project from an idea", guild=discord.Object(id=GUILD_ID))
@app_commands.autocomplete(name=name_autocomplete)
async def tvoje_mama(interaction, name: str):
    g = interaction.guild
    result = await sql_fetch(f"SELECT * FROM ideas WHERE LOWER(name)='{name}'")
    ids = result[0]['name']
    if result[0]['project'] is None:
        logging.info(f"Creating project from `{name}` in channel `{str(ids)}`") # LOG
        category = discord.utils.get(g.categories, name=CATEGORY_NAME)
        channel = await g.create_text_channel(name=ids, category=category)

        await sql_execute(f"UPDATE ideas SET project={channel.id} WHERE LOWER(name)='{name}'")

        await interaction.response.send_message(
            "The idea **" + str(ids) + "** was turned into a project and channel was created in **" + CATEGORY_NAME + "**")
        description = result[0]["description"]
        await channel.send("**The description:**\n" + f"```{description}```\n=============================================")
    else:
        await interaction.response.send_message(f"`{result[0]['name']}` is already a project")


client.run(TOKEN)
