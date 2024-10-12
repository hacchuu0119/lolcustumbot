import asyncio
import discord
from discord import app_commands
import sqlite3
from datetime import datetime

def create_tables():
    conn = sqlite3.connect('lol_custum.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS match_stats (
        match_id INTEGER NOT NULL,
        server_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        win INTEGER NOT NULL,
        kills INTEGER,
        death INTEGER,
        damage INTEGER,
        side TEXT,
        gold INTEGER,
        update_date TEXT NOT NULL,
        PRIMARY KEY (match_id, user_id)
    )''')

    conn.commit()
    conn.close()

create_tables()

class MatchResultView(discord.ui.View):
    def __init__(self, match_id, server_id):
        super().__init__(timeout=None)
        self.match_id = match_id
        self.server_id = server_id
        self.winners = []
        self.losers = []
        self.stage = "winners"
        self.message = None

        # 登録ボタンの追加
        self.add_item(RegisterButton(self))

        # キャンセルボタンの追加
        self.add_item(CancelButton(self))

    async def update_message(self, interaction: discord.Interaction):
        embed = discord.Embed(title="試合結果登録", color=discord.Color.blue())
        embed.add_field(name="Match ID", value=str(self.match_id), inline=False)  # Match ID を追加
        embed.add_field(name="勝者", value="\n".join([player.mention for player in self.winners]) or "未登録", inline=False)
        embed.add_field(name="敗者", value="\n".join([player.mention for player in self.losers]) or "未登録", inline=False)

        if self.stage == "winners":
            embed.add_field(name="次のステップ", value=f"勝者を{5 - len(self.winners)}人メンションしてください。", inline=False)
        elif self.stage == "losers":
            embed.add_field(name="次のステップ", value=f"敗者を{5 - len(self.losers)}人メンションしてください。", inline=False)
        elif self.stage == "completed":
            embed.add_field(name="アクション", value="登録するかキャンセルしてください。", inline=False)

        if self.message:
            await self.message.edit(embed=embed, view=self)
        else:
            self.message = await interaction.followup.send(embed=embed, view=self)

    async def register_results(self, interaction: discord.Interaction):
        conn = sqlite3.connect('lol_custum.db')
        cursor = conn.cursor()

        update_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for winner in self.winners:
            cursor.execute('''INSERT INTO match_stats 
                              (match_id, server_id, user_id, win, update_date) 
                              VALUES (?, ?, ?, 1, ?)''', 
                           (self.match_id, self.server_id, winner.id, update_date))

        for loser in self.losers:
            cursor.execute('''INSERT INTO match_stats 
                              (match_id, server_id, user_id, win, update_date) 
                              VALUES (?, ?, ?, 0, ?)''', 
                           (self.match_id, self.server_id, loser.id, update_date))

        conn.commit()
        conn.close()

        # ボタンを無効化
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        # メッセージを編集して登録完了を表示
        embed = discord.Embed(title="試合結果登録", color=discord.Color.green())
        embed.add_field(name="Match ID", value=str(self.match_id), inline=False)  # Match ID を追加
        embed.add_field(name="勝者", value="\n".join([player.mention for player in self.winners]), inline=False)
        embed.add_field(name="敗者", value="\n".join([player.mention for player in self.losers]), inline=False)
        embed.add_field(name="ステータス", value="試合結果を登録したよ～", inline=False)

        await interaction.message.edit(embed=embed, view=self)

        # ユーザーに確認メッセージを送信
        await interaction.response.send_message("試合結果が登録されました。", ephemeral=True)

        self.stop()

    async def cancel_process(self, interaction: discord.Interaction):
        # ボタンを無効化
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        # メッセージを編集してキャンセルを表示
        embed = discord.Embed(title="試合結果登録", color=discord.Color.red())
        embed.add_field(name="Match ID", value=str(self.match_id), inline=False)  # Match ID を追加
        embed.add_field(name="勝者", value="\n".join([player.mention for player in self.winners]) or "未登録", inline=False)
        embed.add_field(name="敗者", value="\n".join([player.mention for player in self.losers]) or "未登録", inline=False)
        embed.add_field(name="ステータス", value="登録をキャンセルしました。", inline=False)

        await interaction.message.edit(embed=embed, view=self)

        # ユーザーに確認メッセージを送信
        await interaction.response.send_message("登録をキャンセルしました。", ephemeral=True)

        self.stop()

class RegisterButton(discord.ui.Button):
    def __init__(self, parent_view: MatchResultView):
        super().__init__(label="登録", style=discord.ButtonStyle.green)
        self.parent_view = parent_view  # 名前を変更

    async def callback(self, interaction: discord.Interaction):
        if len(self.parent_view.winners) == 5 and len(self.parent_view.losers) == 5:
            await self.parent_view.register_results(interaction)
        else:
            await interaction.response.send_message("勝者と敗者をそれぞれ5人ずつ登録してね", ephemeral=True)

class CancelButton(discord.ui.Button):
    def __init__(self, parent_view: MatchResultView):
        super().__init__(label="キャンセル", style=discord.ButtonStyle.red)
        self.parent_view = parent_view  # 名前を変更

    async def callback(self, interaction: discord.Interaction):
        await self.parent_view.cancel_process(interaction)

@app_commands.command(name="lolcustumwin", description="LoLのカスタム試合結果を登録するよ")
async def lolcustumwin(interaction: discord.Interaction):
    match_id = int(datetime.now().timestamp())
    view = MatchResultView(match_id, interaction.guild_id)
    embed = discord.Embed(title="試合結果登録", description="勝者と敗者を登録して", color=discord.Color.green())
    embed.add_field(name="Match ID", value=str(match_id), inline=False)  # Match ID を追加
    embed.add_field(name="勝者", value="未登録", inline=False)
    embed.add_field(name="敗者", value="未登録", inline=False)
    embed.add_field(name="次のステップ", value="勝者を5人メンションして！", inline=False)

    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    while len(view.winners) < 5 or len(view.losers) < 5:
        try:
            message = await interaction.client.wait_for('message', check=check, timeout=300.0)
            mentions = message.mentions

            if view.stage == "winners":
                for mention in mentions:
                    if len(view.winners) < 5 and mention not in view.winners:
                        view.winners.append(mention)
                if len(view.winners) == 5:
                    view.stage = "losers"
            elif view.stage == "losers":
                for mention in mentions:
                    if len(view.losers) < 5 and mention not in view.losers:
                        view.losers.append(mention)

            # 勝者と敗者が揃ったらステージを完了に設定
            if len(view.winners) == 5 and len(view.losers) == 5:
                view.stage = "completed"

            await view.update_message(interaction)

            if view.stage == "completed":
                break

        except asyncio.TimeoutError:
            # ボタンを無効化
            for item in view.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True

            # メッセージを編集してタイムアウトを表示
            embed = discord.Embed(title="試合結果登録", color=discord.Color.gray())
            embed.add_field(name="Match ID", value=str(match_id), inline=False)  # Match ID を追加
            embed.add_field(name="勝者", value="\n".join([player.mention for player in view.winners]) or "未登録", inline=False)
            embed.add_field(name="敗者", value="\n".join([player.mention for player in view.losers]) or "未登録", inline=False)
            embed.add_field(name="ステータス", value="タイムアウトしました。コマンドを再度実行してください。", inline=False)

            if view.message:
                await view.message.edit(embed=embed, view=view)

            await interaction.followup.send("タイムアウトしました。コマンドを再度実行してください。", ephemeral=True)
            view.stop()
            break