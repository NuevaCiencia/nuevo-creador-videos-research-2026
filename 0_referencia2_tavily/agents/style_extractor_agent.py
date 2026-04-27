import os
import json
import numpy as np
from pathlib import Path
import re
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from .base import call_llm
from config import LLM_MODEL

# Configuración base extraída de config.json de la investigación
TEMPLATES = {
    "A (Directo)": "Escribe un párrafo sobre 'la importancia de la paciencia en el éxito a largo plazo' siguiendo rigurosamente este estilo:",
    "B (Reflexivo)": "Analiza el concepto de 'disciplina diaria' usando el tono, ritmo y vocabulario de estos ejemplos:",
    "C (Dinámico)": "Explica por qué 'el entorno moldea nuestros hábitos' imitando la cadencia de este autor:",
    "D (Metafórico)": "Describe 'el proceso de aprendizaje' usando las metáforas y estructuras típicas de este autor:"
}
TEMPERATURES = [0.4, 0.8]

def load_and_chunk_texts(raw_dir: str, min_words: int = 50, max_words: int = 400) -> list:
    """Reads all txt files in a directory, cleans them, and chunks them by paragraphs."""
    chunks = []
    if not os.path.exists(raw_dir):
        return chunks
        
    for filename in os.listdir(raw_dir):
        if filename.endswith(".txt"):
            filepath = os.path.join(raw_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Basic cleaning
            content = re.sub(r'\s+', ' ', content)
            
            # Simple chunking by approximate word count (split by sentences)
            sentences = re.split(r'(?<=[.!?])\s+', content)
            current_chunk = []
            current_len = 0
            
            for sentence in sentences:
                words = len(sentence.split())
                if current_len + words > max_words and current_len >= min_words:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [sentence]
                    current_len = words
                else:
                    current_chunk.append(sentence)
                    current_len += words
                    
            if current_chunk and current_len >= min_words:
                chunks.append(" ".join(current_chunk))
                
    return chunks

def extract_and_replicate_style(raw_dir: str, progress_callback=None) -> dict:
    """
    Main pipeline to extract style from raw texts and find the best prompt.
    Returns: {"winning_prompt": str, "winning_text": str, "similarity_score": float}
    """
    if progress_callback:
        progress_callback(0.1, "Procesando y dividiendo textos crudos...")
        
    chunks = load_and_chunk_texts(raw_dir)
    if not chunks:
        raise ValueError(f"No se encontraron textos válidos en {raw_dir}")
        
    # We select up to 3 random chunks as reference for the LLM
    import random
    random.seed(42) # For reproducibility in this pipeline
    reference_chunks = random.sample(chunks, min(3, len(chunks)))
    reference_text = "\n---\n".join(reference_chunks)
    
    if progress_callback:
        progress_callback(0.3, "Generando candidatos estilísticos con IA...")
        
    candidates = []
    metadata = []
    
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    errors = []
    # Generate variants
    for t_name, t_prompt in TEMPLATES.items():
        for temp in TEMPERATURES:
            full_prompt = f"{t_prompt}\n\nEJEMPLOS DE REFERENCIA:\n{reference_text}\n\nRESULTADO (Solo el párrafo):"
            
            try:
                response = client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[
                        {"role": "system", "content": "Eres un experto en imitación de estilo literario. Tu objetivo es escribir exactamente como el autor de los ejemplos proporcionados."},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=temp,
                    max_completion_tokens=500
                )
                content = response.choices[0].message.content
                if content:
                    candidates.append(content)
                    # El prompt rector será la instrucción base más los ejemplos que funcionaron
                    prompt_rector = f"Aplica rigurosamente este tono y estilo en tu escritura:\n\nEJEMPLOS DE REFERENCIA DEL AUTOR:\n{reference_text}"
                    metadata.append({
                        'template_name': t_name,
                        'temperature': temp,
                        'prompt_rector': prompt_rector,
                        'text': content
                    })
            except Exception as e:
                errors.append(f"{t_name} (T={temp}): {str(e)}")
                
    if not candidates:
        error_msg = "No se pudo generar ningún candidato literario.\nErrores detectados:\n" + "\n".join(errors)
        raise RuntimeError(error_msg)
        
    if progress_callback:
        progress_callback(0.6, "Evaluando candidatos con StyleDistance...")
        
    # Load Evaluation Model
    os.environ["TRANSFORMERS_NO_TENSORFLOW"] = "1"
    os.environ["USE_TORCH"] = "1"
    
    # Check if we should disable symlinks warning for huggingface hub
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    
    eval_model = SentenceTransformer('StyleDistance/styledistance')
    
    if progress_callback:
        progress_callback(0.8, "Calculando similitud coseno...")
        
    real_emb = eval_model.encode(chunks)
    cand_emb = eval_model.encode(candidates)
    
    # Calculate similarity between each candidate and ALL real chunks
    sim_matrix = cosine_similarity(cand_emb, real_emb)
    
    # The score for a candidate is its average similarity to all real chunks
    cand_scores = sim_matrix.mean(axis=1)
    
    best_idx = np.argmax(cand_scores)
    best_score = cand_scores[best_idx]
    best_candidate = metadata[best_idx]
    
    if progress_callback:
        progress_callback(1.0, "Selección completada.")
        
    return {
        "winning_prompt": best_candidate['prompt_rector'],
        "winning_text": best_candidate['text'],
        "similarity_score": float(best_score),
        "template_used": best_candidate['template_name'],
        "temperature_used": best_candidate['temperature']
    }
