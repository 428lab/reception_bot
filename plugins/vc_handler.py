import datetime

class Handler:
    def __init__(self, db):
        self.db = db
        self.info = {
            "name":"vc handler",
            "permission":"user",
            "type":"vc handler",
            "commands":[],
            "version":"0.0.1",
        }


    def get_plugin_info(self):
        return self.info


    def on_voice_state_update(self, server_id, user_id, user_name, before_id, before_name, after_id, after_name):
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
        if before_id is None and after_id:
            text = f'{now_str} - {user_name} が{after_name} に参加しました。'
        elif after_id is None and before_id:
            text = f'{now_str} - {user_name} が{before_name} から出ました。'
        elif after_id is not before_id:
            text = f'{now_str} - {user_name} が{before_name} から {after_name}に移動しました。'
        channels = self.db.get_notify_channels(server_id, 1)
        reaction = {
            "channels": channels,
            "message": text,
            "embed": None,
            "processed": True,
            "through": False,
            "file": None
        }

        return reaction


    def command_vc(self, server_id, server_name, user_id, user_name, channel_id, channel_name, content):
        args = content.split(" ")
        print(args)
        if args[1] == "add":
            # DBに通知チャンネル登録
            self.db.add_notify_chanel(server_id, channel_id)
            text = f"{channel_name}にVC入退出通知を設定しました"
        elif args[1] == "remove":
            # DBに通知チャンネル登録解除
            self.db.remove_notify_chanel(server_id, channel_id)
            text = f"{channel_name}にVC入退出通知を解除しました"

        reaction = {
            "message": text,
            "embed": None,
            "processed": True,
            "through": False,
            "file": None
        }
        return reaction
