import discord
from discord import app_commands
import sqlite3
import asyncio
from itertools import combinations


def split_into_teams(player_data):
    if not player_data:
        raise ValueError("player_data is empty")
    # 調整後のティアでソート
    adjusted_tiers = [original + adjustment for _, original, adjustment in player_data]
    best_diff = float('inf')
    best_teams = None
    total_sum = sum(adjusted_tiers)
    all_combinations = combinations(range(len(player_data)), len(player_data) // 2)

    for team1_indices in all_combinations:
        team1_sum = sum(adjusted_tiers[i] for i in team1_indices)
        team2_sum = total_sum - team1_sum
        diff = abs(team1_sum - team2_sum)

        if diff < best_diff:
            best_diff = diff
            best_teams = (list(team1_indices), [i for i in range(len(player_data)) if i not in team1_indices])

    return best_teams, best_diff


class TeamButton(discord.ui.Button):
    def __init__(self, label: str):
        super().__init__(style=discord.ButtonStyle.primary, label=label)

    async def callback(self, interaction: discord.Interaction):
        await self.view.add_player(interaction.user, interaction)


class EndButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="終了")

    async def callback(self, interaction: discord.Interaction):
        await self.view.end_team_formation(interaction)


class TeamView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.players = set()
        self.add_item(TeamButton("参加"))
        self.add_item(EndButton())
        self.message = None

    async def add_player(self, user: discord.User, interaction: discord.Interaction):
        if user in self.players:
            await interaction.response.send_message("すでに参加しています。", ephemeral=True)
        else:
            self.players.add(user)
            await self.update_player_list()
            await interaction.response.send_message("参加を受け付けました。", ephemeral=True)

    async def end_team_formation(self, interaction: discord.Interaction):
        await interaction.response.send_message("チーム分けを開始します。", ephemeral=False)
        await self.create_teams(interaction)
        self.stop()

    async def update_player_list(self):
        if self.message:
            embed = discord.Embed(title="参加者リスト", color=discord.Color.blue())
            embed.add_field(name="参加人数", value=f"{len(self.players)}/10", inline=False)
            player_list = "\n".join([player.mention for player in self.players]) or "まだ参加者がいません"
            embed.add_field(name="参加者", value=player_list, inline=False)
            await self.message.edit(embed=embed)

    def calculate_tier_adjustment(self, win_rate: float) -> float:
        adjustment = 0.0
        if win_rate <= 0.3:
            adjustment += 2.4
        if win_rate >= 0.35:
            adjustment += 1.2
        if win_rate >= 0.40:
            adjustment += 0.6
        if win_rate >= 0.45:
            adjustment += 0.3
        if win_rate >= 0.50:
            adjustment = 5.0
        if win_rate >= 0.55:
            adjustment -= 0.3
        if win_rate >= 0.60:
            adjustment -= 0.6
        if win_rate >= 0.65:
            adjustment -= 1.2
        if win_rate >= 0.70:
            adjustment -= 2.4
        return adjustment

    async def create_teams(self, interaction: discord.Interaction):
        conn = sqlite3.connect('lol_custum.db')
        cursor = conn.cursor()

        player_data = []
        for player in self.players:
            cursor.execute("SELECT tier FROM users WHERE user_id = ? AND server_id = ?", (player.id, interaction.guild_id))
            tier_row = cursor.fetchone()

            # ティアがNoneまたはNULLの場合、デフォルト値を設定
            original_tier = 4.0 if (tier_row is None or tier_row[0] is None) else tier_row[0]

            cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN win = 1 THEN 1 ELSE 0 END) as wins FROM match_stats WHERE user_id = ?", (player.id,))
            stats = cursor.fetchone()
            adjustment = 0.0
            if stats and stats[0] >= 10:
                win_rate = stats[1] / stats[0]
                adjustment = self.calculate_tier_adjustment(win_rate)

            player_data.append((player, original_tier, adjustment))

        conn.close()

        # 調整後のティアでソート
        player_data.sort(key=lambda x: x[1] + x[2] if x[1] is not None else float('inf'))

        # チーム分け
        (team1_indices, team2_indices), best_diff = split_into_teams(player_data)

        # チーム表示
        team1_str = "\n".join([
            f"{player_data[i][0].mention} (Tier: {player_data[i][1]:.1f}{f'+{player_data[i][2]:.1f}' if player_data[i][2] >= 0 else f'{player_data[i][2]:.1f}'})"
            for i in team1_indices
        ])
        team2_str = "\n".join([
            f"{player_data[i][0].mention} (Tier: {player_data[i][1]:.1f}{f'+{player_data[i][2]:.1f}' if player_data[i][2] >= 0 else f'{player_data[i][2]:.1f}'})"
            for i in team2_indices
        ])

        embed = discord.Embed(title="チーム分け結果", color=discord.Color.blue())
        embed.add_field(name="チーム1", value=team1_str, inline=False)
        embed.add_field(name="チーム2", value=team2_str, inline=False)

        await interaction.followup.send(embed=embed)


@app_commands.command(name="lolcustomteam", description="LoLのカスタムチームを作成します")
async def lolcustomteam(interaction: discord.Interaction):
    view = TeamView()
    embed = discord.Embed(
        title="LoLカスタムチーム作成",
        description="参加する場合は「参加」ボタンを押してください。",
        color=discord.Color.green()
    )
    embed.add_field(name="参加人数", value="0/10", inline=False)
    embed.add_field(name="参加者", value="まだ参加者がいません", inline=False)

    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()

    # 定期的に参加者リストを更新
    while not view.is_finished():
        await asyncio.sleep(5)  # 5秒ごとに更新
        await view.update_player_list()