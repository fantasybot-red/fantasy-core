import discord

class delmessbt(discord.ui.Button):
    def __init__(self, userid):
        super().__init__(label="Delete", style=discord.ButtonStyle.red, custom_id=f"delmess.{userid}")

class Bard_bt(discord.ui.Button):
    def __init__(self, userid, chatid):
        super().__init__(label="Reply", style=discord.ButtonStyle.blurple, custom_id=f"bard_ai.{userid}.{chatid}")
        
class Bard_Disabled(discord.ui.Button):
    def __init__(self, userid, chatid):
        super().__init__(label="Reply", style=discord.ButtonStyle.blurple, disabled=True)
        
        
class Music_bt(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=0)
        self.add_item(discord.ui.Button(emoji="⏮️", custom_id="m.previous"))
        self.add_item(discord.ui.Button(emoji="⏯️", custom_id="m.resume|pause"))
        self.add_item(discord.ui.Button(emoji="⏭️", custom_id="m.skip"))
        self.add_item(discord.ui.Button(emoji="🔊", custom_id="m.volume_bt"))
        self.add_item(discord.ui.Select(placeholder="Chọn loop mode",
            options=[
                discord.SelectOption(name='Off', value="off"),
                discord.SelectOption(name='Track', value="track"),
                discord.SelectOption(name='Queue', value="queue")
            ], 
            custom_id="m.loop"))

class Music_Volume(discord.ui.Modal):
    def __init__(self):
        super().__init__(timeout=0, title="Set Volume (từ 0 -> 100)", custom_id="m.volume_md")
        self.add_item(discord.ui.TextInput(custom_id="m.voice_ip", label="Số phần trăm volume", min_length=1, max_length=3))
        
    
  