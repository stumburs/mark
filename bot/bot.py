from twitchAPI.chat import Chat, EventData, ChatMessage, ChatCommand
from twitchAPI.type import ChatEvent
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.twitch import Twitch
import asyncio
import backend_subprocess
import time
import tts
import filter
import config
from pathlib import Path
import json

CONFIG = config.read_config()


async def load_config(cmd: ChatCommand | None):
    global CONFIG

    if cmd and cmd.user.name != CONFIG.your_name.lower():
        return

    CONFIG = config.read_config()
    if cmd:
        await cmd.reply("Settings updated from config!")

# Autosave counter
message_counter = 0


# Generation enable toggle
GENERATION_ENABLED: bool = True


# Format output
# If output is longer than a single word, remove the first word as it's likely garbage
# Otherwise, keep the single word


def format_output(text: str) -> str:
    words = text.split()
    if len(words) >= 2:
        return ' '.join(words[1:]).strip()
    return text.strip()


# Global Timeout
last_processed_time = 0


async def on_message(msg: ChatMessage):
    global message_counter

    # filter out commands
    if msg.text.startswith("!"):
        return

    # ignore specific users
    if msg.user.name.lower() in filter.IGNORED_USERS:
        print(f"Ignoring {msg.user.name}")
        return

    # filter out messages with links
    if filter.URL_REGEX.search(msg.text):
        return

    # filter out bad words
    if filter.contains_badword(msg.text, badwords=filter.BAD_WORDS):
        return

    print(f'{msg.user.display_name}: {msg.text}')

    # train bot
    if CONFIG.train_on_chat:
        print(await backend_subprocess.build_ngrams_async(
            split_strategy=CONFIG.split_strategy, character_count=CONFIG.character_count, new_text=msg.text))

        message_counter += 1

        if message_counter >= CONFIG.autosave_interval:
            message_counter = 0
            await backend_subprocess.save_ngrams_async(path=CONFIG.ngram_path)


async def on_ready(ready_event: EventData):
    await ready_event.chat.join_room(CONFIG.target_channel)

    print(f'Bot succesfully connected to {CONFIG.target_channel}')

    # Start up markov
    print("Setting up Markov")
    print(backend_subprocess.proc.stdout.readline())
    print(await backend_subprocess.load_ngrams_async(path=CONFIG.ngram_path))


async def mark_command(cmd: ChatCommand):
    global last_processed_time

    if not GENERATION_ENABLED:
        return

    if cmd.user.name.lower() in filter.NAUGHTY_USERS:
        # didn't manage to find a proper solution so we just ignore them
        return

    # global timeout
    now = time.time()
    if now - last_processed_time < CONFIG.message_timeout:
        return

    last_processed_time = now

    for _ in range(CONFIG.max_retries):
        generated_text = format_output(await backend_subprocess.generate_text_async(length_to_generate=CONFIG.length_to_generate))

        if not filter.contains_badword(message=generated_text, badwords=filter.BAD_WORDS):
            await cmd.reply(generated_text)
            # TTS
            if CONFIG.tts_enabled:
                await tts.speak(generated_text, lang=CONFIG.tts_language, tld=CONFIG.tts_tld)
            return

    await cmd.reply(f"⚠️ Failed to generate clean content after {CONFIG.max_retries} attempts.")


async def save_command(cmd: ChatCommand):
    if cmd.user.name == CONFIG.your_name.lower():  # only the bot owner can run this command
        print(await backend_subprocess.save_ngrams_async(path=CONFIG.ngram_path))


async def generation_toggle_command(cmd: ChatCommand):
    global GENERATION_ENABLED
    if cmd.user.name == CONFIG.your_name.lower():  # only the bot owner can run this command
        GENERATION_ENABLED = not GENERATION_ENABLED
        await cmd.reply(f"Generation has been {"ENABLED" if GENERATION_ENABLED else "DISABLED"}.")


async def toggle_naughty_user(cmd: ChatCommand):

    if cmd.user.name != CONFIG.your_name.lower():  # only the bot owner can run this command
        return

    command_text = cmd.text.removeprefix("!naughty").strip()

    if not command_text:
        await cmd.reply("No user specified!")
        return

    naughty_user = command_text.split()[0].lower().removeprefix("@")

    if naughty_user in filter.NAUGHTY_USERS:
        filter.NAUGHTY_USERS.remove(naughty_user)
        await cmd.reply(f"Removed {naughty_user} from naughty list.")
    else:
        filter.NAUGHTY_USERS.add(naughty_user)
        await cmd.reply(f"Added {naughty_user} to naughty list.")


async def say_tts(cmd: ChatCommand):
    if cmd.user.name == CONFIG.your_name.lower():  # only the bot owner can run this command
        command_text = cmd.parameter

        if not command_text:
            await cmd.reply("No text given!")
            return

        await tts.speak(command_text, lang=CONFIG.tts_language, tld=CONFIG.tts_tld)


TOKEN_FILE = Path("bot/bot_tokens.json")


async def run_bot():
    await load_config(None)
    bot = await Twitch(app_id=CONFIG.app_id, app_secret=CONFIG.app_secret)

    if TOKEN_FILE.exists():
        creds = json.loads(TOKEN_FILE.read_text())
        token = creds["token"]
        refresh_token = creds["refresh_token"]
    else:
        auth = UserAuthenticator(bot, CONFIG.user_scope)
        token, refresh_token = await auth.authenticate()
        TOKEN_FILE.write_text(json.dumps(
            {"token": token, "refresh_token": refresh_token}))

    await bot.set_user_authentication(token, CONFIG.user_scope, refresh_token=refresh_token)

    chat = await Chat(bot)

    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.MESSAGE, on_message)
    chat.register_command(CONFIG.generate_command, mark_command)
    chat.register_command('save', save_command)  # Debug
    chat.register_command('togglebot', generation_toggle_command)
    chat.register_command('refreshconfig', load_config)
    chat.register_command('naughty', toggle_naughty_user)
    chat.register_command('tts', say_tts)

    chat.start()

    try:
        input('Press ENTER to stop\n')
        await backend_subprocess.save_ngrams_async(path=CONFIG.ngram_path)
    finally:
        chat.stop()
        await bot.close()

asyncio.run(run_bot())
