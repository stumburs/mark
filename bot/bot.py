from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.twitch import Twitch
import configparser
import asyncio
import backend_subprocess

config = configparser.ConfigParser()

# TODO: Change path
config.read("bot/config.ini")

# Bot
APP_ID = config.get('AUTH', 'ClientID')
APP_SECRET = config.get('AUTH', 'ClientSecret')
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]
TARGET_CHANNEL = config.get('AUTH', 'TargetChannel')

# Markov
TRAIN_ON_CHAT = config.getboolean('MARKOV', 'TrainOnChat')
NGRAM_PATH = config.get('MARKOV', 'NgramPath')
SPLIT_STRATEGY = config.get("MARKOV", "SplitStrategy", fallback="word").lower()
CHARACTER_COUNT = config.getint("MARKOV", "CharacterCount", fallback=4)
AUTOSAVE_INTERVAL = config.getint("MARKOV", "AutosaveInterval", fallback=100)

message_counter = 0


async def on_message(msg: ChatMessage):
    global message_counter

    if msg.text.startswith("!"):
        return

    print(f'{msg.user.display_name}: {msg.text}')

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
    # print(await backend_subprocess.load_source_text_async("alice.txt"))
    # print(await backend_subprocess.build_ngrams_async(split_strategy=SPLIT_STRATEGY, character_count=CHARACTER_COUNT))


async def mark_command(cmd: ChatCommand):
    await cmd.reply(await backend_subprocess.generate_text_async())


async def save_command(cmd: ChatCommand):
    print(await backend_subprocess.save_ngrams_async(path=NGRAM_PATH))


async def run_bot():
    bot = await Twitch(app_id=APP_ID, app_secret=APP_SECRET)
    auth = UserAuthenticator(bot, USER_SCOPE)
    token, refresh_token = await auth.authenticate()
    await bot.set_user_authentication(token, USER_SCOPE, refresh_token=refresh_token)

    chat = await Chat(bot)

    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.MESSAGE, on_message)
    chat.register_command('mark', mark_command)
    chat.register_command('save', save_command)  # Debug

    chat.start()

    try:
        input('Press ENTER to stop\n')
        await backend_subprocess.save_ngrams_async(path=NGRAM_PATH)
    finally:
        chat.stop()
        await bot.close()

asyncio.run(run_bot())
