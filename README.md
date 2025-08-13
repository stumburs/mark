# mark

**Mark** is a Twitch chat bot that uses a Markov chain to generate text based on live chat input.  
It can be trained from chat messages in real time, generate random sentences, and respond to commands.

---

## How to Set Up

### 1. Requirements

- **Python 3.13+** (3.12 may work but is untested)
- **C++20 compiler** (C++17 may work but is untested)
- **Make** (optional, for building the C++ backend)
- A Twitch Application

---

### 2️. Installation

1.  Download the repo as a .zip or clone it::

    ```bash
    git clone https://github.com/stumburs/mark.git
    ```

2.  Navigate to the backend directory:

    ```bash
    cd mark/markov
    ```

3.  Build the C++ backend:

    If you have `make` installed, run:

    ```bash
    make
    ```

    If you don't have `make`, you can compile manually with:

    ```bash
    g++ markov.cpp -o markov -Wall -Wextra -O3 -std=c++20
    ```

4.  Configure the Twitch Application:

    - Go to the [Twitch Developer Console](https://dev.twitch.tv/console/apps).
    - Create a new application.
    - Set the OAuth Redirect URL to `http://localhost:17563`. (Important to NOT have '/' at the end).
    - Set the application category to "Chat Bot".
    - Note the **Client ID** and generate a **Client Secret**.

5.  Navigate to the `config.ini` file within the `bot` folder.
    - Fill in the `ClientID` and `ClientSecret` with the values from your Twitch application.
    - Set the `TargetChannel` to the Twitch channel you want the bot to join (e.g., `yourchannelname`).
    - Set the `YourName` to your Twitch username. This user will have exclusive permissions to run certain commands.

---

## Commands

| Command          | Description                                           | Permission |
| ---------------- | ----------------------------------------------------- | ---------- |
| `!mark`          | Generates text.                                       | All        |
| `!save`          | Saves the current ngrams to file bypassing autosaves. | Exclusive  |
| `!togglebot`     | Toggles text generation on/off.                       | Exclusive  |
| `!refreshconfig` | Reloads the bot configuration.                        | Exclusive  |
| `!naughty`       | Toggles a user as "naughty" for filtering.            | Exclusive  |
| `!tts`           | Reads out a message using TTS.                        | Exclusive  |

Exclusive commands can only be run by the user specified in `YourName` in `config.ini`.

## Notes

### Knowledge

The bot uses a Markov chain model stored in `data.bin` (by default). This is loaded (or created if doesn't exist) at startup and updated periodically. By deleting `data.bin`, you can reset the model.

### Bad Words

You can add bad words to `badwords.txt`. This serves two purposes. If the bot receives a message containing a word from the list, it will ignore that message, and will not train on it. Additionally, if the bot manages to generate a message containing a bad word, it will not send that message to the chat. Instead, it will attempt to generate a new message 3 times (by default).

### Ignored Users

You can add users to `ignore.txt`. Messages from these users will not be used for training, and the bot will not respond to them.

### URL Filtering

To prevent link spam, (most) messages containing URLs are filtered from training.
