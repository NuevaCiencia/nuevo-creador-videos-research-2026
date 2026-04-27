#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00_restaurar_proyecto.py — Restaurar un proyecto desde un backup ZIP

Descomprime un archivo de deprecated/ en proyectos/ con el nombre indicado,
y restaura los archivos de configuración a la raíz del proyecto.

Uso:
  python 00_restaurar_proyecto.py -z backup_p01_TIMESTAMP.zip -p 01_recuperado
"""

import os
import sys
import shutil
import zipfile
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Restaurar un proyecto desde un backup ZIP")
    parser.add_argument('-z', '--zip', required=True,
                        help='Nombre del archivo ZIP de backup en la carpeta deprecated/')
    parser.add_argument('-p', '--proyecto', required=True,
                        help='Nombre o número de la carpeta destino en proyectos/')
    args = parser.parse_args()

    repo_root = Path(__file__).parent
    deprecated_dir = repo_root / "deprecated"
    proyectos_dir = repo_root / "proyectos"
    
    zip_path = deprecated_dir / args.zip
    dest_path = proyectos_dir / args.proyecto

    print()
    print("=" * 60)
    print("📥  RESTAURAR PROYECTO — creador-videos-mac")
    print("=" * 60)

    # 1. Validaciones iniciales
    if not zip_path.exists():
        print(f"❌ El archivo ZIP no existe: {zip_path}")
        sys.exit(1)

    if dest_path.exists():
        print(f"❌ La carpeta destino ya existe: {dest_path}")
        print("   Por seguridad, elige un nombre diferente para evitar sobreescritura.")
        sys.exit(1)

    print(f"\n📦 Restaurando:")
    print(f"   De: {zip_path.name}")
    print(f"   A:  proyectos/{args.proyecto}/")

    try:
        # 2. Extraer ZIP
        print("\n📂 Extrayendo archivos...")
        dest_path.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(dest_path)
        print("   ✓ Extracción completada.")

        # 3. Restaurar ADN de la carpeta snapshot_config si existe
        snapshot_dir = dest_path / "snapshot_config"
        if snapshot_dir.exists():
            print("\n🧬 Restaurando ADN del proyecto (original_speech y video_config)...")
            for f in snapshot_dir.iterdir():
                # No restauramos ai_config.yaml a la raíz del proyecto porque es global al repo
                if f.name == 'ai_config.yaml':
                    continue
                
                shutil.move(str(f), str(dest_path / f.name))
                print(f"   ✓ {f.name} movido a la raíz de proyectos/{args.proyecto}/")
            
            # Eliminar carpeta temporal de config
            shutil.rmtree(snapshot_dir)
            print("   ✓ Carpeta snapshot_config eliminada.")
        
        # 4. Verificar si los assets están en su lugar
        print("\n✅ RESTAURACIÓN EXITOSA")
        print("=" * 60)
        print(f"""
📋 PRÓXIMOS PASOS:

  1. Verifica que tus assets estén allí:
     proyectos/{args.proyecto}/assets/AUDIO/
     proyectos/{args.proyecto}/assets/images/

  2. Puedes regenerar el video inmediatamente con:
     python 02_generar_video.py -p {args.proyecto}

  3. O modificar el guion primero en:
     proyectos/{args.proyecto}/original_speech.md
""")

    except Exception as e:
        print(f"\n❌ Error durante la restauración: {e}")
        if dest_path.exists():
            print("   Limpiando carpeta de restauración fallida...")
            shutil.rmtree(dest_path)
        sys.exit(1)


if __name__ == "__main__":
    main()
