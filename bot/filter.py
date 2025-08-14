import re

# URL Filter
URL_REGEX = re.compile(
    r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})",
    re.IGNORECASE
)


# Load a txt with each line as a separate word
def load_txt(path: str) -> set[str]:
    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip().lower() for line in f if line.strip())


# Set of bad words
BAD_WORDS: set[str] = load_txt("bot/badwords.txt")


# Check whether the input string contains a word from the bad words set
def contains_badword(message: str, badwords: set[str]) -> bool:
    words = message.lower().split()
    return any(word in badwords for word in words)


# Ignored users
IGNORED_USERS: set[str] = load_txt("bot/ignoredusers.txt")


# Naughty users
NAUGHTY_USERS: set[str] = set()
