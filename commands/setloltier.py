import discord
from discord import app_commands
import sqlite3
from datetime import datetime

class RoleView(discord.ui.View):
    def __init__(self, interaction, is_main=True, target_user: discord.Member = None):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.is_main = is_main
        self.target_user = target_user

    @discord.ui.button(label="TOP", style=discord.ButtonStyle.primary)
    async def top_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_tier_modal(interaction, "TOP")

    @discord.ui.button(label="MID", style=discord.ButtonStyle.primary)
    async def mid_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_tier_modal(interaction, "MID")

    @discord.ui.button(label="ADC", style=discord.ButtonStyle.primary)
    async def adc_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_tier_modal(interaction, "ADC")

    @discord.ui.button(label="SUP", style=discord.ButtonStyle.primary)
    async def sup_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_tier_modal(interaction, "SUP")

    @discord.ui.button(label="JUG", style=discord.ButtonStyle.primary)
    async def jug_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_tier_modal(interaction, "JUG")

    async def show_tier_modal(self, interaction: discord.Interaction, role: str):
        modal = TierModal(role, self.is_main, self.target_user)
        await interaction.response.send_modal(modal)

class TierModal(discord.ui.Modal):
    def __init__(self, role: str, is_main: bool, target_user: discord.Member):
        super().__init__(title=f"Enter {'Main' if is_main else 'Sub'} Tier for {role}")
        self.role = role
        self.is_main = is_main
        self.target_user = target_user

        self.tier_input = discord.ui.TextInput(
            label=f"Enter {'Main' if is_main else 'Sub'} Tier",
            placeholder="Enter a number",
            required=True
        )
        self.add_item(self.tier_input)

    def is_update_record(self, user_id, guild_id):
        conn = sqlite3.connect('lol_custum.db')
        cursor = conn.cursor()
        result = bool(cursor.execute(
            "SELECT user_id FROM users WHERE server_id = ? AND user_id = ?",
            (guild_id, user_id)
        ).fetchone())
        conn.close()
        return result

    async def on_submit(self, interaction: discord.Interaction):
        try:
            tier = float(self.tier_input.value)
        except ValueError:
            await interaction.response.send_message("ティアは数値で入力してください。", ephemeral=True)
            return

        user_id = self.target_user.id
        server_id = self.target_user.guild.id

        conn = sqlite3.connect('lol_custum.db')
        cursor = conn.cursor()

        if self.is_main:
            if self.is_update_record(user_id, server_id):
                cursor.execute('''
                    UPDATE users
                    SET main_role = ?, tier = ?, update_date = CURRENT_TIMESTAMP
                    WHERE server_id = ? AND user_id = ?
                ''', (self.role, tier, server_id, user_id))
                await interaction.response.send_message(
                    f"メイン役割 {self.role} とティア {tier} を更新しました！",
                    ephemeral=True
                )
            else:
                cursor.execute('''
                    INSERT INTO users (server_id, user_id, main_role, tier, update_date)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (server_id, user_id, self.role, tier))
                await interaction.response.send_message(
                    f"メイン役割 {self.role} とティア {tier} を設定しました！",
                    ephemeral=True
                )

            conn.commit()
            conn.close()

            # サブ役割の選択を促す
            sub_view = RoleView(interaction, is_main=False, target_user=self.target_user)
            await interaction.followup.send(
                "次にサブ役割を選択してください：",
                view=sub_view,
                ephemeral=True
            )

        else:
            if self.is_update_record(user_id, server_id):
                cursor.execute('''
                    UPDATE users
                    SET sub_role = ?, sub_tier = ?, update_date = CURRENT_TIMESTAMP
                    WHERE server_id = ? AND user_id = ?
                ''', (self.role, tier, server_id, user_id))
                await interaction.response.send_message(
                    f"サブ役割 {self.role} とティア {tier} を更新しました！",
                    ephemeral=True
                )
            else:
                cursor.execute('''
                    INSERT INTO users (server_id, user_id, sub_role, sub_tier, update_date)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (server_id, user_id, self.role, tier))
                await interaction.response.send_message(
                    f"サブ役割 {self.role} とティア {tier} を設定しました！",
                    ephemeral=True
                )

            conn.commit()
            conn.close()

class SetLoLTierView(discord.ui.View):
    def __init__(self, interaction, user: discord.Member):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.user = user

    @discord.ui.button(label="Set Main Tier", style=discord.ButtonStyle.primary)
    async def set_main_tier(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = RoleView(interaction, is_main=True, target_user=self.user)
        await interaction.response.send_message(
            f"{self.user.mention} のLoLティアを設定します。メイン役割を選択してください：",
            view=view,
            ephemeral=True
        )

@app_commands.command()
async def setloltier(interaction: discord.Interaction, user: discord.Member):
    conn = sqlite3.connect('lol_custum.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id INTEGER,
        user_id INTEGER,
        main_role TEXT,
        tier REAL,
        sub_role TEXT,
        sub_tier REAL,
        update_date DATETIME DEFAULT '2000-01-01 00:00:00'
    )
    ''')

    conn.commit()
    conn.close()

    view = RoleView(interaction, is_main=True, target_user=user)
    await interaction.response.send_message(
        f"{user.mention} のLoLティアを設定します。メイン役割を選択してください：",
        view=view,
        ephemeral=True
    )

async def setup(bot):
    bot.tree.add_command(setloltier)