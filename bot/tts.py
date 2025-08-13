import asyncio
from gtts import gTTS
from playsound import playsound
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor

# Create a shared thread pool for blocking calls
_executor = ThreadPoolExecutor()


async def speak(text: str, lang: str = "en", tld: str = "us") -> None:
    # Create a temp MP3 file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        temp_path = fp.name

    try:
        # Run gTTS and playsound in a background thread (since they're blocking)
        def _generate_and_play():
            tts = gTTS(text, lang=lang, tld=tld)
            tts.save(temp_path)
            playsound(temp_path)

        await asyncio.get_event_loop().run_in_executor(_executor, _generate_and_play)

    finally:
        # Cleanup
        os.remove(temp_path)
