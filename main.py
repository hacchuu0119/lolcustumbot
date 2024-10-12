import discord
from discord import app_commands
from commands.customchoice import customchoice
from commands.vote import vote
from commands.setloltier import setloltier
from commands.lolcustomteam import lolcustomteam
from commands.lolcustomresults import lolcustomresults
from commands.showloltier import showloltier
from commands.lolcustomwin import lolcustumwin
import sqlite3
from dotenv import load_dotenv
import os


if not os.path.exists('.env'):
    with open('.env', 'w', encoding='utf-8') as env_file:
        env_file.write('TOKEN=あなたのディスコードボットのトークンをここに入力してください')
    print('.envファイルが作成されました。トークンを.envファイルに入力してください。')
    exit()

# 環境変数をロード（必要に応じてエンコーディングを指定）
load_dotenv(override=True)

TOKEN = os.getenv('TOKEN')

if not TOKEN:
    print('TOKENが見つかりません。.envファイルにTOKENを設定してください。')
    exit()

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()

client.tree.add_command(customchoice)
client.tree.add_command(vote)
client.tree.add_command(lolcustomteam)
client.tree.add_command(lolcustomresults)
client.tree.add_command(setloltier)
client.tree.add_command(showloltier)
client.tree.add_command(lolcustumwin)

client.run(TOKEN)