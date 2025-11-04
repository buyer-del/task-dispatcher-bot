# ai.py
# ============================================
#  🔊 Аудіо → Faster-Whisper (українська)
#  🖼️ Зображення → EasyOCR (українська)
# ============================================

from faster_whisper import WhisperModel
import easyocr
from PIL import Image
import numpy as np

# --- Faster-Whisper (локальне розпізнавання аудіо) ---
_model = WhisperModel("small", device="cpu", compute_type="int8")

def transcribe_audio(file_path: str) -> str:
    """
    Розпізнає українську мову з аудіо локально (без інтернету).
    """
    try:
        segments, _ = _model.transcribe(
            file_path,
            language="uk",
            vad_filter=True,
            beam_size=5
        )
        text = " ".join(seg.text for seg in segments).strip()
        return text or "(порожній результат)"
    except Exception as e:
        return f"Помилка транскрипції: {e}"


# --- EasyOCR (розпізнавання тексту з картинок) ---
_reader = easyocr.Reader(["uk"], gpu=False)

def extract_text_from_image(image_path: str) -> str:
    """
    Розпізнає текст українською з зображення (без Tesseract).
    """
    try:
        img = np.array(Image.open(image_path))
        results = _reader.readtext(img, detail=0)
        text = " ".join(results).strip()
        return text or "(текст не розпізнано)"
    except Exception as e:
        return f"Помилка OCR: {e}"
