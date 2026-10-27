import tkinter as tk
from tkinter import messagebox
import chess
import random

PIECE_VALUES = {
    chess.PAWN: 10,
    chess.KNIGHT: 30,
    chess.BISHOP: 30,
    chess.ROOK: 50,
    chess.QUEEN: 90,
    chess.KING: 900
}

PIECE_UNICODE = {
    'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙',
    'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟'
}

def evaluate_board(board):
    if board.is_checkmate():
        return -9999 if board.turn else 9999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            val = PIECE_VALUES[piece.piece_type]
            score += val if piece.color == chess.WHITE else -val
    return score

def minimax(board, depth, alpha, beta, is_maximizing):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    if is_maximizing:
        max_eval = -float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def get_ai_move(board, depth):
    best_move = None
    is_maximizing = (board.turn == chess.WHITE)
    best_val = -float('inf') if is_maximizing else float('inf')

    moves = list(board.legal_moves)
    random.shuffle(moves)

    for move in moves:
        board.push(move)
        eval_score = minimax(board, depth - 1, -float('inf'), float('inf'), not is_maximizing)
        board.pop()

        if is_maximizing and eval_score > best_val:
            best_val = eval_score
            best_move = move
        elif not is_maximizing and eval_score < best_val:
            best_val = eval_score
            best_move = move

    return best_move if best_move else (moves[0] if moves else None)

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess AI Game")
        self.root.resizable(False, False)

        self.board = chess.Board()
        self.player_color = chess.WHITE
        self.flipped = False
        self.selected_square = None
        self.valid_moves = []
        self.square_size = 64
        self.board_dim = self.square_size * 8

        self.ai_job = None
        self.is_ai_thinking = False

        # Panel Menu Atas
        control_frame = tk.Frame(root, padx=10, pady=8, bg="#262421")
        control_frame.pack(fill=tk.X)

        # Baris 1: Tingkat Kesulitan & Reset Game
        row1 = tk.Frame(control_frame, bg="#262421")
        row1.pack(fill=tk.X, pady=(0, 6))

        tk.Label(row1, text="Kesulitan:", fg="#bababa", bg="#262421", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        
        self.diff_var = tk.IntVar(value=2)
        for label, val in [("Mudah (1)", 1), ("Sedang (2)", 2), ("Sulit (3)", 3)]:
            tk.Radiobutton(
                row1, text=label, variable=self.diff_var, value=val,
                bg="#262421", fg="#ffffff", selectcolor="#36322d",
                activebackground="#262421", activeforeground="#ffffff", font=("Segoe UI", 9)
            ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            row1, text="Reset Game", command=self.reset_game,
            bg="#81b64c", fg="#ffffff", font=("Segoe UI", 9, "bold"),
            relief="flat", padx=8, cursor="hand2"
        ).pack(side=tk.RIGHT)

        # Baris 2: Pemilihan Peran & Rotasi Papan
        row2 = tk.Frame(control_frame, bg="#262421")
        row2.pack(fill=tk.X)

        self.side_info = tk.StringVar(value="Peran Anda: Putih")
        tk.Label(row2, textvariable=self.side_info, fg="#a3e635", bg="#262421", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 8))

        self.btn_swap_role = tk.Button(
            row2, text="Ganti Sisi Pemain", command=self.toggle_side,
            bg="#3b82f6", fg="#ffffff", font=("Segoe UI", 9, "bold"),
            relief="flat", padx=6, pady=2, cursor="hand2"
        )
        self.btn_swap_role.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_flip_view = tk.Button(
            row2, text="Balik Papan (Visual)", command=self.toggle_board_flip,
            bg="#4b5563", fg="#ffffff", font=("Segoe UI", 9),
            relief="flat", padx=6, pady=2, cursor="hand2"
        )
        self.btn_flip_view.pack(side=tk.LEFT)

        # Kanvas Papan Catur
        self.canvas = tk.Canvas(root, width=self.board_dim, height=self.board_dim, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_square_clicked)

        # Panel Status Bawah
        self.status_var = tk.StringVar(value="Giliran Anda (Putih)")
        status_label = tk.Label(
            root, textvariable=self.status_var, font=("Segoe UI", 11, "bold"),
            pady=8, bg="#1e1e1e", fg="#e0e0e0"
        )
        status_label.pack(fill=tk.X)

        self.draw_board()

    def cancel_pending_ai(self):
        if self.ai_job is not None:
            self.root.after_cancel(self.ai_job)
            self.ai_job = None

    def toggle_board_flip(self):
        self.flipped = not self.flipped
        self.draw_board()

    def toggle_side(self):
        if self.is_ai_thinking:
            return

        self.cancel_pending_ai()

        # Tukar peran pemain
        if self.player_color == chess.WHITE:
            self.player_color = chess.BLACK
            self.flipped = True
            self.side_info.set("Peran Anda: Hitam")
        else:
            self.player_color = chess.WHITE
            self.flipped = False
            self.side_info.set("Peran Anda: Putih")

        self.selected_square = None
        self.valid_moves = []
        self.draw_board()

        # Cek apakah setelah berganti peran, giliran sekarang menjadi milik AI
        if self.board.turn != self.player_color and not self.board.is_game_over():
            color_turn = "Putih" if self.board.turn == chess.WHITE else "Hitam"
            self.status_var.set(f"Giliran {color_turn} (AI sedang berpikir...)")
            self.ai_job = self.root.after(400, self.ai_turn)
        else:
            color_turn = "Putih" if self.player_color == chess.WHITE else "Hitam"
            self.status_var.set(f"Giliran Anda ({color_turn})")

    def reset_game(self):
        if self.is_ai_thinking:
            return

        self.cancel_pending_ai()
        self.board.reset()
        self.selected_square = None
        self.valid_moves = []
        self.draw_board()

        if self.board.turn != self.player_color:
            self.status_var.set("Giliran Putih (AI sedang berpikir...)")
            self.ai_job = self.root.after(400, self.ai_turn)
        else:
            color_turn = "Putih" if self.player_color == chess.WHITE else "Hitam"
            self.status_var.set(f"Giliran Anda ({color_turn})")

    def draw_board(self):
        self.canvas.delete("all")
        colors = ["#eeeed2", "#769656"]
        highlight_color = "#baca44"
        valid_hint_color = "#a2b85e"

        for r in range(8):
            for c in range(8):
                sq = chess.square(7 - c, r) if self.flipped else chess.square(c, 7 - r)

                x1 = c * self.square_size
                y1 = r * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                tile_color = colors[0] if (chess.square_file(sq) + chess.square_rank(sq)) % 2 != 0 else colors[1]
                if sq == self.selected_square:
                    tile_color = highlight_color
                elif sq in self.valid_moves:
                    tile_color = valid_hint_color

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=tile_color, outline="")

                piece = self.board.piece_at(sq)
                if piece:
                    char = PIECE_UNICODE[piece.symbol()]
                    piece_color = "#ffffff" if piece.color == chess.WHITE else "#1a1a1a"
                    
                    if piece.color == chess.WHITE:
                        self.canvas.create_text(
                            x1 + self.square_size // 2 + 1, y1 + self.square_size // 2 + 1,
                            text=char, font=("Segoe UI Symbol", 36), fill="#555555"
                        )
                    self.canvas.create_text(
                        x1 + self.square_size // 2, y1 + self.square_size // 2,
                        text=char, font=("Segoe UI Symbol", 36), fill=piece_color
                    )

    def on_square_clicked(self, event):
        if self.is_ai_thinking or self.board.turn != self.player_color or self.board.is_game_over():
            return

        col = event.x // self.square_size
        row = event.y // self.square_size
        if not (0 <= col < 8 and 0 <= row < 8):
            return

        clicked_sq = chess.square(7 - col, row) if self.flipped else chess.square(col, 7 - row)

        if self.selected_square is None:
            piece = self.board.piece_at(clicked_sq)
            if piece and piece.color == self.player_color:
                self.selected_square = clicked_sq
                self.valid_moves = [m.to_square for m in self.board.legal_moves if m.from_square == clicked_sq]
                self.draw_board()
        else:
            move = chess.Move(self.selected_square, clicked_sq)
            if chess.Move(self.selected_square, clicked_sq, promotion=chess.QUEEN) in self.board.legal_moves:
                move = chess.Move(self.selected_square, clicked_sq, promotion=chess.QUEEN)

            if move in self.board.legal_moves:
                self.board.push(move)
                self.selected_square = None
                self.valid_moves = []
                self.draw_board()
                self.check_game_state()

                if not self.board.is_game_over():
                    color_turn = "Putih" if self.board.turn == chess.WHITE else "Hitam"
                    self.status_var.set(f"Giliran {color_turn} (AI sedang berpikir...)")
                    self.ai_job = self.root.after(300, self.ai_turn)
            else:
                piece = self.board.piece_at(clicked_sq)
                if piece and piece.color == self.player_color:
                    self.selected_square = clicked_sq
                    self.valid_moves = [m.to_square for m in self.board.legal_moves if m.from_square == clicked_sq]
                else:
                    self.selected_square = None
                    self.valid_moves = []
                self.draw_board()

    def ai_turn(self):
        if self.board.is_game_over() or self.board.turn == self.player_color:
            return

        self.is_ai_thinking = True
        self.btn_swap_role.config(state=tk.DISABLED)

        depth = self.diff_var.get()
        ai_move = get_ai_move(self.board, depth)
        
        if ai_move and ai_move in self.board.legal_moves:
            self.board.push(ai_move)

        self.draw_board()
        self.is_ai_thinking = False
        self.btn_swap_role.config(state=tk.NORMAL)

        color_turn = "Putih" if self.player_color == chess.WHITE else "Hitam"
        self.status_var.set(f"Giliran Anda ({color_turn})")
        self.check_game_state()

    def check_game_state(self):
        if self.board.is_game_over():
            if self.board.is_checkmate():
                winner = "Anda Menang (Skakmat)!" if self.board.turn != self.player_color else "AI Menang (Skakmat)!"
                self.status_var.set(winner)
                messagebox.showinfo("Game Selesai", winner)
            else:
                self.status_var.set("Permainan Seri (Remis)!")
                messagebox.showinfo("Game Selesai", "Permainan berakhir Seri (Remis)!")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChessGUI(root)
    root.mainloop()