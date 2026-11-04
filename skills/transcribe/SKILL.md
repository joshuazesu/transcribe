---
name: transcribe
description: Transcribe a voice, meeting or call recording on this Mac, with a speaker name on every line, then summarise it. Use when the user shares or names an audio or video file (m4a, mp3, wav, aiff, mp4, mov and similar) and wants a transcript, notes, a summary, action items or "what was said". Also use for first-time setup and for enrolling someone's voice so transcripts label them by name. Runs locally; nothing is uploaded.
argument-hint: "[recording]"
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/setup *) Bash(${CLAUDE_SKILL_DIR}/scripts/transcribe *) Bash(${CLAUDE_SKILL_DIR}/scripts/enroll *) Bash(cat ${CLAUDE_SKILL_DIR}/passage.txt)
---

# Transcribe

Turns a recording into a transcript with a name on every line, using Whisper for the words and pyannote for who said them, all on this Mac. Then you read the transcript and summarise it for the user.

The user may not be technical. Explain each step in plain words, one step at a time, and wait for them where a step needs them.

## Always start with the setup check

```
${CLAUDE_SKILL_DIR}/scripts/setup check
```

It prints a checklist, the data folder, and a last line that is either `READY` or `NEXT: <step>`. If it's `READY`, go to [Transcribing](#transcribing). Otherwise, walk the user through the step it names (below), run the check again, and repeat until it says `READY`. If the user came with a recording, tell them setup comes first, once, and takes about 10 minutes of their time.

## First-time setup

### NEXT: homebrew

Homebrew is the tool that installs the other tools. Ask the user to open the Terminal app, paste the install command shown at https://brew.sh, follow its prompts (it asks for their Mac password), and tell you when it's finished. Don't run it yourself: it needs their password.

### NEXT: install

Tell the user this downloads about 3 GB (the Whisper speech model plus the speaker-ID software) and takes a few minutes depending on their connection. Then run, in the background so the download isn't cut off by a time limit:

```
${CLAUDE_SKILL_DIR}/scripts/setup install
```

Wait for it to finish, then read the checklist it prints at the end.

### NEXT: hf-login

Speaker ID uses a free model from Hugging Face that asks each user to accept its terms. Give the user these steps, with the links:

1. Create a free account at https://huggingface.co/join (skip if they have one).
2. Open https://huggingface.co/pyannote/speaker-diarization-community-1 while logged in, and accept the conditions to access the model (a short form).
3. Create an access token at https://huggingface.co/settings/tokens: choose **Create new token**, type **Read**, any name. Copy it.
4. In the Terminal app (not in this chat), run the command below, using the data folder from the setup check, and paste the token when asked. It can answer `n` to adding the token as a git credential.

   ```
   <data folder>/venv/bin/hf auth login
   ```

Tell them never to paste the token into this chat: the login command stores it on their Mac. When they say it's done, run the setup check again.

### NEXT: hf-access

They're logged in, but the model can't be downloaded. Usually the conditions on https://huggingface.co/pyannote/speaker-diarization-community-1 haven't been accepted with the same account the token belongs to, or the token was deleted. Ask them to check both (and that they're online), then run the check again.

### NEXT: enroll

This teaches the tool the user's voice, so their lines are labelled with their name instead of "Speaker 1".

1. Ask for the name they want on their lines (usually their first name).
2. Show them the passage to read, from `cat ${CLAUDE_SKILL_DIR}/passage.txt`, exactly as it is.
3. Ask them to record themselves reading it aloud: about a minute, in a quiet room, with nobody else talking. The Voice Memos app is easiest. On a Mac, drag the finished memo from Voice Memos onto the Desktop to get a file. On an iPhone, share it to their Mac with AirDrop. Any recording app works.
4. When they give you the file (dragged into the chat or as a path), run:

   ```
   ${CLAUDE_SKILL_DIR}/scripts/enroll "<file>" "<name>"
   ```

5. Run the setup check. When it says `READY`, tell them setup is finished, and that they can delete the practice recording.

If enroll says the recording is too short, ask for a longer one (at least 30 seconds, 60 is better).

## Transcribing

1. **Consent.** If the recording includes other people and the user hasn't said they agreed to be recorded, remind them once, briefly: in many places (for example NSW in Australia, and several US states) everyone in a private conversation has to agree to it being recorded. Don't lecture, and don't refuse.
2. **Speakers.** If the user says how many people are talking, pass `--speakers N`: it makes the speaker split more accurate. If the recording isn't in English, pass `--language <code>` (such as `fr`), or leave it to auto-detect.
3. **Run it in the background**, since a long recording takes minutes (roughly 2 to 4 minutes per hour of audio on Apple Silicon), and wait for it to finish:

   ```
   ${CLAUDE_SKILL_DIR}/scripts/transcribe [--speakers N] "<file>"
   ```

   It writes next to the recording: `<name>.txt` (plain), `<name>.srt` (subtitles) and `<name>.speakers.txt` (a name on every line, like `[00:12] Joshua: ...`). Several files can go in one call.
4. **Read** `<name>.speakers.txt` (or `<name>.txt` if there's no speakers file). Read a long one in parts.
5. **Summarise** what the user asked for. If they didn't say, give:
   - one or two sentences on what the conversation was about, and who took part
   - the key points
   - decisions made
   - action items, with who owns each and any dates
   - open questions or follow-ups
   - a few notable quotes with their timestamps, when they help

   Keep it shorter than the transcript by a long way, and don't invent anything that isn't in it. End with the paths of the transcript files.

People who haven't enrolled appear as "Speaker 1", "Speaker 2" and so on. If it's clear from the conversation who they are (they're greeted by name, say), use the name in the summary and say you inferred it. Speaker changes can be off by a word or two, and a speaker label can be wrong when voices sound alike, so treat odd attributions with care.

## Enrolling someone else

To label a colleague or friend by name, they record themselves reading the passage, with their agreement, and you run `enroll` with their file and name. Enrolling the same name again replaces their voiceprint. Voiceprints are kept in `<data folder>/voiceprints/`, one `.npy` file per person; deleting the file removes that person.
