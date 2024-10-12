import discord
from discord import app_commands
import sqlite3

class MatchResult(discord.ui.Modal, title='LoL Custom Match Result'):
    match_id = discord.ui.TextInput(label='Match ID', style=discord.TextStyle.short, placeholder='Enter match ID')
    team_blue = discord.ui.TextInput(label='Blue Team (user_id,k,d,a,dmg;...)', style=discord.TextStyle.paragraph, placeholder='1234,5,3,7,10000;5678,2,4,10,8000;...')
    team_red = discord.ui.TextInput(label='Red Team (user_id,k,d,a,dmg;...)', style=discord.TextStyle.paragraph, placeholder='9012,3,5,6,9000;3456,4,2,8,11000;...')
    winning_side = discord.ui.TextInput(label='Winning Side', style=discord.TextStyle.short, placeholder='blue or red')

    async def on_submit(self, interaction: discord.Interaction):
        conn = sqlite3.connect('lol_custum.db')
        cursor = conn.cursor()

        match_id = int(self.match_id.value)
        winning_side = self.winning_side.value.lower()

        for side, team_data in [('blue', self.team_blue.value), ('red', self.team_red.value)]:
            for player in team_data.split(';'):
                user_id, kills, deaths, assists, damage = map(int, player.split(','))
                win = (side == winning_side)
                cursor.execute('''
                INSERT INTO match_stats (match_id, user_id, kills, deaths, assists, damage, side, win)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (match_id, user_id, kills, deaths, assists, damage, side, win))

        conn.commit()
        conn.close()

        await interaction.response.send_message('Match results have been recorded successfully!', ephemeral=True)

@app_commands.command()
async def lolcustomresults(interaction: discord.Interaction):
    await interaction.response.send_modal(MatchResult())

def setup(bot):
    bot.tree.add_command(lolcustomresults)
