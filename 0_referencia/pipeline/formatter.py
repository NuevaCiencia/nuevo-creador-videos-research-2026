import os


class GuionFormatter:
    def corregir_gaps(self, segmentos):
        if not segmentos: return []
        ordenados = sorted(segmentos, key=lambda x: x["inicio"])
        corregidos = []

        for i in range(len(ordenados)):
            seg = ordenados[i].copy()
            if i == 0:
                nxt = ordenados[1]["inicio"] if len(ordenados) > 1 else seg["fin"]
                seg["inicio"] = 0.0
                seg["duracion"] = nxt
                seg["fin"] = nxt
            else:
                prev = corregidos[i-1]
                gap = seg["inicio"] - prev["fin"]
                nuevo_inicio = prev["fin"]
                nueva_duracion = seg["duracion"] + gap if gap > 0.001 else seg["duracion"]
                seg["inicio"] = nuevo_inicio
                seg["duracion"] = nueva_duracion
                seg["fin"] = nuevo_inicio + nueva_duracion
            corregidos.append(seg)
        return corregidos

    def exportar(self, segmentos, out_path):
        print("\n📝 Corrigiendo Gaps y formateando Guion Maestro...")
        finales = self.corregir_gaps(segmentos)

        guion = ""
        t_acum = 0.0
        for seg in finales:
            m = int(t_acum // 60)
            s = int(t_acum % 60)
            millis = int((t_acum % 1) * 1000)

            guion += f"#SEGMENT [{m:02d}:{s:02d}.{millis:03d}]\n"
            guion += f"TYPE={seg.get('tipo', 'TEXT').upper()}\n"
            if seg.get('params'):
                guion += f"PARAMS={'//'.join(seg['params'])}\n"
            guion += f"TIME={seg['duracion']:.3f}\n"
            guion += f"TEXT={seg['texto']}\n"
            guion += f"TEXT_STYLE=\nASSET=\nSPEECH={seg['texto']}\nNOTES=\n\n"
            t_acum += seg['duracion']

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(guion)
        print(f"✅ Guion Base exportado en: {out_path}")
