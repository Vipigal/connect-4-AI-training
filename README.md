# TP1 – Busca Competitiva (Ligue-4)

Agente de IA para **Ligue-4** (*Connect Four*), desenvolvido para a disciplina DCC642 – Introdução à Inteligência Artificial (UFMG, 2026/2). O agente evolui do **Minimax** com profundidade limitada para a **poda Alfa-Beta** e, por fim, para o **Iterative Deepening** com limite de tempo, todos guiados por uma função heurística de avaliação.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `src/search.py` | O agente: Minimax, Alfa-Beta, Iterative Deepening e heurística. Ponto de entrada: `choose_move(board, player, config)`. |
| `src/server.py` | Servidor Flask que serve a interface web (p5.js) e chama o agente. |
| `src/experiments.py` | Script que roda partidas automáticas (sem servidor) e gera as tabelas do relatório. |
| `src/resultados.log` | Saída bruta da execução dos experimentos. |
| `reports/` | Relatório no template AAAI-27. |
| `diretrizes.md` | Enunciado do trabalho. |

## Como executar

```bash
python -m venv tp1-env
source tp1-env/bin/activate
pip install -r src/requirements.txt

cd src
python server.py            # interface em http://localhost:5001
```

Para reproduzir os experimentos:

```bash
cd src
python experiments.py                          # exp. 1, 2 e 3, 10 partidas por confronto
python experiments.py --exp 1 2 -n 20          # escolhe experimentos e número de partidas
python experiments.py --exp 3 --csv out.csv    # salva os resultados agregados em CSV
```

Opções úteis: `--opening` (jogadas aleatórias de abertura nos exp. 2 e 3, padrão 2), `--ab-depth` (profundidade do Alfa-Beta no exp. 3, padrão 5) e `--seed` (padrão 42).

## O agente

**Convenção de pontuação.** O Jogador 1 é sempre o maximizador e o Jogador 2 o minimizador. Estados terminais valem `±1.000.000` (descontada a profundidade, para preferir vitórias mais rápidas e derrotas mais tardias); empate vale 0.

**Minimax.** Busca em profundidade limitada; ao atingir o limite, o estado é avaliado pela heurística.

**Alfa-Beta.** Mesma busca, com poda pelos limites α/β. As colunas são exploradas do centro para as bordas (`3, 2, 4, 1, 5, 0, 6`), o que tende a encontrar boas jogadas cedo e aumentar as podas.

**Iterative Deepening** (`choose_move`). Executa o Alfa-Beta com profundidades 1, 2, 3, … até `max_depth` ou até o tempo acabar, guardando sempre a melhor jogada da última iteração completa. O estouro de tempo é sinalizado por uma exceção (`SearchTimeout`) que aborta a iteração em andamento; uma margem de segurança de 200 ms garante que a resposta chegue antes do limite do servidor. A busca para cedo se encontrar uma vitória ou derrota forçada.

**Heurística.** `h(s) = pontos(P1) − pontos(P2)`, onde os pontos de cada jogador somam:

- **Sequências vivas:** para cada janela de 4 casas (horizontal, vertical e nas duas diagonais) que contém apenas peças do jogador e casas vazias, +3 se houver 2 peças e +20 se houver 3.
- **Controle do centro:** +1 por peça na região 3×3 central inferior do tabuleiro (as 3 linhas de baixo das colunas 2–4).

## Metodologia dos experimentos

- Cada confronto alterna quem começa a cada partida; os resultados são reportados do ponto de vista do agente A.
- Como Minimax e Alfa-Beta são determinísticos, os exp. 2 e 3 começam com 2 jogadas aleatórias de abertura para gerar partidas distintas.
- Os nós visitados são contados envolvendo as funções de busca, sem alterar o `search.py`.
- No exp. 3, a profundidade do ID é a da última iteração **completa** antes do estouro de tempo.

## Resultados

> ⚠️ **Pendente:** as métricas finais ainda estão sendo coletadas. As tabelas abaixo serão preenchidas com a saída de `experiments.py`.

### Experimento 1 – Minimax vs. Aleatório

| Profundidade | V / E / D | Taxa de vitória | Tempo médio/jogada (ms) | Nós/jogada |
|---|---|---|---|---|
| 2 | _TODO_ | _TODO_ | _TODO_ | _TODO_ |
| 3 | _TODO_ | _TODO_ | _TODO_ | _TODO_ |
| 4 | _TODO_ | _TODO_ | _TODO_ | _TODO_ |
| 5 | _TODO_ | _TODO_ | _TODO_ | _TODO_ |

### Experimento 2 – Alfa-Beta vs. Minimax (sem poda)

| Profundidade | V / E / D (AB) | Taxa de vitória (AB) | Tempo/jogada AB (ms) | Tempo/jogada MM (ms) | Nós/jogada AB | Nós/jogada MM | Redução de nós |
|---|---|---|---|---|---|---|---|
| 2 | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ |
| 3 | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ |
| 4 | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ |
| 5 | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ |

### Experimento 3 – Iterative Deepening vs. Alfa-Beta (d=5)

| Limite de tempo | V / E / D (ID) | Taxa de vitória (ID) | Tempo/jogada ID (ms) | Tempo/jogada AB (ms) | Prof. média ID | Nós/jogada ID | Nós/jogada AB |
|---|---|---|---|---|---|---|---|
| 1 s | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ |
| 2 s | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ |

### Experimento 4 – IA vs. jogador humano

_TODO: resultado das (≥ 5) partidas e percepções qualitativas — forças e fraquezas observadas._

### Discussão

_TODO: principais conclusões após a coleta (impacto da profundidade no tempo e na qualidade, ganho da poda, profundidade alcançada pelo ID em cada limite de tempo)._

## Limitações e próximos passos

- A heurística não distingue ameaças jogáveis imediatamente de ameaças "flutuantes" (que dependem de casas ainda sem apoio embaixo), nem considera a paridade de linhas.
- Não há tabela de transposição: posições alcançadas por ordens diferentes de jogadas são reavaliadas.
- O ID não reaproveita a melhor jogada da iteração anterior para ordenar a seguinte; a ordenação é fixa (centro primeiro).
- A implementação usa cópias de listas Python e varre todo o tabuleiro em cada verificação de vitória; uma representação em *bitboard* permitiria buscas bem mais profundas no mesmo tempo.
