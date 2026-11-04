# Transcribe

A Claude Code plugin that transcribes recordings on your Mac, with a speaker name on every line, and then has Claude summarise them. Give Claude a voice memo, a meeting or a call recording, and you get back:

- a transcript where every line says who's talking: `[00:12] Joshua: ...`
- a summary: what it was about, key points, decisions, action items with owners, open questions and notable quotes

Everything runs locally. The recording, the transcript and your voiceprint never leave your computer.

It uses [whisper.cpp](https://github.com/ggml-org/whisper.cpp) for the words and [pyannote](https://github.com/pyannote/pyannote-audio) for who said them. A one-time setup records about a minute of your voice, so your lines are labelled with your name instead of "Speaker 1".

## Requirements

- A Mac with Apple Silicon (M1 or later). It may run on an Intel Mac, but slowly.
- [Homebrew](https://brew.sh). Setup tells you how to install it if it's missing.
- About 4 GB of free disk space.
- A free [Hugging Face](https://huggingface.co) account, for the speaker-ID model. Setup walks you through it.

## Install

At the prompt of a Claude Code terminal session:

```
/plugin install transcribe --marketplace joshuazesu/transcribe
```

Answer `y` to add the marketplace, then choose a scope (user scope makes it available in every project). From a shell:

```sh
claude plugin install transcribe --marketplace joshuazesu/transcribe
```

In the desktop app, where `/plugin` doesn't run, click **+** next to the prompt box, then **Plugins**. Choose **Add marketplace** with `joshuazesu/transcribe`, then **Add plugin**.

## First-time setup

Ask Claude something like "set up transcribe", or just give it a recording: it checks the setup first and guides you through whatever's missing. Setup takes about 10 minutes, most of it downloading.

1. **Tools.** Claude installs ffmpeg, whisper-cpp and uv with Homebrew, downloads the Whisper model (`large-v3-turbo`, about 1.6 GB) and sets up the speaker-ID software in its own Python environment (about 1 GB).
2. **Hugging Face.** The speaker-ID model, [pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1), is free but asks you to accept its terms. You create an account, accept the terms on the model page, create a **Read** token, and log in with one command in the Terminal app. Claude gives you the links and the command. The token stays on your Mac: never paste it into the chat.
3. **Your voice.** Claude shows you a short passage. Record yourself reading it aloud, about a minute, alone in a quiet room (Voice Memos works well), and give Claude the file. It saves a voiceprint under the name you choose.

## Use

Give Claude a recording and ask for what you want:

> Transcribe ~/Desktop/team-sync.m4a and summarise it. There were three of us.

> What did we agree on in this call? (with the file dragged into the chat)

You can also run `/transcribe:transcribe <file>`.

Most audio and video formats work: m4a, mp3, wav, aiff, mp4, mov and anything else ffmpeg reads. Next to the recording you get:

| File | What's in it |
| --- | --- |
| `<name>.speakers.txt` | The transcript with a speaker name on every line |
| `<name>.txt` | The plain transcript |
| `<name>.srt` | Subtitles with timestamps |

An hour of audio takes about 2 to 4 minutes on Apple Silicon. Saying how many people are talking makes the speaker split more accurate. Recordings in other languages work too: the language is detected automatically, or you can name it.

People who haven't enrolled show up as "Speaker 1", "Speaker 2" and so on. To label someone else by name, they read the same passage, with their agreement, and you ask Claude to enrol their voice.

## Recording other people

In many places, everyone in a private conversation has to agree before it's recorded: for example New South Wales in Australia, and several US states. Check the rules where you are, and ask first.

## Accuracy

- The words are usually very accurate for clear audio. Crosstalk, heavy background noise and strong accents lower it.
- Speaker changes can be off by a word or two.
- Two people with very similar voices can be mixed up. Telling it the number of speakers helps.
- A voice is matched to a name when its similarity to the voiceprint is at least 0.45. A recording in very different conditions from your enrolment (a bad phone line, say) can fall below that and show as "Speaker 1". Re-enrolling with a recording made in similar conditions helps.

## What it installs, and where

- **Homebrew packages:** `ffmpeg`, `whisper-cpp` and `uv`, if they aren't already installed.
- **Everything else lives in one folder,** `~/.local/share/transcribe` (set `TRANSCRIBE_HOME` to move it):
  - `models/ggml-large-v3-turbo.bin`: the Whisper model
  - `venv/`: Python 3.12 with `pyannote.audio` 4.0.7 and its dependencies (PyTorch and others)
  - `voiceprints/<name>.npy`: one small file per enrolled person, a list of numbers describing their voice. It can't be turned back into audio.
- **Hugging Face's own files:** your login token in `~/.cache/huggingface/token`, and the downloaded speaker-ID model in `~/.cache/huggingface/hub`.

The plugin's scripts are in `skills/transcribe/scripts/`:

- `setup check` shows which setup steps are done, and `setup install` installs what's missing.
- `enroll <recording> <name>` saves a voiceprint.
- `transcribe [--speakers N] [--language CODE] <recording>...` writes the transcripts.
- `diarize.py` does the speaker split and the name matching.

## Privacy

After setup, nothing goes over the network. The recording is converted, transcribed and split by speaker on your Mac. The transcript is written next to the recording, and Claude reads it from there to write the summary. That summary is made by Claude, like anything else you ask it, so the transcript's text goes to Claude as part of your conversation. The audio and your voiceprint don't.

Setup downloads from Homebrew, Hugging Face and the Python package index. The Hugging Face login is only needed to download the speaker-ID model. The setup check also contacts Hugging Face to confirm your access to that model.

pyannote normally sends anonymous usage metrics (audio length, number of speakers, its version) to `otel.pyannote.ai`. The plugin turns that off (`PYANNOTE_METRICS_ENABLED=false`). It also loads the models in offline mode while transcribing and enrolling (`HF_HUB_OFFLINE=1`), so Hugging Face isn't contacted then either.

## Uninstall

```sh
claude plugin uninstall transcribe
rm -rf ~/.local/share/transcribe
```

To also remove the speaker-ID model and your Hugging Face login: `rm -rf ~/.cache/huggingface/hub/models--pyannote--speaker-diarization-community-1`, then `hf auth logout` (or delete `~/.cache/huggingface/token`). The Homebrew packages can go with `brew uninstall whisper-cpp` (and `ffmpeg` or `uv`, if nothing else uses them).

## Credits

- [whisper.cpp](https://github.com/ggml-org/whisper.cpp), running OpenAI's Whisper `large-v3-turbo` model
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) and its `speaker-diarization-community-1` pipeline. See the [model card](https://huggingface.co/pyannote/speaker-diarization-community-1) for its licence and terms.

## License

MIT. See [LICENSE](LICENSE).
