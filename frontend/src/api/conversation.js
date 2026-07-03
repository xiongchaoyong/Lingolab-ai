/** 向后兼容 re-export — 所有逻辑已迁移至 voiceChat.js */
export {
  readSSEStream,
  streamStart as streamStartConversation,
  streamSpeak as streamSpeakConversation,
  startChat as startConversation,
  speakChat as speakConversation,
  endChat as endConversation,
  ttsStreamUrl,
  ttsCachedUrl,
  ttsChat as ttsConversation,
  getSessions as getConversationSessions,
} from './voiceChat'
