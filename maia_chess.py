import os
import sys
import pygame
import chess
import chess.engine
import warnings

# Initialize Pygame
pygame.init()

warnings.filterwarnings("ignore", category=UserWarning, module="pygame.image")

# Set up the display
WIDTH, HEIGHT = 1200, 900  # Increased width for move suggestions
SQ_SIZE = WIDTH // 15  # Adjusted for new width
BOARD_SIZE = 8 * SQ_SIZE
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess GUI")


# Determine the resource path
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Load images
IMAGES = {}
PIECES = ["wP", "bP", "wN", "bN", "wB", "bB", "wR", "bR", "wQ", "bQ", "wK", "bK"]
for piece in PIECES:
    image = pygame.image.load(resource_path(f"images/{piece}.png"))
    IMAGES[piece] = pygame.transform.smoothscale(image, (SQ_SIZE, SQ_SIZE))

# Piece to image mapping
piece_to_image = {
    "P": "wP",
    "p": "bP",
    "N": "wN",
    "n": "bN",
    "B": "wB",
    "b": "bB",
    "R": "wR",
    "r": "bR",
    "Q": "wQ",
    "q": "bQ",
    "K": "wK",
    "k": "bK",
}

# Colors for highlights and arrows
ARROW_COLOR = pygame.Color(255, 255, 255, 192)
ARROW_COLORS = [
    pygame.Color(255, 192, 203, 128),  # Light Pink
    pygame.Color(173, 216, 230, 128),  # Light Blue
    pygame.Color(144, 238, 144, 128),  # Light Green
]
LEGAL_MOVE_COLOR = pygame.Color(255, 255, 102, 128)  # Light Yellow
SELECTED_SQUARE_COLOR = pygame.Color(255, 0, 0, 128)  # Semi-transparent Red


# New Tile class
class Square:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.abs_x = x * width
        self.abs_y = y * height
        self.abs_pos = (self.abs_x, self.abs_y)
        self.pos = (x, y)
        self.color = "light" if (x + y) % 2 == 0 else "dark"
        self.draw_color = (220, 208, 194) if self.color == "light" else (53, 53, 53)
        self.highlight_color = (100, 249, 83) if self.color == "light" else (0, 228, 10)
        self.occupying_piece = None
        self.coord = self.get_coord()
        self.highlight = False
        self.rect = pygame.Rect(self.abs_x, self.abs_y, self.width, self.height)

    def get_coord(self):
        columns = "abcdefgh"
        return columns[self.x] + str(self.y + 1)

    def draw(self, display):
        if self.highlight:
            pygame.draw.rect(display, self.highlight_color, self.rect)
        else:
            pygame.draw.rect(display, self.draw_color, self.rect)
        if self.occupying_piece is not None:
            centering_rect = self.occupying_piece.img.get_rect()
            centering_rect.center = self.rect.center
            display.blit(self.occupying_piece.img, centering_rect.topleft)


# New Board class
class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tile_width = width // 8
        self.tile_height = height // 8
        self.selected_piece = None
        self.turn = "white"
        self.config = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
        ]
        self.squares = self.generate_squares()
        self.setup_board()

    def generate_squares(self):
        output = []
        for y in range(8):
            for x in range(8):
                output.append(Square(x, y, self.tile_width, self.tile_height))
        return output

    def get_square_from_pos(self, pos):
        for square in self.squares:
            if (square.x, square.y) == (pos[0], pos[1]):
                return square

    def get_piece_from_pos(self, pos):
        return self.get_square_from_pos(pos).occupying_piece

    def setup_board(self):
        for y, row in enumerate(self.config):
            for x, piece in enumerate(row):
                if piece != "":
                    square = self.get_square_from_pos((x, y))
                    piece_image = IMAGES[piece]
                    square.occupying_piece = piece_image

    def draw(self, display):
        for square in self.squares:
            square.draw(display)


# Draw the board
def draw_board():
    global game_board
    game_board.draw(WINDOW)


# Draw pieces
def draw_pieces(board):
    for square in game_board.squares:
        piece = board.piece_at(chess.square(square.x, 7 - square.y))
        if piece:
            piece_image = IMAGES[piece_to_image[piece.symbol()]]
            square.occupying_piece = piece_image
            WINDOW.blit(piece_image, square.rect)


