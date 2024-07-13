from songbird import VoiceClientModel
from unity.music_obj import MusicQueue

class Voice_Client_Music(VoiceClientModel):
    
    async def event_callback(self, event):
        await self.client.db.publish(f"music_client_event:{self.guild.id}", event)
    
    def __init__(self, *args, **kwargs):
        super().__init__("voice_manager", *args, **kwargs)
        self.queue = MusicQueue(self.client, self.guild.id)
        
class Voice_Client_TTS(VoiceClientModel):
    def __init__(self, *args, **kwargs):
        super().__init__("voice_manager", *args, **kwargs)

