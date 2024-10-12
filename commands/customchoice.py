import discord
from discord import app_commands
from discord.ui import View, Button
import random

class CustomChoiceView(View):
    def __init__(self, x):
        super().__init__(timeout=None)
        self.participants = set()
        self.x = x

    @discord.ui.button(label="参加", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participants:
            self.participants.add(interaction.user)
            await self.update_message(interaction)
            await interaction.response.send_message("エントリーしたよー", ephemeral=True)
        else:
            await interaction.response.send_message("何回も押すなし。もう参加済みだよ", ephemeral=True)

    @discord.ui.button(label="抜ける", style=discord.ButtonStyle.grey)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participants:
            self.participants.remove(interaction.user)
            await self.update_message(interaction)
            await interaction.response.send_message("逃げるな卑怯者ーー", ephemeral=True)
        else:
            await interaction.response.send_message("そもそも参加してないが", ephemeral=True)

    @discord.ui.button(label="終了", style=discord.ButtonStyle.red)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        winners = self.select_winners()

        for item in self.children:
            item.disabled = True

        if not winners:
            if not self.participants:
                message = "誰も参加してない！！！！"
            else:
                message = f"全員当たりだよ？人足りてないけど。{len(self.participants)} / {self.x}"

            await self.update_message(interaction)
            await interaction.response.send_message(content=message)
            return

        winner_mentions = " ".join([winner.mention for winner in winners])

        await self.update_message(interaction)
        await interaction.response.send_message(content=f"当選者はっぴょー！\n当選者: {winner_mentions}")

    def select_winners(self):
        if len(self.participants) < self.x:
            return []
        return random.sample(list(self.participants), self.x)

    async def update_message(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"{self.x}人が当選するよー！参加ボタン押してね。", color=0x3498db)

        if self.participants:
            participant_list = "\n".join([f"• {participant.mention}" for participant in self.participants])
            embed.add_field(name=f"参加者: {len(self.participants)}", value=participant_list, inline=False)
        else:
            embed.add_field(name="参加者", value="まだ誰も参加していません。", inline=False)

        embed.set_footer(text=f"主催: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        await interaction.message.edit(content=None, embed=embed, view=self)

@app_commands.command()
@app_commands.describe(x="抽選する人数")
async def customchoice(interaction: discord.Interaction, x: int):
    if x <= 0:
        await interaction.response.send_message("抽選人数は1以上の整数を指定してください。")
        return

    view = CustomChoiceView(x)
    embed = discord.Embed(title=f"{x}人が当選するよー！参加ボタン押してね。", color=0x3498db)
    embed.add_field(name="参加者", value="まだ誰も参加していません。", inline=False)
    embed.set_footer(text=f"主催: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed, view=view)