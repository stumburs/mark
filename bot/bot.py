from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.twitch import Twitch
import configparser
import asyncio
import backend_subprocess
import re

config = configparser.ConfigParser()

# TODO: Change path
config.read("bot/config.ini")

# Bot
APP_ID = config.get('AUTH', 'ClientID')
APP_SECRET = config.get('AUTH', 'ClientSecret')
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]
TARGET_CHANNEL = config.get('AUTH', 'TargetChannel')

# Markov
TRAIN_ON_CHAT = config.getboolean('MARKOV', 'TrainOnChat', fallback=True)
NGRAM_PATH = config.get('MARKOV', 'NgramPath', fallback="data.bin")
SPLIT_STRATEGY = config.get("MARKOV", "SplitStrategy", fallback="word").lower()
CHARACTER_COUNT = config.getint("MARKOV", "CharacterCount", fallback=4)
AUTOSAVE_INTERVAL = config.getint("MARKOV", "AutosaveInterval", fallback=100)
GENERATE_COMMAND = config.get('MARKOV', 'GenerateCommand', fallback="mark")
LENGTH_TO_GENERATE = config.getint('MARKOV', 'LengthToGenerate', fallback=100)
IGNORE_STREAMELEMENTS = config.getboolean(
    'MARKOV', 'IgnoreStreamElements', fallback=True)
MAX_RETRIES = config.getint("MARKOV", "MaxRetries", fallback=3)


# Autosave counter
message_counter = 0

# URL Filter
URL_REGEX = re.compile(
    r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})",
    re.IGNORECASE
)

# Generation enable toggle
GENERATION_ENABLED: bool = True

# Bad words


def load_txt(path: str) -> set[str]:
    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip().lower() for line in f if line.strip())


BAD_WORDS: set[str] = load_txt("bot/badwords.txt")


def contains_badword(message: str, badwords: set[str]) -> bool:
    words = message.lower().split()
    return any(word in badwords for word in words)


# Ignored users
IGNORED_USERS: set[str] = load_txt("bot/ignoredusers.txt")


async def on_message(msg: ChatMessage):
    global message_counter

    # filter out commands
    if msg.text.startswith("!"):
        return

    # ignore specific users
    if msg.user.name.lower() in IGNORED_USERS:
        print(f"Ignoring {msg.user.name}")
        return

    # filter out messages with links
    if URL_REGEX.search(msg.text):
        return

    # filter out bad words
    if contains_badword(msg.text, badwords=BAD_WORDS):
        return

    print(f'{msg.user.display_name}: {msg.text}')

    # train bot
    if TRAIN_ON_CHAT:
        print(await backend_subprocess.build_ngrams_async(
            split_strategy=SPLIT_STRATEGY, character_count=CHARACTER_COUNT, new_text=msg.text))

        message_counter += 1

        if message_counter >= AUTOSAVE_INTERVAL:
            message_counter = 0
            await backend_subprocess.save_ngrams_async(path=NGRAM_PATH)


async def on_ready(ready_event: EventData):
    await ready_event.chat.join_room(TARGET_CHANNEL)

    print(f'Bot succesfully connected to {TARGET_CHANNEL}')

    # Start up markov
    print("Setting up Markov")
    print(backend_subprocess.proc.stdout.readline())
    print(await backend_subprocess.load_ngrams_async(path=NGRAM_PATH))


async def mark_command(cmd: ChatCommand):
    if not GENERATION_ENABLED:
        return

    for _ in range(MAX_RETRIES):
        generated_text = await backend_subprocess.generate_text_async(length_to_generate=LENGTH_TO_GENERATE)

        if not contains_badword(message=generated_text, badwords=BAD_WORDS):
            await cmd.reply(generated_text)
            return

    await cmd.reply(f"⚠️ Failed to generate clean content after {MAX_RETRIES} attempts.")


async def save_command(cmd: ChatCommand):
    if cmd.user.name == TARGET_CHANNEL.lower():  # only the channel owner can run this command
        print(await backend_subprocess.save_ngrams_async(path=NGRAM_PATH))


async def generation_toggle_command(cmd: ChatCommand):
    global GENERATION_ENABLED
    GENERATION_ENABLED = not GENERATION_ENABLED
    await cmd.reply(f"Generation has been {"ENABLED" if GENERATION_ENABLED else "DISABLED"}.")


async def run_bot():
    bot = await Twitch(app_id=APP_ID, app_secret=APP_SECRET)
    auth = UserAuthenticator(bot, USER_SCOPE)
    token, refresh_token = await auth.authenticate()
    await bot.set_user_authentication(token, USER_SCOPE, refresh_token=refresh_token)

    chat = await Chat(bot)

    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.MESSAGE, on_message)
    chat.register_command(GENERATE_COMMAND, mark_command)
    chat.register_command('save', save_command)  # Debug
    chat.register_command('togglebot', generation_toggle_command)

    chat.start()

    try:
        input('Press ENTER to stop\n')
        await backend_subprocess.save_ngrams_async(path=NGRAM_PATH)
    finally:
        chat.stop()
        await bot.close()

asyncio.run(run_bot())
