# Referências de estilo (vídeos que funcionam)

## 1. "COMO ASSIM" (blusinha)
- Hook nos primeiros 3s: palavra em **letras recortadas** (colagem de revista) + frase em **máquina de escrever** com cursor.
- Depois do hook, vídeo limpo, com cortes no ritmo da música.
- Transição de troca de roupa tampando a câmera (pé/mão chegando na lente).

## 2. "POV de dentro da máquina de lavar" (vestido marrom)
Vídeo de 14s, **sem nenhum texto na tela** — a ideia do vídeo é o próprio hook.

| Tempo | O que acontece |
|---|---|
| 0–5s | Câmera dentro do tambor da máquina. Ela tira a peça limpa, mostra o tecido de perto e sorri pra câmera. |
| 5,2–6,8s | **Transição girando**: o quadro roda ~180° como se o tambor estivesse girando, com zoom. |
| 6,8–12s | Ela já aparece **vestindo a peça**, ainda vista "de dentro da máquina": gira, mexe na saia, mostra o caimento. |
| 12–14s | Fecha perto da câmera e manda um beijo. |

Por que funciona:
- **Ângulo inusitado** prende nos primeiros segundos sem precisar de texto.
- Conta uma mini-história real de uso (lavou → vestiu), o que parece experiência e não anúncio.
- Mostra o **antes (peça na mão)** e o **depois (vestida)** em um corte só, com uma transição que "esconde" a troca de roupa.
- Final íntimo (beijo, olhar na câmera) aumenta a vontade de comentar.

Como aplicar com o material que temos:
- Quando houver um trecho da peça sozinha (cabide, caixa, mesa) e outro vestida, usar a **transição girando** entre eles (rotação de 180° + zoom + leve desfoque de movimento, ~0,6s) no lugar do corte seco.
- Para gravar do zero: celular dentro da máquina (porta aberta, tambor limpo e seco), câmera frontal 0,5x, tirar a peça, girar o celular junto com o tambor no fim do take 1, e começar o take 2 já vestida girando no sentido contrário.
- Texto opcional: no máximo uma linha curta no hook; o resto limpo.

## Técnicas do vídeo "17 efeitos de vídeo que o Claude cria" (aprendidas)
Formato: apresentador segura um celular (mockup) que mostra cada efeito com contador "01/17"; título fixo no topo; legendas palavra-a-palavra; CTA "comenta EFEITOS". Os efeitos são implementados em `tiktokshop/scripts/efeitos/efeitos.py` (fn(img, t) -> img):
1. `polaroids` – fotos (frames do próprio vídeo) caem em ângulos aleatórios com sombra
2. `neon_frame` – contorno neon verde pulsante + chamada ("PULA PRA")
3. `bw_keyword` – preto e branco + palavra-chave amarela gigante com "pop"
4. `chat_split` – tela dividida: vídeo em cima, conversa de chat digitando embaixo
5. `scrapbook` – papel kraft, vídeo inclinado com fita, letras recortadas (corta e cola)
6. `doodles` – quadro negro com rabiscos desenhados à mão (coroa, estrela, coração)
7. `duotone_red` – duotone vermelho + pergunta gigante
8. `magazine` – capa de revista (título serifado, foto, selo)
9. `glass_text` – texto gigante "vidro" (desfoque translúcido)
10. `timeline_ui` – timeline de editor com playhead e faixas coloridas
11. `gradient_promo` – card com degradê roxo, título e vídeo arredondado
Ideias da referência ainda não implementadas: mockup de celular na mão, recorte da pessoa (precisa segmentação), efeito de "gravar → mandar → postar" (checklist), página de revista com vários títulos.
Demo: `tiktokshop/scripts/efeitos/demo.py <pasta_frames>` (FONT_DIR = pasta com mont*.ttf).
