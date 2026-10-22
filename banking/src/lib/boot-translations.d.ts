export function resolveTranslationMessages(
  initialMessages: Record<string, string> | undefined,
  remoteMessages: Promise<Record<string, string>> | undefined,
): Promise<Record<string, string>>
