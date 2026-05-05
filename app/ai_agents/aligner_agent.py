"""
Port exacto de:
  0_referencia/pipeline/aligner.py   → SegmentAligner
  0_referencia/pipeline/formatter.py → GuionFormatter

Sin IA — pure Python (difflib).
Adaptado para leer desde DB en lugar de archivos.
"""
import re
import json
from difflib import SequenceMatcher


# ── Tagged script builder ─────────────────────────────────────────────────────

def build_tagged_script(screen_segments) -> str:
    """
    Assembles ScreenSegment DB rows into the tagged script format
    that SegmentAligner.parse_script() expects.

    Python equivalent of app.js buildTaggedScript().
    This is the web-app replacement for 0_referencia's original_speech.md.

    Output format:
        <!-- type:TEXT -->
        narration text

        <!-- type:LIST // @ Title // Item1 // Item2 -->
        narration text
    """
    parts = []
    for seg in screen_segments:
        tag = f"<!-- type:{seg.screen_type.strip()}"
        if seg.params and seg.params.strip():
            tag += f" // {seg.params.strip()}"
        tag += " -->"
        parts.append(f"{tag}\n{seg.narration}")
    return "\n\n".join(parts)


# ── SegmentAligner — exact port ───────────────────────────────────────────────

class SegmentAligner:

    def parse_script(self, text: str) -> list:
        text = re.sub(r'<#.*?#>', '', text, flags=re.DOTALL)
        patron = r'<!-- type:(.*?) -->\s*\n*(.*?)(?=<!-- type:|\Z)'
        coincidencias = re.findall(patron, text, re.DOTALL)
        sections = []
        for i, (etiqueta_full, contenido) in enumerate(coincidencias, 1):
            partes = etiqueta_full.strip().split('//')
            etiqueta_tipo   = partes[0].strip()
            etiqueta_params = [p.strip() for p in partes[1:]] if len(partes) > 1 else []
            texto_limpio = re.sub(
                r'\s+', ' ',
                contenido.strip().replace('---', '').replace('"', '').replace("'", "")
            )
            words = texto_limpio.split()
            sections.append({
                'number':       i,
                'type':         etiqueta_tipo,
                'params':       etiqueta_params,
                'target_words': len(words),
                'last_words':   words[-5:] if words else [],
                'text':         texto_limpio,
            })
        return sections

    def calculate_similarity(self, text1_words: list, text2_words: list) -> float:
        c1 = [re.sub(r'[^\w]', '', w.lower()) for w in text1_words]
        c2 = [re.sub(r'[^\w]', '', w.lower()) for w in text2_words]
        c1 = [w for w in c1 if w]
        c2 = [w for w in c2 if w]
        if not c1 or not c2:
            return 0.0
        return SequenceMatcher(None, c1, c2).ratio()

    def alinear(self, bloques_corregidos: list, original_text: str) -> list:
        """Exact port of SegmentAligner.alinear()"""
        print("\n🔍 Alineando guion con tiempos de Whisper…")
        sections = self.parse_script(original_text)

        all_words: list   = []
        word_to_time: dict = {}
        idx = 0
        for b in bloques_corregidos:
            for w in b['text'].split():
                all_words.append(w)
                word_to_time[idx] = (b['start'], b['end'])
                idx += 1

        segments = []
        current_idx = 0

        for section in sections:
            target = section['target_words']
            last   = section['last_words']

            if target == 0:
                print(f"⚠️ Segmento sin locución ignorado: [{section['type']}]")
                continue
            if current_idx >= len(all_words):
                print(f"⚠️ Audio agotado para: [{section['type']}]")
                continue

            best_count = target
            best_sim   = self.calculate_similarity(
                last, all_words[current_idx:current_idx + target][-5:]
            )

            for offset in range(-50, 51):
                if offset == 0:
                    continue
                test_end = current_idx + target + offset
                if test_end <= current_idx or test_end > len(all_words):
                    continue
                sim = self.calculate_similarity(last, all_words[current_idx:test_end][-5:])
                if sim > best_sim:
                    best_sim   = sim
                    best_count = target + offset

            end_idx    = min(current_idx + best_count, len(all_words))
            start_time = word_to_time[current_idx][0]
            end_time   = word_to_time[end_idx - 1][1] if (end_idx - 1) in word_to_time else start_time

            segments.append({
                'inicio':   start_time,
                'fin':      end_time,
                'duracion': max(0.01, end_time - start_time),
                'texto':    ' '.join(all_words[current_idx:end_idx]),
                'tipo':     section['type'],
                'params':   section['params'],
            })
            current_idx = end_idx

        print(f"✅ Alineación completada: {len(segments)} secciones")
        return segments


# ── GuionFormatter — exact port ───────────────────────────────────────────────

class GuionFormatter:

    def corregir_gaps(self, segmentos: list) -> list:
        if not segmentos:
            return []
        ordenados  = sorted(segmentos, key=lambda x: x["inicio"])
        corregidos = []


        for i, seg in enumerate(ordenados):
            seg = seg.copy()
            if i == 0:
                nxt             = ordenados[1]["inicio"] if len(ordenados) > 1 else seg["fin"]
                seg["inicio"]   = 0.0
                seg["duracion"] = nxt
                seg["fin"]      = nxt
            else:
                prev           = corregidos[i - 1]
                gap            = seg["inicio"] - prev["fin"]
                nuevo_inicio   = prev["fin"]
                nueva_duracion = seg["duracion"] + gap if gap > 0.001 else seg["duracion"]
                seg["inicio"]  = nuevo_inicio
                seg["duracion"]= nueva_duracion
                seg["fin"]     = nuevo_inicio + nueva_duracion
            corregidos.append(seg)
        return corregidos

    def to_text(self, segmentos: list) -> str:
        """Same output as guion_base.txt in 0_referencia."""
        finales = self.corregir_gaps(segmentos)
        lines   = []
        t_acum  = 0.0

        for seg in finales:
            m   = int(t_acum // 60)
            s   = int(t_acum % 60)
            ms  = int((t_acum % 1) * 1000)
            lines.append(f"#SEGMENT [{m:02d}:{s:02d}.{ms:03d}]")
            lines.append(f"TYPE={seg.get('tipo', 'TEXT').upper()}")
            if seg.get('params'):
                lines.append(f"PARAMS={'//'.join(seg['params'])}")
            lines.append(f"TIME={seg['duracion']:.3f}")
            lines.append(f"TEXT={seg['texto']}")
            lines.append(f"TEXT_STYLE=\nASSET=\nSPEECH={seg['texto']}\nNOTES=\n")
            t_acum += seg['duracion']

        return "\n".join(lines)


# ── Entry point ───────────────────────────────────────────────────────────────

def run_alignment(bloques_corregidos: list, screen_segments) -> dict:
    """
    Runs SegmentAligner + GuionFormatter.
    screen_segments: list of ScreenSegment ORM rows (ordered by .order).
    Returns {"segments": [...], "content": "<guion_base.txt text>"}
    """
    tagged_script = build_tagged_script(screen_segments)
    segments      = SegmentAligner().alinear(bloques_corregidos, tagged_script)
    content       = GuionFormatter().to_text(segments)
    return {"segments": segments, "content": content}
