import type { CreditPack, SupportedLanguage } from "./types"

export const CREDIT_PACKS: CreditPack[] = [
  {
    id: "pack_30",
    name: "Starter",
    credits: 30,
    priceUsd: 999,
  },
  {
    id: "pack_120",
    name: "Pro",
    credits: 120,
    priceUsd: 2999,
    popular: true,
  },
  {
    id: "pack_300",
    name: "Studio",
    credits: 300,
    priceUsd: 5999,
  },
]

export const SOURCE_LANGUAGES: SupportedLanguage[] = [
  { code: "bg", name: "Bulgarian" },
  { code: "ca", name: "Catalan" },
  { code: "cs", name: "Czech" },
  { code: "da", name: "Danish" },
  { code: "de", name: "German" },
  { code: "el", name: "Greek" },
  { code: "en", name: "English" },
  { code: "es", name: "Spanish" },
  { code: "et", name: "Estonian" },
  { code: "fa", name: "Persian / Farsi" },
  { code: "fi", name: "Finnish" },
  { code: "fr", name: "French" },
  { code: "hi", name: "Hindi" },
  { code: "hu", name: "Hungarian" },
  { code: "id", name: "Indonesian" },
  { code: "it", name: "Italian" },
  { code: "ja", name: "Japanese" },
  { code: "ko", name: "Korean" },
  { code: "lt", name: "Lithuanian" },
  { code: "lv", name: "Latvian" },
  { code: "ms", name: "Malay" },
  { code: "nl", name: "Dutch" },
  { code: "nl-BE", name: "Flemish" },
  { code: "no", name: "Norwegian" },
  { code: "pl", name: "Polish" },
  { code: "pt", name: "Portuguese" },
  { code: "ro", name: "Romanian" },
  { code: "ru", name: "Russian" },
  { code: "sk", name: "Slovak" },
  { code: "sv", name: "Swedish" },
  { code: "th", name: "Thai" },
  { code: "tr", name: "Turkish" },
  { code: "uk", name: "Ukrainian" },
  { code: "vi", name: "Vietnamese" },
  { code: "zh", name: "Chinese" },
]

export const SUPPORTED_LANGUAGES: SupportedLanguage[] = [
  { code: "en", name: "English" },
  { code: "es", name: "Spanish" },
  { code: "fr", name: "French" },
  { code: "de", name: "German" },
  { code: "it", name: "Italian" },
  { code: "pt", name: "Portuguese" },
  { code: "nl", name: "Dutch" },
  { code: "ru", name: "Russian" },
  { code: "ja", name: "Japanese" },
  { code: "ko", name: "Korean" },
  { code: "zh", name: "Chinese (Simplified)" },
  { code: "zh-TW", name: "Chinese (Traditional)" },
  { code: "ar", name: "Arabic" },
  { code: "hi", name: "Hindi" },
  { code: "tr", name: "Turkish" },
  { code: "pl", name: "Polish" },
  { code: "sv", name: "Swedish" },
  { code: "da", name: "Danish" },
  { code: "fi", name: "Finnish" },
  { code: "no", name: "Norwegian" },
  { code: "th", name: "Thai" },
  { code: "vi", name: "Vietnamese" },
  { code: "id", name: "Indonesian" },
  { code: "uk", name: "Ukrainian" },
]

export const MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024 // 2GB
export const MAX_DURATION_SECONDS = 3 * 60 * 60 // 3 hours
export const ACCEPTED_VIDEO_TYPES = [
  "video/mp4",
  "video/quicktime",
  "video/webm",
  "video/x-matroska",
]

export const SESSION_COOKIE_NAME = "__session"
export const SESSION_EXPIRY_DAYS = 5

export const SUBTITLE_COLORS = [
  { name: "White", value: "&H00FFFFFF&" },
  { name: "Yellow", value: "&H0000FFFF&" },
  { name: "Green", value: "&H0000FF00&" },
  { name: "Cyan", value: "&H00FFFF00&" },
  { name: "Blue", value: "&H00FF0000&" },
  { name: "Magenta", value: "&H00FF00FF&" },
  { name: "Red", value: "&H000000FF&" },
  { name: "Black", value: "&H00000000&" },
]
