import discord
from discord.ext import commands
from mylib import EnvLoader, log, LogType, debug_except
from typing import Callable

class DiscordBot (commands.Cog):
    """DiscordBotをCogで動かすためのクラス

    Args:
        commands (_type_): Extends command.Cog
    """    

    """ =====================================================
        定数
    ======================================================""" 

    FORMAT_MENTION = "{0} \n"
    """メンションのフォーマット
    「～さん」など付ける場合はこの値を変更する
    """

    FROMAT_COMMENT_AUTO_REPLY = f""
    """自動送信メッセージ"""

    def __init__(self, bot, el : EnvLoader) :
        """コンストラクタ

        Args:
            bot (): Cogの仕様で必ずこの名前で受け取る、Cogの初期化時に
            el (EnvLoader): 環境変数を読み込んだものを受け取る
        """
        self.bot = bot
        self.el = el
        self.events = {}

    """ =====================================================
        Discord汎用処理
    ======================================================""" 
    @staticmethod
    async def send_message(channel, message: str, mention="", view: discord.ui.View = None, embeds=None, delete_after = None) :
        """指定されたチャンネルに、指定されたメッセージを送る。

        Args:
            channel (discord.TextChannel): テキストチャンネル
            message (str): メッセージ
            mention (str, optional): メンション先 Defaults to "".
            view (discord.ui.View, optional): メッセージに添付するView Defaults to None.
            delete_after (int, optional): 何秒後に削除するか Defaults to None.
        """
        log(LogType.D, f"{channel.name}チャンネルにメッセージを送信します。")
        await channel.send(
            content=("" if mention == "" else DiscordBot.FORMAT_MENTION.format(mention))
                + message 
                + (DiscordBot.FROMAT_COMMENT_AUTO_REPLY if message != "" else "") , 
            view=view,
            embeds=embeds,
            delete_after=delete_after
        )
        log(LogType.D, f"･･･送信完了しました。")

    @staticmethod
    def get_role(guild:discord.guild, role_id:str) :
        """ロールIDからロールを取得する。

        Args:
            guild (discord.guild): ギルド
            role_id (str): ロールID(intにキャストしない)

        Returns:
            discord.Role: 取得したロール
            False: ロールが存在しない場合False
        """
        role = guild.get_role(int(role_id))
        if role is None:
            log(LogType.E, f"ロール【{role_id}】が取得できませんでした。")
            return False
        return role
    
    @staticmethod
    def get_channel(guild:discord.guild, channel_id: str) :
        """チャンネルIDからチャンネルを取得する。

        Args:
            guild (discord.guild): ギルド
            channel_id (str): チャンネルID(intにキャストしない)

        Returns:
            discord.Channel: 取得したチャンネル
            False: チャンネルが存在しない場合False
        """
        channel = guild.get_channel(int(channel_id))
        if channel is None:
            log(LogType.E, f"チャンネル【{channel_id}】が取得できませんでした。")
            return False
        return channel    

    """ =====================================================
        Botイベント
    ======================================================""" 
    @commands.Cog.listener()
    async def on_interaction(self, interaction:discord.Interaction):
        """インタラクション発生時の処理
        viewのコンポーネントは通常Botのタスクが終了した時点で、
        インスタンスを破棄してしまうため、コンポーネントのイベントが
        正しく拾うことができない。
        そのため、viewのインスタンスが破棄されても同じ動作をしたいものは
        ここで拾って、カスタムIDで紐づけした関数をCALLする。

        Args:
            interaction (discord.Interaction): インタラクション
        """
        try:
            if interaction.data['component_type'] == 2:
                # ボタン
                await self.on_button_click(interaction)
            if interaction.data['component_type'] == 3:
                # リスト
                await self.on_list_change(interaction)
        except KeyError as e:
            # イベント非発生時は、component_typeがデータに入ってこないため、
            # KeyError のExceptionを無視するようにハンドリング
            pass

    async def on_button_click(self, interaction:discord.Interaction):
        """ボタン押下時に呼ばれる処理

        Args:
            interaction (discord.Interaction): インタラクション
        """
        # 事前に登録されたイベントを取得する
        # ボタンのカスタムIDに、事前に登録されたカスタムIDが含まれるものが対象
        custom_id = interaction.data["custom_id"]
        event_func = dict(filter(lambda item:  item[0] in custom_id ,self.events.items()))

        if len(event_func) > 0 : 
            # 引数の解読
            args_str = custom_id.replace(list(event_func.keys())[0] + "_", "")
            args = args_str.split("-")
           
            # 登録されたイベントを実行する
            await list(event_func.values())[0](interaction, args)
        else: 
            log(LogType.E, f"カスタムID[{custom_id}]に対するイベントが登録されていません。")
    
    async def on_list_change(self, interaction:discord.Interaction):
        """セレクト変更時に呼ばれる処理

        Args:
            interaction (discord.Interaction): インタラクション
        """
        # ひとまずボタン押下時と同様の処理とする。
        await self.on_button_click(interaction)


    @commands.Cog.listener()
    async def on_ready(self):
        log(LogType.I, f"{self.bot.user}としてログインしました。")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """サーバにユーザ参加時の動作

        Args:
            member (discord.Member): 参加したメンバー
        """
        pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """メッセージ受信時の動作

        Args:
            message (discord.Message): _description_
        """
        pass

    """ =====================================================
        独自関数
    ======================================================""" 
    def regist_event(self, custom_id:str, func):
        """イベント登録処理
        ボタン押下時やリスト変更時などの、
        当クラスでインタラクションから拾うイベント発生時に実行する関数を、
        カスタムIDと紐づけを行う。

        Args:
            custom_id (str): カスタムID
            func (_type_): 実行する関数
        """
        self.events[custom_id] = func
