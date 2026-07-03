/** 向后兼容 re-export — 所有逻辑已迁移至 voiceChat.js */
export {
  readSSEStream,
  streamStart as streamStartRoleplay,
  streamSpeak as streamSpeakRoleplay,
  startChat as startRoleplay,
  speakChat as speakRoleplay,
  endChat as endRoleplay,
  ttsStreamUrl,
  ttsCachedUrl,
  ttsChat as ttsRoleplay,
} from './voiceChat'
