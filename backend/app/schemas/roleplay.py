"""角色扮演 Schema — 向后兼容别名，请使用 voice_chat.py"""

from app.schemas.voice_chat import (
    VoiceChatStartRequest as RoleplayStartRequest,
    VoiceChatStartResponse as RoleplayStartResponse,
    VoiceChatSpeakResponse as RoleplaySpeakResponse,
    VoiceChatEndResponse as RoleplayEndResponse,
)
