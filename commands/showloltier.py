import discord
from discord import app_commands
import sqlite3

async def setup(bot):
    bot.tree.add_command(showloltier)

def has_manage_channels_permission(interaction: discord.Interaction) -> bool:
    return interaction.user.guild_permissions.manage_channels

@app_commands.command(name="showloltier", description="サーバー内のメンバーのLoLティアと勝率を一覧表示します。")
@app_commands.default_permissions(manage_channels=True)
async def showloltier(interaction: discord.Interaction):
    server_id = interaction.guild_id

    await interaction.response.defer(ephemeral=True)  # コマンド処理中のレスポンス

    # データベースからサーバー内のユーザーのティア情報と勝率を取得し、ソート
    try:
        conn = sqlite3.connect('lol_custum.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.user_id, u.main_role, u.tier,
                   COUNT(m.match_id) as total_matches,
                   SUM(m.win) as total_wins
            FROM users u
            LEFT JOIN match_stats m ON u.user_id = m.user_id AND u.server_id = m.server_id
            WHERE u.server_id = ?
            GROUP BY u.user_id
            ORDER BY u.main_role ASC, u.tier ASC
        ''', (server_id,))
        records = cursor.fetchall()
        conn.close()
        print(f"Fetched {len(records)} records from the database.")
    except Exception as e:
        print(f"Database error: {e}")
        await interaction.followup.send("データベースから情報を取得中にエラーが発生しました。", ephemeral=True)
        return

    if not records:
        await interaction.followup.send("登録されたティア情報がありません。", ephemeral=True)
        return

    # チャンネルの確認
    existing_channel = discord.utils.get(interaction.guild.channels, name="lolティア一覧", type=discord.ChannelType.text)

    if existing_channel:
        # 既存チャンネルのメッセージを削除
        try:
            deleted = await existing_channel.purge()
            print(f"Purged {len(deleted)} messages from existing LoLTierList channel.")
        except discord.Forbidden:
            await interaction.followup.send("チャンネルのメッセージを削除する権限がありません。", ephemeral=True)
            return
        except Exception as e:
            print(f"Error purging messages: {e}")
            await interaction.followup.send("チャンネルのメッセージを削除中にエラーが発生しました。", ephemeral=True)
            return
    else:
        # 新規チャンネルを作成
        try:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False)
            }
            existing_channel = await interaction.guild.create_text_channel(
                'lolティア一覧',
                topic="サーバー内メンバーのLoLティアと勝率一覧",
                overwrites=overwrites
            )
            print(f"Created new channel LoLTierList.")
        except discord.Forbidden:
            await interaction.followup.send("チャンネルを作成する権限がありません。", ephemeral=True)
            return
        except Exception as e:
            print(f"Error creating channel: {e}")
            await interaction.followup.send("チャンネルを作成中にエラーが発生しました。", ephemeral=True)
            return

    # テーブルヘッダーと内容をコードブロックで囲む
    header = f"{'メンバー名':<20} | {'メインロール':<10} | {'メインティア':<8} | {'勝利/試合数 (勝率%)':<20}"
    separator = "-" * len(header)
    table = "```\n"
    table += f"{header}\n{separator}\n"

    # テーブルの行を追加
    for record in records:
        user_id, main_role, tier, total_matches, total_wins = record
        try:
            member = await interaction.guild.fetch_member(user_id)
            if member.bot:  # ボットの場合はスキップ
                continue
        except discord.NotFound:
            print(f"Member with ID {user_id} not found in the guild.")
            continue
        except Exception as e:
            print(f"Error fetching member {user_id}: {e}")
            continue

        member_name = member.display_name
        main_info = main_role if main_role else "未設定"
        tier_info = f"{tier}" if tier else "未設定"

        # 勝率の計算
        if total_matches > 0:
            win_rate = (total_wins / total_matches) * 100
            win_info = f"{total_wins}/{total_matches} ({win_rate:.1f}%)"
        else:
            win_info = "0/0 (0.0%)"

        # 各列の幅を設定し、内容を揃える
        table += f"{member_name:<20} | {main_info:<10} | {tier_info:<8} | {win_info:<20}\n"

    table += "```"

    # メッセージ送信（2000文字制限に対応）
    MAX_MESSAGE_LENGTH = 1990  # 余裕を持って
    if len(table) <= MAX_MESSAGE_LENGTH:
        try:
            await existing_channel.send(table.strip())
            await interaction.followup.send(f"`{existing_channel.name}` チャンネルにLoLティア一覧を投稿しました。", ephemeral=True)
            print("Successfully sent the tier list.")
        except discord.Forbidden:
            await interaction.followup.send("チャンネルにメッセージを送信する権限がありません。", ephemeral=True)
        except Exception as e:
            print(f"Error sending message: {e}")
            await interaction.followup.send("メッセージを送信中にエラーが発生しました。", ephemeral=True)
    else:
        # メッセージが長すぎる場合、分割して送信
        try:
            chunks = []
            current_chunk = "```\n"
            for line in table.strip().split("\n")[1:-1]:  # 最初と最後の```を除外
                if len(current_chunk) + len(line) + 5 > MAX_MESSAGE_LENGTH:
                    current_chunk += "```"
                    chunks.append(current_chunk.strip())
                    current_chunk = "```\n"
                current_chunk += line + "\n"
            if current_chunk != "```\n":
                current_chunk += "```"
                chunks.append(current_chunk.strip())

            for chunk in chunks:
                await existing_channel.send(chunk)

            await interaction.followup.send(f"`{existing_channel.name}` チャンネルにLoLティア一覧を投稿しました。", ephemeral=True)
            print("Successfully sent the tier list in multiple messages.")
        except discord.Forbidden:
            await interaction.followup.send("チャンネルにメッセージを送信する権限がありません。", ephemeral=True)
        except Exception as e:
            print(f"Error sending messages: {e}")
            await interaction.followup.send("メッセージを送信中にエラーが発生しました。", ephemeral=True)

# エラーハンドリング用イベントリスナー
@showloltier.error
async def showloltier_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True)
    else:
        await interaction.response.send_message("エラーが発生しました。再度お試しください。", ephemeral=True)