def highlight_selected_square(window, selected_square):
    if selected_square is not None:
        x, y = (
            chess.square_file(selected_square),
            7 - chess.square_rank(selected_square),  # Invert y-coordinate here
        )
        pygame.draw.rect(
            window,
            SELECTED_SQUARE_COLOR,
            pygame.Rect(x * SQ_SIZE, y * SQ_SIZE, SQ_SIZE, SQ_SIZE),
        )


def highlight_legal_moves(window, board, selected_square):
    if selected_square is not None:
        for move in board.legal_moves:
            if move.from_square == selected_square:
                x, y = (
                    chess.square_file(move.to_square),
                    7 - chess.square_rank(move.to_square),
                )
                pygame.draw.circle(
                    window,
                    LEGAL_MOVE_COLOR,
                    (x * SQ_SIZE + SQ_SIZE // 2, y * SQ_SIZE + SQ_SIZE // 2),
                    SQ_SIZE // 6,
                )


# Draw an arrow from the starting square to the ending square
def draw_move_arrow(window, from_square, to_square, color=ARROW_COLOR):
    if from_square is not None and to_square is not None:
        start_pos = (
            chess.square_file(from_square) * SQ_SIZE + SQ_SIZE // 2,
            (7 - chess.square_rank(from_square)) * SQ_SIZE + SQ_SIZE // 2,
        )
        end_pos = (
            chess.square_file(to_square) * SQ_SIZE + SQ_SIZE // 2,
            (7 - chess.square_rank(to_square)) * SQ_SIZE + SQ_SIZE // 2,
        )
        pygame.draw.line(window, color, start_pos, end_pos, 5)


# Draw arrows for best moves
def draw_arrows(window, best_moves):
    for idx, (move, _) in enumerate(best_moves):
        if idx >= len(ARROW_COLORS):
            break
        draw_move_arrow(window, move.from_square, move.to_square, ARROW_COLORS[idx])


# Handle user input
def get_square_under_mouse():
    mouse_pos = pygame.mouse.get_pos()
    x, y = [int(v // SQ_SIZE) for v in mouse_pos]
    flipped_y = 7 - y
    if 0 <= x < 8 and 0 <= flipped_y < 8:
        square = chess.square(x, flipped_y)
        return square
    return None


def set_engine_parameters(engine, elo_rating):
    if elo_rating < 1100 or elo_rating > 1900 or elo_rating % 100 != 0:
        raise ValueError(
            "Invalid Elo rating. Please choose a rating between 1100 and 1900 in increments of 100."
        )

    weights = f"maia-{elo_rating}.pb.gz"
    engine.quit()
    engine = chess.engine.SimpleEngine.popen_uci(
        [
            "lc0",
            f"--weights=/Volumes/nvme/PROJECTS/coding_projects/python_chess_gui/{weights}",
        ]
    )
    engine.configure({"Threads": 1})
    return engine


def display_best_moves_text(best_moves):
    font = pygame.font.Font(None, 24)
    text_y = 10  # Start below the board
    for idx, (move, score) in enumerate(best_moves):
        move_text = f"{idx+1}. {move.uci()} ({score:.2f})"
        text_surface = font.render(move_text, True, pygame.Color(0, 0, 0))
        WINDOW.blit(text_surface, (BOARD_SIZE + 10, text_y))
        text_y += 30


def get_best_moves(engine, board, num_moves=3):
    result = engine.analyse(board, chess.engine.Limit(time=1), multipv=num_moves)
    best_moves = []
    for info in result:
        move = info["pv"][0]
        score = info["score"].relative.score(mate_score=10000) / 100.0
        best_moves.append((move, score))
    return best_moves


def elo_menu(window, current_elo):
    menu_running = True
    font = pygame.font.Font(None, 36)
    button_width = 100
    button_height = 50
    button_spacing = 20
    buttons = []

    for i, elo in enumerate(range(1100, 2000, 100)):
        x = 100 + (i % 5) * (button_width + button_spacing)
        y = 100 + (i // 5) * (button_height + button_spacing)
        buttons.append((pygame.Rect(x, y, button_width, button_height), elo))

    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                menu_running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button, elo in buttons:
                    if button.collidepoint(event.pos):
                        return elo  # Return the selected ELO rating

        window.fill(pygame.Color(200, 200, 200))
        for button, elo in buttons:
            pygame.draw.rect(window, pygame.Color(0, 0, 255), button)
            text_surface = font.render(f"Elo: {elo}", True, pygame.Color(0, 0, 0))
            window.blit(
                text_surface,
                (
                    button.x + (button_width - text_surface.get_width()) // 2,
                    button.y + (button_height - text_surface.get_height()) // 2,
                ),
            )

        pygame.display.flip()

    return current_elo  # If menu is exited without selection, return current ELO


def main():
    global game_board
    board = chess.Board()
    clock = pygame.time.Clock()

    selected_square = None
    player_clicks = []
    last_move = None
    elo_rating = 1500
    show_menu = False

    # Initialize the game board
    game_board = Board(BOARD_SIZE, BOARD_SIZE)

    # Move history for undo functionality
    move_history = []

    # Initialize the Maia engine with the default Elo rating
    engine = chess.engine.SimpleEngine.popen_uci(
        [
            "lc0",
            "--weights=/Volumes/nvme/PROJECTS/coding_projects/python_chess_gui/maia-1500.pb.gz",
        ]
    )
    engine.configure({"Threads": 1})

    best_moves = get_best_moves(engine, board)

    def redraw_all():
        draw_board()
        highlight_selected_square(WINDOW, selected_square)
        highlight_legal_moves(WINDOW, board, selected_square)
        draw_pieces(board)
        if last_move:
            draw_move_arrow(WINDOW, last_move.from_square, last_move.to_square)
        draw_arrows(WINDOW, best_moves)
        pygame.draw.rect(
            WINDOW,
            pygame.Color(200, 200, 200),
            pygame.Rect(BOARD_SIZE, 0, WIDTH - BOARD_SIZE, HEIGHT),
        )  # Clear the area for best moves
        display_best_moves_text(best_moves)
        draw_undo_button()
        draw_restart_button()
        pygame.display.update()

    def draw_undo_button():
        undo_button = pygame.Rect(BOARD_SIZE + 10, HEIGHT - 60, 120, 40)
        pygame.draw.rect(WINDOW, pygame.Color(255, 0, 0), undo_button)
        font = pygame.font.Font(None, 36)
        text_surface = font.render("Undo Move", True, pygame.Color(255, 255, 255))
        WINDOW.blit(text_surface, (BOARD_SIZE + 20, HEIGHT - 50))
        return undo_button

    def draw_restart_button():
        restart_button = pygame.Rect(BOARD_SIZE + 150, HEIGHT - 60, 120, 40)
        pygame.draw.rect(WINDOW, pygame.Color(0, 0, 255), restart_button)
        font = pygame.font.Font(None, 36)
        text_surface = font.render("Restart", True, pygame.Color(255, 255, 255))
        WINDOW.blit(text_surface, (BOARD_SIZE + 160, HEIGHT - 50))
        return restart_button

    redraw_all()

    while not board.is_game_over():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                engine.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                show_menu = not show_menu
                if show_menu:
                    elo_rating = elo_menu(WINDOW, elo_rating)
                    engine = set_engine_parameters(engine, elo_rating)
                    best_moves = get_best_moves(engine, board)
                    show_menu = False
                    redraw_all()
            elif event.type == pygame.MOUSEBUTTONDOWN and not show_menu:
                if draw_undo_button().collidepoint(event.pos):
                    if move_history:
                        board.pop()
                        move_history.pop()
                        last_move = move_history[-1] if move_history else None
                        best_moves = get_best_moves(engine, board)
                        redraw_all()
                elif draw_restart_button().collidepoint(event.pos):
                    board.reset()
                    move_history.clear()
                    last_move = None
                    best_moves = get_best_moves(engine, board)
                    redraw_all()
                else:
                    square = get_square_under_mouse()
                    if square:
                        if selected_square is None:
                            selected_square = square
                            player_clicks.append(square)
                        else:
                            player_clicks.append(square)
                            move = chess.Move(player_clicks[0], player_clicks[1])
                            if move in board.legal_moves:
                                board.push(move)
                                move_history.append(move)
                                last_move = move
                                best_moves = get_best_moves(engine, board)
                                selected_square = None
                                player_clicks = []
                                redraw_all()
                            else:
                                player_clicks = [square]
                                selected_square = square

        if not show_menu:
            redraw_all()
        clock.tick(30)

    engine.quit()


if __name__ == "__main__":
    main()
