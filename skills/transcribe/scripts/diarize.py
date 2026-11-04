"""Speaker labelling for Whisper transcripts, using pyannote.

  diarize.py check
      Check that the Hugging Face token works and the gated model can be downloaded.

  diarize.py enroll <wav> <voiceprint.npy>
      Save a voiceprint from a clean recording of one person.

  diarize.py label <wav> <whisper.json> <out.txt> [voiceprint.npy ...] [--speakers N]
      Split the recording by speaker, match speakers to voiceprints,
      and write a transcript with a name on every line.
"""
import json
import sys
import wave
from bisect import bisect_right
from pathlib import Path

import numpy as np

PIPELINE = "pyannote/speaker-diarization-community-1"
MATCH_THRESHOLD = 0.45  # cosine similarity needed to put a name on a speaker


def load_pipeline():
    import torch
    from pyannote.audio import Pipeline

    pipeline = Pipeline.from_pretrained(PIPELINE)
    if pipeline is None:  # older pyannote releases return None instead of raising when access is denied
        raise PermissionError("no access to " + PIPELINE)
    if torch.backends.mps.is_available():
        pipeline.to(torch.device("mps"))  # the Apple Silicon GPU
    return pipeline


def load_wav(path):
    """Read the 16-bit PCM WAV made by ffmpeg, without depending on torchaudio's backends."""
    import torch

    with wave.open(str(path)) as w:
        sr, channels = w.getframerate(), w.getnchannels()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    data = data.reshape(-1, channels).mean(axis=1)
    return {"waveform": torch.from_numpy(data)[None], "sample_rate": sr}


def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def check():
    from huggingface_hub import get_token

    if not get_token():
        print("no-token: not logged in to Hugging Face")
        sys.exit(1)
    try:
        load_pipeline()
    except Exception as e:  # gated repo, bad token or no network
        print(f"no-access: {type(e).__name__}: {str(e).splitlines()[0][:200]}")
        sys.exit(1)
    print("ok")


def enroll(wav_path, out_path):
    pipeline = load_pipeline()
    audio = load_wav(wav_path)
    wav, sr = audio["waveform"], audio["sample_rate"]
    seconds = wav.shape[1] / sr
    if seconds < 20:
        sys.exit(f"The recording is only {seconds:.0f}s long. Record at least 30 seconds (60 is better).")
    # Average 10 s chunks so one cough or pause doesn't skew the voiceprint.
    chunk = 10 * sr
    pieces = [wav[:, i:i + chunk] for i in range(0, wav.shape[1], chunk)]
    pieces = [p for p in pieces if p.shape[1] >= 3 * sr]
    embeddings = [pipeline._embedding(p[None].to(pipeline.device))[0] for p in pieces]
    voiceprint = np.mean(embeddings, axis=0)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path, voiceprint)
    print(f"Saved voiceprint from {len(pieces)} chunks ({seconds:.0f}s) to {out_path}")


def fmt(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def label(wav_path, json_path, out_path, voiceprint_paths, num_speakers=None):
    pipeline = load_pipeline()
    result = pipeline(load_wav(wav_path), num_speakers=num_speakers)
    turns = result.exclusive_speaker_diarization
    labels = result.speaker_diarization.labels()

    # Name each pyannote speaker after the closest voiceprint, if close enough.
    names = {}
    voiceprints = {Path(p).stem.replace("-", " ").title(): np.load(p) for p in voiceprint_paths}
    if result.speaker_embeddings is not None:
        for name, vp in voiceprints.items():
            scores = {lab: cosine(vp, emb) for lab, emb in zip(labels, result.speaker_embeddings)
                      if not np.isnan(emb).any()}
            if not scores:
                continue
            best = max(scores, key=scores.get)
            print(f"{name}: best match {best} (similarity {scores[best]:.2f})", file=sys.stderr)
            if scores[best] >= MATCH_THRESHOLD and best not in names:
                names[best] = name
    others = iter(f"Speaker {i}" for i in range(1, 100))
    for lab in labels:
        if lab not in names:
            names[lab] = next(others)

    # Give each word to whoever most recently started speaking when the word starts, so a
    # speaker change inside a Whisper segment still splits the line. Whisper's word times
    # run late, often by half a second at the end of a turn, so a word that lands in the
    # pause between two turns belongs to the person who was just talking. A word starting
    # within LEAD seconds of the next turn already belongs to the next speaker.
    LEAD = 0.2
    tracks = sorted(turns.itertracks(yield_label=True), key=lambda x: x[0].start)
    starts = [turn.start for turn, _, _ in tracks]

    def speaker_at(t):
        if not tracks:
            return None
        i = max(bisect_right(starts, t + LEAD) - 1, 0)
        return names[tracks[i][2]]

    words = []  # (start, text, end) with sub-word tokens merged into whole words
    for seg in json.loads(Path(json_path).read_text())["transcription"]:
        for tok in seg.get("tokens", []):
            text = tok["text"]
            if text.startswith("[_") or not text.strip():
                continue
            start, end = tok["offsets"]["from"] / 1000, tok["offsets"]["to"] / 1000
            if words and not text.startswith(" "):
                s, w, e = words[-1]
                # Punctuation has its own (often late) timing; don't let it stretch the word
                words[-1] = (s, w + text, end if any(c.isalnum() for c in text) else e)
            else:
                words.append((start, text.strip(), end))

    lines, prev = [], None
    for start, text, end in words:
        speaker = speaker_at(start) or prev or "Unknown"
        if speaker == prev and lines:
            lines[-1] += " " + text
        else:
            lines.append(f"[{fmt(start)}] {speaker}: {text}")
        prev = speaker
    Path(out_path).write_text("\n\n".join(lines) + "\n")
    print(f"Speakers found: {len(labels)} -> {', '.join(names[l] for l in labels)}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, *args = sys.argv[1:]
    if cmd == "check":
        check()
    elif cmd == "enroll":
        enroll(*args)
    elif cmd == "label":
        n = None
        if "--speakers" in args:
            i = args.index("--speakers")
            n = int(args[i + 1])
            args = args[:i] + args[i + 2:]
        label(args[0], args[1], args[2], args[3:], n)
    else:
        sys.exit(__doc__)
