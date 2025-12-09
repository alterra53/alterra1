import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed, ui
import json
import os
from fastapi import FastAPI
import uvicorn
import threading

TOKEN = os.getenv("DISCORD_TOKEN")

DATA_FILE = "guild_data.json"

# -------------------------------------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=4)

guild_data = load_data()

# -------------------------------------------------

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------------------------------  
# FASTAPI KEEPALIVE
# -------------------------------------------------

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

threading.Thread(target=run_fastapi, daemon=True).start()

# -------------------------------------------------
# SETUP COMMANDS
# -------------------------------------------------

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
    except:
        pass

# ---- /setup_channel ----

@bot.tree.command(name="setup_channel", description="Set the current channel as the verification channel.")
async def setup_channel(interaction: Interaction):
    gid = str(interaction.guild_id)

    if gid not in guild_data:
        guild_data[gid] = {}

    guild_data[gid]["verify_channel"] = interaction.channel_id
    save_data(guild_data)

    await interaction.response.send_message(
        f"Verification channel set to: <#{interaction.channel_id}>",
        ephemeral=True
    )

# ---- /setup_role ----

@bot.tree.command(name="setup_role", description="Select the role users will receive after verification.")
@app_commands.describe(role="Choose a role")
async def setup_role(interaction: Interaction, role: discord.Role):
    gid = str(interaction.guild_id)

    if gid not in guild_data:
        guild_data[gid] = {}

    guild_data[gid]["verify_role"] = role.id
    save_data(guild_data)

    await interaction.response.send_message(
        f"Verification role set: `{role.name}`",
        ephemeral=True
    )

# ---- /setup_verify ----

class VerifyButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Verify", style=discord.ButtonStyle.primary, custom_id="alterra_verify")
    async def verify(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message("Well done.", ephemeral=True)

@bot.tree.command(name="setup_verify", description="Create the verification message.")
async def setup_verify(interaction: Interaction):
    gid = str(interaction.guild_id)

    if gid not in guild_data or "verify_channel" not in guild_data[gid]:
        await interaction.response.send_message(
            "You must run /setup_channel first.",
            ephemeral=True
        )
        return

    embed = Embed(
        title="Alterra Verification",
        description="Please complete this verification to access the server systems.",
        color=0xFFA500
    )

    view = VerifyButton()

    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("Verification message created.", ephemeral=True)

# -------------------------------------------------

bot.run(TOKEN)
