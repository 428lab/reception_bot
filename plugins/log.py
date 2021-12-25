
class Handler:
    def __init__(self, db):
        self.db = db
        self.info = {
            "name":"log",
            "permission":"user",
            "type":"command",
            "commands":["*"],
            "version":"0.0.1",
        }


    def get_plugin_info(self):
        return self.info


    def on_message(self, server_id, server_name, user_id, user_name, channel_id, channel_name, content, command):
        self.db.discord_log_chat(server_id, channel_id, user_id, content)

        reaction = {
            "message": None,
            "embed": None,
            "processed": True,
            "through": True,
            "file": None
        }

        return reaction

