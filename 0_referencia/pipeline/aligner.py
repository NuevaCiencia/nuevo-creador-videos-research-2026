import re
from difflib import SequenceMatcher


class SegmentAligner:
    def parse_script(self, text):
        # Eliminar comentarios humanos <# ... #> antes de procesar
        text = re.sub(r'<#.*?#>', '', text, flags=re.DOTALL)
        
        patron = r'<!-- type:(.*?) -->\s*\n*(.*?)(?=<!-- type:|\Z)'
        coincidencias = re.findall(patron, text, re.DOTALL)
        sections = []
        for i, (etiqueta_full, contenido) in enumerate(coincidencias, 1):
            partes = etiqueta_full.strip().split('//')
            etiqueta_tipo = partes[0]
            etiqueta_params = partes[1:] if len(partes) > 1 else []

            texto_limpio = re.sub(r'\s+', ' ', contenido.strip().replace('---', '').replace('"', '').replace("'", ""))
            words = texto_limpio.split()
            sections.append({
                'number': i,
                'type': etiqueta_tipo,
                'params': etiqueta_params,
                'target_words': len(words),
                'last_words': words[-5:] if words else [],
                'text': texto_limpio
            })
        return sections

    def calculate_similarity(self, text1_words, text2_words):
        c1 = [re.sub(r'[^\w]', '', w.lower()) for w in text1_words]
        c2 = [re.sub(r'[^\w]', '', w.lower()) for w in text2_words]
        c1, c2 = [w for w in c1 if w], [w for w in c2 if w]
        if not c1 or not c2: return 0.0
        return SequenceMatcher(None, c1, c2).ratio()

    def alinear(self, bloques_corregidos, original_text):
        print("\n🔍 Alineando Lógica del Guion con Tiempos de Whisper...")
        sections = self.parse_script(original_text)

        all_words = []
        word_to_time = {}
        idx = 0
        for b in bloques_corregidos:
            words = b['text'].split()
            for w in words:
                all_words.append(w)
                word_to_time[idx] = (b['start'], b['end'])
                idx += 1

        segments = []
        current_idx = 0
        for section in sections:
            target = section['target_words']
            last = section['last_words']

            # Ignorar segmentos sin palabras de audio (etiquetas sin locución — p.ej. REMOTION al final del archivo)
            if target == 0:
                tipo = section['type'].strip()
                params = ''.join(section['params']).strip()
                print(f"⚠️ Segmento sin locución ignorado: [{tipo} {params}] — no tiene texto de audio que lo respalde.")
                continue

            # Si ya se agotaron las palabras de Whisper, no crear segmentos fantasma
            if current_idx >= len(all_words):
                tipo = section['type'].strip()
                params = ''.join(section['params']).strip()
                print(f"⚠️ Segmento sin tiempo de audio ignorado: [{tipo} {params}] — se acabó el audio transcrito.")
                continue

            best_count = target
            best_sim = self.calculate_similarity(last, all_words[current_idx:current_idx+target][-5:])

            for offset in range(-50, 51):
                if offset == 0: continue
                test_end = current_idx + target + offset
                if test_end <= current_idx or test_end > len(all_words): continue
                sim = self.calculate_similarity(last, all_words[current_idx:test_end][-5:])
                if sim > best_sim:
                    best_sim = sim
                    best_count = target + offset

            end_idx = min(current_idx + best_count, len(all_words))

            start_time = word_to_time[current_idx][0]
            end_time = word_to_time[end_idx-1][1] if end_idx-1 < len(all_words) else start_time

            text_encontrado = ' '.join(all_words[current_idx:end_idx])
            segments.append({
                'inicio': start_time,
                'fin': end_time,
                'duracion': max(0.01, end_time - start_time),
                'texto': text_encontrado,
                'tipo': section['type'],
                'params': section['params']
            })
            current_idx = end_idx

        print(f"✅ Alineación Completada: {len(segments)} secciones logradas.")
        return segments
