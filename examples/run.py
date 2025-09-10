# テスト実行用のモジュール
# タスクトレイのプログラムはIDE上でうまく動かない為、こちらからテストする。
from mylib import *
from discord_bot.discord_bot import DiscordBot
from pathlib import Path

import discord
import asyncio
from discord.ext import commands

if __name__ == "__main__":
    el = EnvLoader( env_path=Path(__file__).parent.parent / ".env" )
    el.load("トークン","TOKEN")
    intents = discord.Intents.all()
    activity = discord.Activity(name="DiscordBot", type=discord.ActivityType.competing)
    bot = commands.Bot(command_prefix='!', intents=intents, activity=activity)
    asyncio.run(bot.add_cog(DiscordBot(bot,el)))
    asyncio.run(bot.start(el.get("TOKEN")))