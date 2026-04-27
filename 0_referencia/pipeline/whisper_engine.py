import os
import torch
import whisperx
import yaml
from pathlib import Path


def _load_ai_config():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, 'ai_config.yaml')
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class WhisperAnalyzer:
    def __init__(self, max_window_s=1.0, min_words=1):
        self.max_window_s = max_window_s
        self.min_words = min_words
        cfg = _load_ai_config().get('whisper', {})
        self.whisper_model = cfg.get('model', 'large-v3')
        self.whisper_language = cfg.get('language', 'es')

    def reconstruir_bloques(self, words):
        bloques, bloque_actual, inicio_bloque = [], [], None
        for w in words:
            if inicio_bloque is None: inicio_bloque = w["start"]
            if w["end"] - inicio_bloque <= self.max_window_s:
                bloque_actual.append(w)
            else:
                if len(bloque_actual) >= self.min_words:
                    bloques.append({"start": inicio_bloque, "end": bloque_actual[-1]["end"], "text": " ".join(x["text"] for x in bloque_actual)})
                bloque_actual = [w]
                inicio_bloque = w["start"]
        if bloque_actual and len(bloque_actual) >= self.min_words:
            bloques.append({"start": inicio_bloque, "end": bloque_actual[-1]["end"], "text": " ".join(x["text"] for x in bloque_actual)})
        return bloques

    def transcribir(self, audio_file, output_dir='output/01_transcripcion'):
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio no encontrado: {audio_file}")

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        print(f"🎙️ WhisperX: Cargando modelo ({self.whisper_model}, language={self.whisper_language})...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "float32"
        model = whisperx.load_model(self.whisper_model, device=device, compute_type=compute_type, language=self.whisper_language)

        print("🎙️ WhisperX: Escuchando el audio...")
        audio = whisperx.load_audio(audio_file)
        seg_result = model.transcribe(audio, batch_size=8, chunk_size=30, print_progress=False, verbose=False)

        print("🎙️ WhisperX: Alineando tiempos...")
        align_model, meta = whisperx.load_align_model(language_code=seg_result["language"], device=device)
        aligned = whisperx.align(seg_result["segments"], align_model, meta, audio, device, return_char_alignments=True)

        words = []
        for seg in aligned["segments"]:
            if "words" in seg and seg["words"]:
                for w in seg["words"]:
                    if w.get("start") is None or w.get("end") is None: continue
                    words.append({"start": w["start"], "end": w["end"], "text": (w.get("text") or w.get("word") or "").strip()})
            else:
                words.append({"start": seg["start"], "end": seg["end"], "text": seg["text"].strip()})

        if not words:
            raise ValueError("No se extrajeron palabras.")

        bloques = self.reconstruir_bloques(words)

        texto_completo = " ".join(w["text"] for w in words)
        with open(os.path.join(output_dir, "transcripcion.txt"), "w", encoding="utf-8") as f:
            f.write(texto_completo)

        with open(os.path.join(output_dir, "subtitulos_formato_personalizado.txt"), "w", encoding="utf-8") as f:
            for b in bloques:
                f.write(f"[{b['start']:.3f} - {b['end']:.3f}]: {b['text']}\n")

        with open(os.path.join(output_dir, "subtitulos.srt"), "w", encoding="utf-8") as f:
            for i, b in enumerate(bloques, start=1):
                f.write(f"{i}\n{b['start']:.3f} --> {b['end']:.3f}\n{b['text']}\n\n")

        print("✅ Generación local de borradores de texto y .srt completada exitosamente.")
        return bloques
