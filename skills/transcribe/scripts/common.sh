# Shared paths for the transcribe scripts. Sourced, not run.
# Everything the plugin downloads or creates lives in one folder, outside the plugin,
# so it survives plugin updates. Set TRANSCRIBE_HOME to move it.
TRANSCRIBE_HOME="${TRANSCRIBE_HOME:-$HOME/.local/share/transcribe}"
VENV="$TRANSCRIBE_HOME/venv"
PY="$VENV/bin/python"
MODEL="$TRANSCRIBE_HOME/models/ggml-large-v3-turbo.bin"
MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin"
VOICES="$TRANSCRIBE_HOME/voiceprints"
SCRIPTS="${0:A:h}"

# Homebrew's folders aren't always on PATH when Claude Code runs a command
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# Convert any audio or video file to the 16 kHz mono WAV that Whisper and pyannote expect
to_wav() {
  ffmpeg -loglevel error -y -i "$1" -vn -ar 16000 -ac 1 -c:a pcm_s16le "$2"
}
