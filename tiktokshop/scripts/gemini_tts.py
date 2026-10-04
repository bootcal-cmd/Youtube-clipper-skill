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
# Tom pedido para o vídeo de protesto: suave, mas com firmeza
DEFAULT_STYLE = ("Leia em português do Brasil, com voz feminina suave e calma, "
                 "mas firme e indignada, como alguém desabafando com sinceridade. "
                 "Faça pausas naturais nas reticências: ")
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
    body = {"contents": [{"parts": [{"text": style + text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    for attempt in range(4):
        r = call(f"models/{model}:generateContent", body)
        try:
            return base64.b64decode(r["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        except (KeyError, IndexError):
            time.sleep(2 ** attempt)
    sys.exit(f"Resposta sem áudio: {json.dumps(r)[:500]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lines_file", nargs="?")
    ap.add_argument("--voice", default="Kore", help="ex.: Kore (firme), Sulafat (calorosa), Achernar (suave), Aoede")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--style", default=DEFAULT_STYLE)
    ap.add_argument("--out", default="narr")
    ap.add_argument("--list-models", action="store_true")
    a = ap.parse_args()
    if a.list_models:
        return list_models()
    lines = [l.strip() for l in open(a.lines_file, encoding="utf-8") if l.strip()]
    os.makedirs(a.out, exist_ok=True)
    durs = []
    for i, line in enumerate(lines):
        pcm = speak(line, a.voice, a.model, a.style)
        with wave.open(os.path.join(a.out, f"{i}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm)
        durs.append(round(len(pcm) / 2 / SR, 2))
        print(f"{i}: {durs[-1]}s  {line[:60]}")
    json.dump({"sr": SR, "dur": durs, "lines": lines}, open(os.path.join(a.out, "meta.json"), "w"), ensure_ascii=False)
    print("total", round(sum(durs), 2), "s")


if __name__ == "__main__":
    main()
