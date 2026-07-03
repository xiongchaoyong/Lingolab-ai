"""语音对话 Schema — 向后兼容别名，请使用 voice_chat.py"""

from app.schemas.voice_chat import (
    VoiceChatStartRequest as ConversationStartRequest,
    VoiceChatStartResponse as ConversationStartResponse,
    VoiceChatSpeakResponse as ConversationSpeakResponse,
    VoiceChatEndResponse as ConversationEndResponse,
)
