import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import datetime

import glob
import sys
import importlib
from importlib import import_module
from importlib.abc import MetaPathFinder
from importlib.util import spec_from_file_location

import time

import asyncio

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = os.environ.get("ADMIN_IDS").split(",")

intents = discord.Intents.default()
intents.members = True

def import_module_from_path(name, path):
    class Finder(MetaPathFinder):
        @staticmethod
        def find_spec(fullname, *_):
            if fullname == name:
                return spec_from_file_location(name, path)

    finder = Finder()
    sys.meta_path.insert(0, finder)
    try:
        return import_module(name)
    finally:
        sys.meta_path.remove(finder)


class BotMain(commands.Bot):
    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)
        self.loop_seconds = 0
        self.db = None
        self.modules = []
        self.plugin_handlers = []
        self.reload_all()
        self.sheduled_task.start()


    def load_plugins(self):
        if len(self.modules) > 0:
            self.plugin_handlers = []
            for module in self.modules:
                module = import_module_from_path(os.path.basename(module["name"]), module["path"])                
                plugin_instance = module.Handler(self.db)
                self.plugin_handlers.append(plugin_instance)
                print("reload plugin",plugin_instance.get_plugin_info())
        else:
            self.modules = []
            self.plugin_handlers = []
            plugins = glob.glob('./plugins/*.py')
            for plugin in plugins:
                name = os.path.splitext(os.path.basename(plugin))[0]
                module = import_module_from_path(os.path.basename(name), plugin)
                self.modules.append({"module":module, "name":name, "path":plugin})
                plugin_instance = module.Handler(self.db)
                self.plugin_handlers.append(plugin_instance)
                print("load plugin",plugin_instance.get_plugin_info())


    def load_db(self):
        if self.db:
            importlib.reload(self.db)
        else:
            import db
            self.db = db
        print("load db")


    def reload_all(self):
        self.load_db()
        self.load_plugins()


    @tasks.loop(seconds=10.0)
    async def sheduled_task(self):
        import time
        print("sheduled_task")
        for handler in self.plugin_handlers:
            info = handler.get_plugin_info()
            if info['type'] != "job":
                continue
            if self.loop_seconds % info['period'] == 0:
                start = time.time()
                reactions = handler.on_schedule()
                print(f"{self.loop_seconds} task [{info['name']}] reactions:",len(reactions))
                for reaction in reactions:
                    embed = discord.Embed.from_dict(reaction['embed'])
                    try:
                        channel = self.get_channel(reaction['channel'])
                        if channel:
                            await channel.send(content=f"{reaction['message']}", embed=embed)
                            reaction["callback"]["ok_func"](reaction["callback"]["param"])
                        else:
                            # チャンネルが存在しない
                            reaction["callback"]["error_func"](reaction["callback"]["param"],error_text="404")
                    except Exception as e:
                        print("channel error id:",reaction['channel'])
                        print(e)
                        import traceback
                        trace = traceback.format_exc()
                        reaction["callback"]["error_func"](reaction["callback"]["param"],error_text=trace)
                elapsed_time = round(time.time() - start,2)
                print(f"{self.loop_seconds} task [{info['name']}] elapsed_time:{elapsed_time} sec")

        self.loop_seconds = (self.loop_seconds + 10) % 10000


    @sheduled_task.before_loop
    async def before_sheduled_task(self):
        await self.wait_until_ready()


    async def on_ready(self):
        print('on ready.')
        sys.stdout.flush()


    async def on_member_join(self, member):
        print(f'on_member_join.{member.name}')
        self.db.discord_log_join(member.guild.id, member.id, member.name, member.nick)


    async def on_guild_remove(self, guild):
        print(f'on_member_remove.{guild.name}')
        self.db.discord_log_left(member.guild.id, member.id, member.name, member.nick)


    async def on_voice_state_update(self, member, before, after):
        processed = False
        for handler in self.plugin_handlers:
            info = handler.get_plugin_info()
            if info['type'] == "vc handler":
                server_id = str(member.guild.id)
                member_id = str(member.id)
                member_name = member.name
                before_id = None
                before_name = None
                if before and before.channel:
                    before_id = str(before.channel.id)
                    before_name = str(before.channel.name)

                after_name = None
                after_id = None
                if after and after.channel:
                    after_id = str(after.channel.id)
                    after_name = str(after.channel.name)

                reaction = handler.on_voice_state_update(server_id, member_id, member_name, before_id, before_name, after_id, after_name)
                if reaction["processed"] and not reaction["through"]:
                    processed = True
                    break
        if processed:
            _embed = reaction["embed"]
            if reaction["embed"]:
                embed = discord.Embed(title=_embed["title"],
                                      description=_embed["description"])
                for field in _embed["fields"]:
                    embed.add_field(name=field["disp"],
                                    value=_embed["info"][field['name']],
                                    inline=_embed["info"]["inline"])
            else:
                embed = None

            for channel in reaction["channels"]:
                channel = self.get_channel(int(channel["channel_id"]))
                if channel:
                   await channel.send(content=f"{reaction['message']}", embed=embed)

    async def on_message(self, message):
        try:
            processed = False
            server_id = str(message.guild.id)
            server_name = message.guild.name
            user_id = str(message.author.id)
            user_name = message.author.name
            channel_id = str(message.channel.id)
            channel_name = message.channel.name
            content = message.content

            if content.startswith("!reload") and user_id in ADMIN_IDS:
                self.reload_all()
                texts = "\n".join([f'{handler.info["name"]}:{handler.info["version"]}' for handler in self.plugin_handlers])
                await message.channel.send(content=f"<@{user_id}>\nplugins reloaded.\n{texts}")
                return

            for handler in self.plugin_handlers:
                info = handler.get_plugin_info()
                if info['type'] != "command":
                    continue
                for command in info['commands']:
                    if info['permission'] == "admin":
                        if user_id not in ADMIN_IDS:
                            continue
                    if command == "*":
                        reaction = handler.on_message(server_id, server_name, user_id, user_name, channel_id, channel_name, content, command)
                        if reaction["processed"] and not reaction["through"]:
                            processed = True
                            break
                    elif content.startswith(command):
                        reaction = handler.on_message(server_id, server_name, user_id, user_name, channel_id, channel_name, content, command)
                        if reaction["processed"] and not reaction["through"]:
                            processed = True
                            break
                if processed:
                    # 処理されたら他のハンドラには渡さない
                    break

            if processed:
                if reaction["file"] is None:
                    _embed = reaction["embed"]
                    if reaction["embed"]:
                        embed = discord.Embed(title=_embed["title"],
                                              description=_embed["description"])
                        for field in _embed["fields"]:
                            embed.add_field(name=field["disp"],
                                            value=_embed["info"][field['name']],
                                            inline=_embed["info"]["inline"])
                    else:
                        embed = None

                    await message.channel.send(content=f"<@{user_id}>\n{reaction['message']}", embed=embed)
        except Exception as e:
            print(e)
        sys.stdout.flush()


bot = BotMain(['!', '！'], intents=intents)


if __name__ == '__main__':
    bot.run(BOT_TOKEN)
