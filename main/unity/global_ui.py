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
        self.add_item(discord.ui.Button(emoji="🎶", label="Now Playing", row=2, custom_id="m.nowplaying"))
        self.add_item(discord.ui.Button(emoji="📜", label="Queue", row=2, custom_id="m.queue"))
        self.add_item(discord.ui.Button(label="Reload", row=2, custom_id="m.reload"))
        self.add_item(discord.ui.Select(placeholder="Chọn loop mode",
            options=[
                discord.SelectOption(label='Off', value="off"),
                discord.SelectOption(label='Track', value="track"),
                discord.SelectOption(label='Queue', value="queue")
            ], 
            custom_id="m.loop", row=3))

class Input_Modal(discord.ui.Modal):
    def __init__(self, *, title, custom_id, custom_id_input, label, style=discord.TextStyle.short, min_length=None, max_length=None, placeholder=None):
        super().__init__(timeout=0, title=title, custom_id=custom_id)
        self.add_item(discord.ui.TextInput(custom_id=custom_id_input, style=style, placeholder=placeholder, label=label, min_length=min_length, max_length=max_length))
        
    
  