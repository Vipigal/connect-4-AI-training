"""
Script auxiliar de experimentos do TP1 (código de coleta de métricas).

Roda partidas automáticas entre agentes, sem servidor, e imprime as tabelas do relatório:
  1. Minimax vs. Aleatório        (profundidades 2, 3, 4, 5)
  2. Alfa-Beta vs. Minimax        (profundidades 2, 3, 4, 5)
  3. Iterative Deepening vs. Alfa-Beta (limites de 1 s e 2 s)

Não altera o search.py: a contagem de nós é feita envolvendo as funções de busca,
e as chamadas recursivas passam pelo wrapper porque usam o nome global do módulo.

Uso (na pasta src):
  python experiments.py                 # todos os experimentos, 10 partidas por confronto
  python experiments.py --exp 1 2 -n 20
  python experiments.py --exp 3 --ab-depth 5 --csv resultados.csv
"""
import argparse
import builtins
import csv
import math
import random
import time
from contextlib import contextmanager

import search as s

# -----------------------------------------------------------------------------
# Instrumentação
# -----------------------------------------------------------------------------
_orig_minimax = s.minimax
_orig_alpha_beta = s.alpha_beta_minimax


class Stats:
    nodes = 0
    last_root_depth = 0   # limite de profundidade da iteração mais recente do ID
    timed_out = False


def _counted_minimax(*args, **kwargs):
    Stats.nodes += 1
    return _orig_minimax(*args, **kwargs)


def _counted_alpha_beta(*args, **kwargs):
    Stats.nodes += 1
    is_root_child = kwargs.get("depth", 0) == 1
    if is_root_child:
        Stats.last_root_depth = kwargs.get("max_depth", args[2] if len(args) > 2 else 0)
    try:
        return _orig_alpha_beta(*args, **kwargs)
    except s.SearchTimeout:
        if is_root_child:
            Stats.timed_out = True
        raise


s.minimax = _counted_minimax
s.alpha_beta_minimax = _counted_alpha_beta


@contextmanager
def silent():
    """Silencia os prints do search.py durante a busca."""
    original = builtins.print
    builtins.print = lambda *a, **k: None
    try:
        yield
    finally:
        builtins.print = original


def _better(turn, score, best):
    return score > best if s.is_max_player(turn) else score < best


# -----------------------------------------------------------------------------
# Agentes: cada um recebe (board, turn) e devolve (col, info)
# -----------------------------------------------------------------------------
def random_agent():
    def play(board, turn):
        return random.choice(s.valid_moves(board)), {}
    play.label = "Aleatório"
    return play


def minimax_agent(depth):
    """Minimax sem poda, profundidade fixa (mesma convenção do choose_move: raiz = nível 1)."""
    def play(board, turn):
        best_move, best = None, -math.inf if s.is_max_player(turn) else math.inf
        for move in s.valid_moves(board):
            score = s.minimax(s.make_move(board, move, turn), s.other(turn), depth, 1)
            if _better(turn, score, best):
                best, best_move = score, move
        return best_move, {"depth": depth}
    play.label = f"Minimax d={depth}"
    return play


def alpha_beta_agent(depth):
    """Alfa-Beta com ordenação, profundidade fixa, sem Iterative Deepening."""
    def play(board, turn):
        best_move, best = None, -math.inf if s.is_max_player(turn) else math.inf
        alpha, beta = -math.inf, math.inf
        for move in s.ordered_valid_moves(board):
            score = s.alpha_beta_minimax(s.make_move(board, move, turn), s.other(turn),
                                         max_depth=depth, alpha=alpha, beta=beta,
                                         timer=lambda: False, depth=1)
            if _better(turn, score, best):
                best, best_move = score, move
            if s.is_max_player(turn):
                alpha = max(alpha, best)
            else:
                beta = min(beta, best)
        return best_move, {"depth": depth}
    play.label = f"Alfa-Beta d={depth}"
    return play


def id_agent(time_ms, max_depth=42):
    """O agente final (choose_move): Iterative Deepening com limite de tempo."""
    def play(board, turn):
        Stats.last_root_depth, Stats.timed_out = 0, False
        col = s.choose_move(board, turn, {"max_time_ms": time_ms, "max_depth": max_depth})
        completed = Stats.last_root_depth - 1 if Stats.timed_out else Stats.last_root_depth
        return col, {"depth": completed}
    play.label = f"ID {time_ms / 1000:g} s"
    return play


# -----------------------------------------------------------------------------
# Partidas
# -----------------------------------------------------------------------------
def play_game(agent_p1, agent_p2, opening_plies=0, rng=None):
    """Joga uma partida. Devolve (vencedor, métricas por jogador)."""
    board = [[s.EMPTY] * s.COLS for _ in range(s.ROWS)]
    agents = {s.P1: agent_p1, s.P2: agent_p2}
    metrics = {p: {"moves": 0, "time": 0.0, "nodes": 0, "depths": []} for p in (s.P1, s.P2)}
    turn = s.P1
    plies = 0

    while True:
        ended, winner = s.terminal(board)
        if ended:
            return winner, metrics

        if plies < opening_plies:
            # Abertura aleatória: gera partidas diferentes entre agentes determinísticos
            col = (rng or random).choice(s.valid_moves(board))
        else:
            Stats.nodes = 0
            start = time.perf_counter()
            with silent():
                col, info = agents[turn](board, turn)
            m = metrics[turn]
            m["time"] += time.perf_counter() - start
            m["nodes"] += Stats.nodes
            m["moves"] += 1
            if "depth" in info:
                m["depths"].append(info["depth"])

        board = s.make_move(board, col, turn)
        turn = s.other(turn)
        plies += 1


