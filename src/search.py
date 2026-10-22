from typing import List, Tuple, Optional, Dict
import time
import math
import random

ROWS, COLS = 6, 7
EMPTY, P1, P2 = 0, 1, 2
CENTER_ZONE_SIZE = 3
TWO_PIECE_SEQUENCE = 2
THREE_PIECE_SEQUENCE = 3
SEQUENCE_POINTS = {TWO_PIECE_SEQUENCE: 3, THREE_PIECE_SEQUENCE: 20}
CENTER_ORDER = sorted(range(COLS), key=lambda c: abs(c - COLS // 2))
VICTORY_POINTS = 1_000_000

class SearchTimeout(Exception): pass

# -----------------------------------------------------------------------------
# Utilidades de tabuleiro (PRONTAS)
# -----------------------------------------------------------------------------
def copy_board(board: List[List[int]]) -> List[List[int]]:
    return [row[:] for row in board]

def valid_moves(board: List[List[int]]) -> List[int]:
    """Retorna as colunas ainda jogáveis (topo vazio)."""
    return [c for c in range(COLS) if board[0][c] == EMPTY]

def ordered_valid_moves(board: List[List[int]]) -> List[int]:
    """Retorna as colunas ainda jogáveis (topo vazio). Ordena para retornar primeiro as colunas do meio do board para otimizar o minimax com poda"""
    return [c for c in CENTER_ORDER if board[0][c] == EMPTY]

def make_move(board: List[List[int]], col: int, player: int) -> Optional[List[List[int]]]:
    """Retorna um novo tabuleiro aplicando a gravidade na coluna col; None se inválido."""
    if col < 0 or col >= COLS or board[0][col] != EMPTY:
        return None
    nb = copy_board(board)
    for r in reversed(range(ROWS)):
        if nb[r][col] == EMPTY:
            nb[r][col] = player
            return nb
    return None
def winner(board: List[List[int]]) -> int:
    """0 se ninguém venceu; 1 ou 2 se há 4 em linha."""
    # Horizontais
    for r in range(ROWS):
        for c in range(COLS - 3):
            x = board[r][c]
            if x != EMPTY and x == board[r][c+1] == board[r][c+2] == board[r][c+3]:
                return x
    # Verticais
    for c in range(COLS):
        for r in range(ROWS - 3):
            x = board[r][c]
            if x != EMPTY and x == board[r+1][c] == board[r+2][c] == board[r+3][c]:
                return x
    # Diag ↘
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            x = board[r][c]
            if x != EMPTY and x == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3]:
                return x
    # Diag ↗
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            x = board[r][c]
            if x != EMPTY and x == board[r-1][c+1] == board[r-2][c+2] == board[r-3][c+3]:
                return x
    return 0

def is_full(board: List[List[int]]) -> bool:
    return all(board[0][c] != EMPTY for c in range(COLS))

def terminal(board: List[List[int]]) -> Tuple[bool, int]:
    """(é_terminal, vencedor) com vencedor=0 para empate/indefinido."""
    w = winner(board)
    if w != 0:
        return True, w
    if is_full(board):
        return True, 0
    return False, 0

def other(player: int) -> int:
    return P1 if player == P2 else P2

# -----------------------------------------------------------------------------
# ÚNICO PONTO A SER IMPLEMENTADO PELOS ALUNOS
# -----------------------------------------------------------------------------
def choose_move(board: List[List[int]], turn: int, config: Dict) -> Tuple[int, Dict]:
    """
    Decide a coluna (0..6) para jogar agora.

    Parâmetros:
      - board: matriz 6x7 com valores {0,1,2}
      - turn: 1 ou 2
      - config: {"max_time_ms": int, "max_depth": int}

    Retorna:
      - col: int (0..6)
    """
    max_time_ms = int(config.get("max_time_ms"))
    max_depth = int(config.get("max_depth"))
    turn = int(turn)

    print(f"AI choose_move called with max_time_ms={max_time_ms}, max_depth={max_depth}, player={turn}")
    
    start = time.time()

    # Função auxiliar para checar tempo decorrido   
    def time_exceeded():
        safety_net_ms = 200
        return max_time_ms > 0 and (time.time() - start) * 1000.0 >= max_time_ms - safety_net_ms
    
    legal = ordered_valid_moves(board)

    move = 0
    if not legal:
        # Sem jogadas: devolve 0 por convenção (servidor lida com isso)
        return move
    
    # VERSÃO INICIAL: escolhe aleatoriamente entre as jogadas legais
    # move = random.choice(legal)
    best_move = legal[0]
    current_depth = 1
    # Versao minimax:
    while current_depth <= max_depth:
      current_best_move = None
      best_score = -math.inf if is_max_player(turn) else math.inf
      alpha = -math.inf
      beta = math.inf
      try:
        for move in legal:
              copied_board = copy_board(board)
              moved_board = make_move(copied_board, move, turn)
              score = alpha_beta_minimax(moved_board, other(turn), max_depth=current_depth, alpha=alpha, beta=beta, timer=time_exceeded, depth=1)
              if is_max_player(turn):
                if score > best_score:
                  best_score = score
                  current_best_move = move
                alpha = max(best_score, alpha)
              else:
                if score < best_score:  
                  best_score = score
                  current_best_move = move
                beta = min(best_score, beta)
      except SearchTimeout:
          print(f"Timeout recebido com depth = {current_depth}")
          break
      best_move = current_best_move 
      if abs(best_score) > VICTORY_POINTS - 100: break
      current_depth += 1

    if best_move is None:
        print(f'Minimax nao achou nenhuma boa jogada com max_depth={max_depth}')
        best_move = legal[0]
            
    return best_move

def choose_move_infinity(board: List[List[int]], turn: int, config: Dict) -> Tuple[int, Dict]:
    """
    Decide a coluna (0..6) para jogar agora.

    Parâmetros:
      - board: matriz 6x7 com valores {0,1,2}
      - turn: 1 ou 2
      - config: {"max_time_ms": int, "max_depth": int}

    Retorna:
      - col: int (0..6)
    """
    max_time_ms = int(config.get("max_time_ms"))
    max_depth = int(config.get("max_depth"))
    turn = int(turn)

    print(f"AI choose_move called with max_time_ms={max_time_ms}, max_depth={max_depth}, player={turn}")
    
    start = time.time()

    # Função auxiliar para checar tempo decorrido   
    def time_exceeded():
        return max_time_ms > 0 and (time.time() - start) * 1000.0 >= max_time_ms
    
    legal = valid_moves(board)

    move = 0
    if not legal:
        # Sem jogadas: devolve 0 por convenção (servidor lida com isso)
        return move
    
    # VERSÃO INICIAL: escolhe aleatoriamente entre as jogadas legais
    i = 0
    while True:
        i += 1

    return move

def is_max_player(player: int) -> bool:
    return True if player == P1 else False

def minimax(board, player, max_depth, depth = 0) -> int:
    """
    Recebe o tabuleiro, de qual jogador é a vez e retorna o melhor score para aquele jogador com base no tabuleiro atual. 

    Parâmetros:
      - board: matriz 6x7 com valores {0,1,2}
      - player: 1 ou 2
      - depth: int

    Retorna:
      - int (score)
    """
    
    game_ended, winner = terminal(board)
    is_tie = game_ended and winner == 0

    if(is_tie): return 0

    if(game_ended):
        return VICTORY_POINTS - depth if winner == P1 else -VICTORY_POINTS + depth

    if(depth >= max_depth):
      return heuristics(board)

    if(is_max_player(player)):
        best_score = -math.inf
        for move in valid_moves(board):
            copied_board = copy_board(board)
            new_board = make_move(copied_board, move, P1)
            score = minimax(new_board, other(P1), max_depth, depth + 1)
            best_score = max(best_score, score)
        return best_score

    best_score = +math.inf
    for move in valid_moves(board):
      copied_board = copy_board(board)
      new_board = make_move(copied_board, move, P2)
      score = minimax(new_board, other(P2), max_depth, depth + 1)
      best_score = min(best_score, score)
    return best_score


def alpha_beta_minimax(board, player, max_depth, alpha, beta, timer, depth = 0) -> int:
    """
    Recebe o tabuleiro, de qual jogador é a vez e retorna o melhor score para aquele jogador com base no tabuleiro atual.
    Utiliza a otimizacao alpha-beta pruning para melhorar eficiencia. 

    Parâmetros:
      - board: matriz 6x7 com valores {0,1,2}
      - player: 1 ou 2
      - depth: int

    Retorna:
      - int (score)
    """
    if(timer()): raise SearchTimeout()
    
    game_ended, winner = terminal(board)
    is_tie = game_ended and winner == 0

    if(is_tie): return 0

    if(game_ended):
        return VICTORY_POINTS - depth if winner == P1 else -VICTORY_POINTS + depth

    if(depth >= max_depth):
      return heuristics(board)

    if(is_max_player(player)):
        best_score = -math.inf
        for move in ordered_valid_moves(board):
            copied_board = copy_board(board)
            new_board = make_move(copied_board, move, P1)
            score = alpha_beta_minimax(new_board, other(P1), max_depth, alpha=alpha, beta=beta, timer=timer, depth=depth + 1)
            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
            if beta <= alpha: break
        return best_score

    best_score = +math.inf
    for move in ordered_valid_moves(board):
      copied_board = copy_board(board)
      new_board = make_move(copied_board, move, P2)
      score = alpha_beta_minimax(new_board, other(P2), max_depth, alpha=alpha, beta=beta, timer=timer, depth=depth + 1)
      best_score = min(best_score, score)
      beta = min(beta, best_score)
      if beta <= alpha: break
    return best_score


def heuristics(board)->int:
    return estimated_points(board, P1) - estimated_points(board, P2)


def estimated_points(board: List[List[int]], player) -> int:
    points = 0 
    points += middle_ground_control_points(board, player)
    points += sequence_points(board, player)
    return points

def sequence_points(board, player) -> int:
    points = 0

    def is_sequence_alive(mine, empty):
        return mine + empty == 4

    def points_by(sequence_size)-> int:
        return SEQUENCE_POINTS.get(sequence_size, 0)

    def points_in(window) -> int:
        points = 0
        mine = window.count(player)
        empty = window.count(EMPTY)
        if(is_sequence_alive(mine, empty)):
            points += points_by(mine)
        return points
    
    # Horizontais
    for r in range(ROWS):
        for c in range(COLS - 3):
          board_window = [board[r][c + i] for i in range(4)]
          points += points_in(board_window)
                  

    # Verticais
    for c in range(COLS):
        for r in range(ROWS - 3):
          board_window = [board[r + i][c] for i in range(4)]
          points += points_in(board_window)

    # Diag ↘
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
          board_window = [board[r + i][c + i] for i in range(4)]
          points += points_in(board_window)

    # Diag ↗
    for r in range(3, ROWS):
        for c in range(COLS - 3):
          board_window = [board[r + i*-1][c + i] for i in range(4)]
          points += points_in(board_window)

    return points

def middle_ground_control_points(board, player) -> int:
    points = 0
    row_start = ROWS - CENTER_ZONE_SIZE
    col_start = (COLS - CENTER_ZONE_SIZE) // 2
    col_end = col_start + CENTER_ZONE_SIZE

    points = sum(1 for row in board[row_start:] for cell in row[col_start:col_end] if cell == player)
    return points