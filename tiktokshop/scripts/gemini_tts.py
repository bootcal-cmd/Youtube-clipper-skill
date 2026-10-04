"""Narração com o gerador de voz do Gemini (Google AI Studio).

Lê uma frase por linha de um arquivo de texto e gera narr/<n>.wav + narr/meta.json,
no mesmo formato que protesto.py espera.

Chave: variável de ambiente GEMINI_API_KEY (crie em https://aistudio.google.com/apikey).

uso:
  python3 gemini_tts.py narracao_protesto.txt                 # voz e tom padrão
  python3 gemini_tts.py narracao_protesto.txt --voice Sulafat
  python3 gemini_tts.py --list-models                         # mostra os modelos de voz disponíveis
"""
import argparse, base64, json, os, sys, time, urllib.request, urllib.error, wave

API = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
# Tom pedido para o vídeo de protesto: suave, mas com firmeza.
# As notas de direção ficam separadas da transcrição para a voz NÃO lê-las em voz alta.
DEFAULT_STYLE = ("Voz feminina, português do Brasil. Tom suave e calmo, mas firme e indignado, "
                 "como alguém desabafando com sinceridade. Ritmo natural, sem pressa.")
SR = 24000  # o Gemini devolve PCM 16-bit mono a 24 kHz


def key():
    k = os.environ.get("GEMINI_API_KEY")
    if not k:
        sys.exit("Defina GEMINI_API_KEY nas variáveis de ambiente do ambiente de nuvem.")
    return k


def call(path, body=None):
    req = urllib.request.Request(f"{API}/{path}", data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key()})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Erro {e.code} da API do Gemini: {e.read().decode()[:500]}")


def list_models():
    for m in call("models?pageSize=200").get("models", []):
        if "tts" in m["name"]:
            print(m["name"].removeprefix("models/"))


def speak(text, voice, model, style):
    prompt = (f"### NOTAS DE DIREÇÃO (não leia esta parte)\n{style}\n"
              f"Entre um parágrafo e outro, faça uma pausa longa de cerca de um segundo.\n\n"
              f"### TRANSCRIÇÃO (leia somente isto)\n{text}")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    for attempt in range(4):
        r = call(f"models/{model}:generateContent", body)
        try:
            return base64.b64decode(r["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        except (KeyError, IndexError):
            time.sleep(2 ** attempt)
    sys.exit(f"Resposta sem áudio: {json.dumps(r)[:500]}")


def _silences(pcm, min_len=0.35):
    """trechos de silêncio (início, fim) em amostras"""
    import numpy as np
    fr = int(SR * 0.02); n = len(pcm) // fr
    e = np.sqrt((pcm[: n * fr].astype(np.float32).reshape(n, fr) ** 2).mean(1)) / 32768
    quiet = e < 0.01; out, st = [], None
    for k, q in enumerate(quiet):
        if q and st is None: st = k
        if not q and st is not None:
            if (k - st) * 0.02 >= min_len: out.append((st * fr, k * fr))
            st = None
    return out


def split_points(pcm, n_lines, lengths):
    """escolhe os n-1 silêncios que melhor batem com a posição esperada de cada quebra de frase"""
    sil = [s for s in _silences(pcm) if s[0] > SR * 0.3 and s[1] < len(pcm) - SR * 0.3]
    total = sum(lengths); acc = 0; cuts = []
    for L in lengths[:-1]:
        acc += L; target = len(pcm) * acc / total
        # prefere silêncios longos perto da posição esperada
        best = max(sil, key=lambda s: (s[1] - s[0]) / SR - abs((s[0] + s[1]) / 2 - target) / SR * 0.35)
        cuts.append((best[0] + best[1]) // 2); sil.remove(best)
    return sorted(cuts)


def trim(seg, pad=0.08):
    import numpy as np
    a = np.abs(seg.astype(np.int32)); idx = np.where(a > 400)[0]
    if len(idx) == 0: return seg
    p = int(pad * SR); return seg[max(0, idx[0] - p): idx[-1] + p]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lines_file", nargs="?")
    ap.add_argument("--voice", default="Kore", help="ex.: Kore (firme), Sulafat (calorosa), Achernar (suave), Aoede")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--style", default=DEFAULT_STYLE)
    ap.add_argument("--out", default="narr")
    ap.add_argument("--list-models", action="store_true")
    ap.add_argument("--single", action="store_true", help="uma chamada só para tudo (economiza cota) e corta nas pausas")
    a = ap.parse_args()
    if a.list_models:
        return list_models()
    lines = [l.strip() for l in open(a.lines_file, encoding="utf-8") if l.strip()]
    os.makedirs(a.out, exist_ok=True)
    durs = []
    if a.single:
        import numpy as np
        pcm = np.frombuffer(speak("\n\n".join(lines), a.voice, a.model, a.style), dtype=np.int16)
        cuts = split_points(pcm, len(lines), [len(l) for l in lines])
        for i, (s0, s1) in enumerate(zip([0] + cuts, cuts + [len(pcm)])):
            seg = trim(pcm[s0:s1])
            with wave.open(os.path.join(a.out, f"{i}.wav"), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(seg.tobytes())
            durs.append(round(len(seg) / SR, 2)); print(f"{i}: {durs[-1]}s  {lines[i][:60]}")
        lines_done = True
    else:
        lines_done = False
    for i, line in enumerate([] if lines_done else lines):
        pcm = speak(line, a.voice, a.model, a.style)
        with wave.open(os.path.join(a.out, f"{i}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm)
        durs.append(round(len(pcm) / 2 / SR, 2))
        print(f"{i}: {durs[-1]}s  {line[:60]}")
    json.dump({"sr": SR, "dur": durs, "lines": lines}, open(os.path.join(a.out, "meta.json"), "w"), ensure_ascii=False)
    print("total", round(sum(durs), 2), "s")


if __name__ == "__main__":
    main()
