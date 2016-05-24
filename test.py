import chess
import chess.uci

board = chess.Board()
print(board)
path = "/home/denis/Downloads/stockfish-7-linux/src/stockfish"
engine = engine = chess.uci.popen_engine(path)

while not board.is_checkmate():
    engine.position(board)
    a = engine.go(movetime=2000)
    board.push_uci(a.bestmove.uci())
    print(board)