def match(make_a, make_b, games, opening_plies, seed):
    """
    Confronto A vs. B com `games` partidas, alternando quem começa.
    Resultados do ponto de vista de A.
    """
    rng = random.Random(seed)
    random.seed(seed)
    agent_a, agent_b = make_a(), make_b()
    totals = {"a": {"moves": 0, "time": 0.0, "nodes": 0, "depths": []},
              "b": {"moves": 0, "time": 0.0, "nodes": 0, "depths": []}}
    wins = draws = losses = 0

    for g in range(games):
        a_is_p1 = g % 2 == 0
        p1, p2 = (agent_a, agent_b) if a_is_p1 else (agent_b, agent_a)
        winner, metrics = play_game(p1, p2, opening_plies, rng)

        side_a = s.P1 if a_is_p1 else s.P2
        if winner == 0:
            draws += 1
        elif winner == side_a:
            wins += 1
        else:
            losses += 1

        for key, side in (("a", side_a), ("b", s.other(side_a))):
            for field in ("moves", "time", "nodes"):
                totals[key][field] += metrics[side][field]
            totals[key]["depths"] += metrics[side]["depths"]

        print(f"    partida {g + 1}/{games}: "
              f"{'vitória de ' + agent_a.label if winner == side_a else 'empate' if winner == 0 else 'vitória de ' + agent_b.label}",
              flush=True)

    def summary(t):
        moves = max(t["moves"], 1)
        return {
            "tempo_medio_ms": 1000 * t["time"] / moves,
            "nos_medios": t["nodes"] / moves,
            "prof_media": sum(t["depths"]) / len(t["depths"]) if t["depths"] else None,
        }

    return {
        "agente_a": agent_a.label, "agente_b": agent_b.label, "partidas": games,
        "vitorias_a": wins, "empates": draws, "derrotas_a": losses,
        "taxa_vitoria_a": wins / games,
        **{f"a_{k}": v for k, v in summary(totals["a"]).items()},
        **{f"b_{k}": v for k, v in summary(totals["b"]).items()},
    }


# -----------------------------------------------------------------------------
# Experimentos
# -----------------------------------------------------------------------------
def experiments(args):
    plan = []
    if 1 in args.exp:
        for d in (2, 3, 4, 5):
            plan.append((1, lambda d=d: minimax_agent(d), random_agent, 0))
    if 2 in args.exp:
        for d in (2, 3, 4, 5):
            plan.append((2, lambda d=d: alpha_beta_agent(d), lambda d=d: minimax_agent(d), args.opening))
    if 3 in args.exp:
        for ms in (1000, 2000):
            plan.append((3, lambda ms=ms: id_agent(ms), lambda: alpha_beta_agent(args.ab_depth), args.opening))
    return plan


def fmt(v, digits=1):
    return "—" if v is None else f"{v:.{digits}f}"


def print_table(exp, rows):
    titles = {1: "Experimento 1: Minimax vs. Aleatório",
              2: "Experimento 2: Alfa-Beta vs. Minimax",
              3: "Experimento 3: Iterative Deepening vs. Alfa-Beta"}
    print(f"\n### {titles[exp]}\n")
    print("| Agente A | Agente B | V / E / D (A) | Taxa vit. A | Tempo/jogada A (ms) | Tempo/jogada B (ms) "
          "| Nós/jogada A | Nós/jogada B | Prof. média A |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['agente_a']} | {r['agente_b']} | {r['vitorias_a']} / {r['empates']} / {r['derrotas_a']} "
              f"| {100 * r['taxa_vitoria_a']:.0f}% | {fmt(r['a_tempo_medio_ms'])} | {fmt(r['b_tempo_medio_ms'])} "
              f"| {fmt(r['a_nos_medios'], 0)} | {fmt(r['b_nos_medios'], 0)} | {fmt(r['a_prof_media'])} |")


def main():
    parser = argparse.ArgumentParser(description="Experimentos do TP1 (Ligue-4)")
    parser.add_argument("--exp", type=int, nargs="+", default=[1, 2, 3], choices=[1, 2, 3])
    parser.add_argument("-n", "--games", type=int, default=10, help="partidas por confronto (par, para alternar quem começa)")
    parser.add_argument("--opening", type=int, default=2,
                        help="jogadas aleatórias de abertura nos exp. 2 e 3 (agentes determinísticos repetiriam a mesma partida)")
    parser.add_argument("--ab-depth", type=int, default=5, help="profundidade fixa do Alfa-Beta no exp. 3")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--csv", help="salva os resultados agregados em CSV")
    args = parser.parse_args()

    results = {}
    for i, (exp, make_a, make_b, opening) in enumerate(experiments(args)):
        label = f"{make_a().label} vs. {make_b().label}"
        print(f"[exp {exp}] {label}", flush=True)
        t0 = time.perf_counter()
        row = match(make_a, make_b, args.games, opening, args.seed + i)
        row["experimento"] = exp
        print(f"    concluído em {time.perf_counter() - t0:.0f} s", flush=True)
        results.setdefault(exp, []).append(row)

    for exp, rows in results.items():
        print_table(exp, rows)

    if args.csv:
        rows = [r for rs in results.values() for r in rs]
        with open(args.csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["experimento"] + [k for k in rows[0] if k != "experimento"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nCSV salvo em {args.csv}")


if __name__ == "__main__":
    main()
