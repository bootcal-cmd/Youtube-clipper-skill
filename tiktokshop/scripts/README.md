# Scripts de edição para TikTok Shop

| Arquivo | O que faz |
|---|---|
| `setup.sh` | Instala ffmpeg, Pillow e baixa as fontes. Rode uma vez por sessão. |
| `macacao.py` | Hook com letras recortadas + legendas em máquina de escrever + 5 CTAs animados (rabisco, 👇, holofote, corações, setinhas). |
| `protesto.py` | Vídeo narrado de protesto: prints da violação com grifos, legendas sincronizadas com a narração. |
| `gemini_tts.py` | Gera a narração com a voz do Gemini (precisa de `GEMINI_API_KEY`). |
| `narracao_protesto.txt` | Texto da narração, uma frase por linha. |

Regras de conteúdo usadas: sem preço, sem medidas, sem forma de pagamento; tom de quem comprou;
CTA só com animação apontando para o link da loja (canto inferior esquerdo, y≈1520–1740 em 1080×1920).

Os vídeos (`*.mp4`) não vão para o git (estão no `.gitignore`).
Os caminhos dos vídeos e prints de origem ficam no topo de cada script — ajuste para os arquivos da sessão.
