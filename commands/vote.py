import discord
from discord import app_commands
from discord.ui import View, Button
from typing import List

class VoteView(View):
    def __init__(self, options: List[str]):
        super().__init__(timeout=None)
        self.votes = {option: 0 for option in options}
        self.voters = set()

        for option in options:
            self.add_item(Button(label=option, custom_id=f"vote_{option}", style=discord.ButtonStyle.primary))

        self.add_item(Button(label="投票終了", custom_id="end_vote", style=discord.ButtonStyle.danger))

    async def handle_vote(self, interaction: discord.Interaction, option: str):
        if interaction.user.id in self.voters:
            await interaction.response.send_message("もう投票済みだよ！", ephemeral=True)
            return

        self.votes[option] += 1
        self.voters.add(interaction.user.id)
        await self.update_message(interaction)
        await interaction.response.send_message(f"{option}に投票したよ！", ephemeral=True)

    async def end_vote(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True
        await self.update_message(interaction)
        await interaction.response.send_message("投票が終了しました！", ephemeral=True)

    async def update_message(self, interaction: discord.Interaction):
        embed = discord.Embed(title="投票結果", color=0x3498db)
        for option, count in self.votes.items():
            embed.add_field(name=option, value=f"{count} 票", inline=False)
        embed.set_footer(text=f"総投票数: {len(self.voters)}")
        await interaction.message.edit(embed=embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data["component_type"] == 2:  # Button
            custom_id = interaction.data["custom_id"]
            if custom_id == "end_vote":
                await self.end_vote(interaction)
            else:
                option = custom_id.split("_")[1]
                await self.handle_vote(interaction, option)
        return True

@app_commands.command(name="vote")
@app_commands.describe(
    question="投票の質問",
    option1="選択肢1",
    option2="選択肢2",
    option3="選択肢3（任意）",
    option4="選択肢4（任意）",
    option5="選択肢5（任意）"
)
async def vote(
    interaction: discord.Interaction, 
    question: str, 
    option1: str, 
    option2: str, 
    option3: str = None, 
    option4: str = None, 
    option5: str = None
):
    options = [option for option in [option1, option2, option3, option4, option5] if option]

    if len(options) < 2:
        await interaction.response.send_message("投票には最低2つの選択肢が必要です。", ephemeral=True)
        return

    view = VoteView(options)
    embed = discord.Embed(title=question, color=0x3498db)
    for option in options:
        embed.add_field(name=option, value="0 票", inline=False)
    embed.set_footer(text=f"作成者: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed, view=view)