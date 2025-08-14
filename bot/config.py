from dataclasses import dataclass
import configparser
from twitchAPI.type import AuthScope


@dataclass
class BotConfig:
    # Auth
    app_id: str
    app_secret: str
    user_scope: str
    target_channel: str
    your_name: str

    # Markov
    ngram_path: str
    split_strategy: str
    character_count: int
    generate_command: str
    train_on_chat: bool
    autosave_interval: int
    length_to_generate: int
    max_retries: int
    message_timeout: int

    # TTS
    tts_enabled: bool
    tts_language: str
    tts_tld: str


def read_config(path="bot/config.ini") -> BotConfig:
    config = configparser.ConfigParser()
    config.read(path)

    return BotConfig(
        # Auth
        app_id=config.get('AUTH', 'ClientID'),
        app_secret=config.get('AUTH', 'ClientSecret'),
        user_scope=[AuthScope.CHAT_READ, AuthScope.CHAT_EDIT],
        target_channel=config.get('AUTH', 'TargetChannel'),
        your_name=config.get('AUTH', 'YourName',
                             fallback=config.get('AUTH', 'TargetChannel')),

        # Markov
        ngram_path=config.get('MARKOV', 'NgramPath', fallback="data.bin"),
        split_strategy=config.get(
            "MARKOV", "SplitStrategy", fallback="word").lower(),
        character_count=config.getint("MARKOV", "CharacterCount", fallback=4),
        generate_command=config.get(
            'MARKOV', 'GenerateCommand', fallback="mark"),
        train_on_chat=config.getboolean(
            'MARKOV', 'TrainOnChat', fallback=True),
        autosave_interval=config.getint(
            "MARKOV", "AutosaveInterval", fallback=100),
        length_to_generate=config.getint(
            'MARKOV', 'LengthToGenerate', fallback=100),
        max_retries=config.getint("MARKOV", "MaxRetries", fallback=3),
        message_timeout=config.getint("MARKOV", "MessageTimeout", fallback=0),

        tts_enabled=config.getboolean('TTS', 'TTS', fallback=False),
        tts_language=config.get('TTS', 'TTSLanguage', fallback="en"),
        tts_tld=config.get('TTS', 'TTSTLD', fallback="co.uk")
    )
