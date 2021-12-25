
class Handler:
    def __init__(self, db):
        self.db = db
        self.info = {
            "name":"register",
            "permission":"user",
            "type":"command",
            "commands":["!vc"],
            "version":"0.0.1",
        }


    def get_plugin_info(self):
        return self.info


    def on_message(self, server_id, server_name, user_id, user_name, channel_id, channel_name, content, command):
        if command.startswith(self.info["commands"][0]):
            # vcコマンドの時
            result = self.command_vc(server_id, server_name, user_id, user_name, channel_id, channel_name, content)

        return result


    def command_vc(self, server_id, server_name, user_id, user_name, channel_id, channel_name, content):
        args = content.split(" ")
        print(args)
        if args[1] == "add":
            # DBに通知チャンネル登録
            self.db.add_notify_channel(server_id, channel_id)
            text = f"{channel_name}にVC入退出通知を設定しました"
        elif args[1] == "remove":
            # DBに通知チャンネル登録解除
            self.db.remove_notify_channel(server_id, channel_id)
            text = f"{channel_name}にVC入退出通知を解除しました"

        reaction = {
            "message": text,
            "embed": None,
            "processed": True,
            "through": False,
            "file": None
        }
        return reaction
