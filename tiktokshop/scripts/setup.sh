#!/usr/bin/env bash
# Prepara o ambiente: ffmpeg (via pip), Pillow e as fontes Montserrat/Great Vibes usadas nos vídeos.
set -e
cd "$(dirname "$0")"
pip install -q imageio-ffmpeg pillow fonttools brotli soundfile numpy
ln -sf "$(python3 -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())')" /usr/local/bin/ffmpeg
CSS=$(curl -sS -A "Mozilla/5.0 Chrome/120" "https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;800;900&display=swap")
URL=$(echo "$CSS" | grep -o 'https://fonts.gstatic.com/s/montserrat/[^)]*' | tail -1)
curl -sS -o mv.woff2 "$URL"
python3 - <<'PY'
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
for w in (500, 700, 800, 900):
    instancer.instantiateVariableFont(TTFont("mv.woff2"), {"wght": w}).save(f"mont{w}.ttf")
PY
rm -f mv.woff2
echo "ok"
