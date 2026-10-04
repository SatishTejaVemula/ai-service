from faster_whisper import WhisperModel

print("Loading Faster Whisper Model...")

model = WhisperModel(
    "base",
    device="cpu",      # change to "cuda" if using NVIDIA GPU
    compute_type="int8"
)

print("Faster Whisper Ready")


def transcribe(path):

    segments, info = model.transcribe(
        path,
        beam_size=5
    )

    text = " ".join(segment.text for segment in segments)

    return text.strip()