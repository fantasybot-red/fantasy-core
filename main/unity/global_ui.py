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
        
    
  