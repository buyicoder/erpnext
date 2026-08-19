export async function resolveTranslationMessages(initialMessages = {}, remoteMessages) {
  try {
    return { ...initialMessages, ...(await remoteMessages) }
  } catch {
    return initialMessages
  }
}
