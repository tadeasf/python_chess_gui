import os
import sys
import pygame
import chess
import chess.engine
import warnings
import math

# Initialize Pygame
pygame.init()

warnings.filterwarnings("ignore", category=UserWarning, module="pygame.image")

# Set up the display
WIDTH, HEIGHT = 800, 1000  # Adjusted the width and height as per requirements
SQ_SIZE = WIDTH // 8  # Square size for the chessboard
BOARD_SIZE = 8 * SQ_SIZE
INFO_HEIGHT = HEIGHT - BOARD_SIZE
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fořtí Chess Engine")


def resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and for PyInstaller/Nuitka"""
    try:
        # PyInstaller/Nuitka creates a temp folder and stores the path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


font = pygame.font.Font(resource_path("assets/fonts/IosevkaSlab-Regular.ttf"), 24)
font = pygame.font.Font(resource_path("assets/fonts/IosevkaSlab-Regular.ttf"), 36)

# Load images
IMAGES = {}
PIECES = ["wP", "bP", "wN", "bN", "wB", "bB", "wR", "bR", "wQ", "bQ", "wK", "bK"]
for piece in PIECES:
    image = pygame.image.load(resource_path(f"assets/images/{piece}.png"))
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
LEGAL_MOVE_COLOR = pygame.Color(149, 149, 149, 128)
SELECTED_SQUARE_COLOR = pygame.Color(255, 109, 97, 128)


# Draw the board
def draw_board():
    colors = [pygame.Color(150, 150, 150), pygame.Color(120, 120, 120)]
    for r in range(8):
        for c in range(8):
            color = colors[(r + c) % 2]
            pygame.draw.rect(
                WINDOW, color, pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            )


def draw_coordinates():
    font = pygame.font.Font("assets/fonts/IosevkaSlab-Regular.ttf", 18)
    for i in range(8):
        # Draw files (a-h) at the bottom of the board, aligned to the bottom-right of each square
        file_label = font.render(chr(97 + i), True, pygame.Color(0, 0, 0))
        WINDOW.blit(
            file_label,
            (
                (i + 1) * SQ_SIZE - file_label.get_width() - 2,
                BOARD_SIZE - file_label.get_height() - 2,
            ),
        )
        # Draw ranks (1-8) on the left side of the board, aligned to the top-left of each square
        rank_label = font.render(str(8 - i), True, pygame.Color(0, 0, 0))
        WINDOW.blit(rank_label, (5, i * SQ_SIZE + 5))


# Draw pieces
def draw_pieces(board):
    for r in range(8):
        for c in range(8):
            piece = board.piece_at(chess.square(c, 7 - r))
            if piece:
                piece_image = IMAGES[piece_to_image[piece.symbol()]]
                WINDOW.blit(
                    piece_image, pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
                )


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


def draw_move_arrow(window, from_square, to_square, color=ARROW_COLOR):
    if from_square is not None and to_square is not None:
        # Calculate start and end positions
        start_pos = (
            chess.square_file(from_square) * SQ_SIZE + SQ_SIZE // 2,
            (7 - chess.square_rank(from_square)) * SQ_SIZE + SQ_SIZE // 2,
        )
        end_pos = (
            chess.square_file(to_square) * SQ_SIZE + SQ_SIZE // 2,
            (7 - chess.square_rank(to_square)) * SQ_SIZE + SQ_SIZE // 2,
        )

        # Draw the main line of the arrow
        pygame.draw.line(window, color, start_pos, end_pos, 5)

        # Calculate the direction of the arrow
        direction = (end_pos[0] - start_pos[0], end_pos[1] - start_pos[1])
        length = math.hypot(*direction)
        if length == 0:
            return  # Prevent division by zero if start and end positions are the same

        unit_direction = (direction[0] / length, direction[1] / length)

        # Determine the size of the arrowhead
        arrow_size = 20  # Increased arrowhead size for more pronounced tip
        arrow_width = 15  # Increased arrowhead width for more pronounced tip

        # Calculate the first point of the arrowhead
        left = (
            end_pos[0]
            - unit_direction[0] * arrow_size
            + unit_direction[1] * arrow_width,
            end_pos[1]
            - unit_direction[1] * arrow_size
            - unit_direction[0] * arrow_width,
        )

        # Calculate the second point of the arrowhead
        right = (
            end_pos[0]
            - unit_direction[0] * arrow_size
            - unit_direction[1] * arrow_width,
            end_pos[1]
            - unit_direction[1] * arrow_size
            + unit_direction[0] * arrow_width,
        )

        # Draw the arrowhead
        pygame.draw.polygon(window, color, [end_pos, left, right])


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
        return chess.square(x, flipped_y)
    return None


def set_engine_parameters(engine, elo_rating):
    if elo_rating < 1100 or elo_rating > 1900 or elo_rating % 100 != 0:
        raise ValueError(
            "Invalid Elo rating. Please choose a rating between 1100 and 1900 in increments of 100."
        )
    weights = f"assets/models/maia-{elo_rating}.pb.gz"
    engine.quit()
    engine = chess.engine.SimpleEngine.popen_uci(["lc0", f"--weights={weights}"])
    engine.configure({"Threads": 1})
    return engine


def display_best_moves_text(best_moves):
    font = pygame.font.Font("assets/fonts/IosevkaSlab-Regular.ttf", 24)
    text_y = BOARD_SIZE + 20  # Start below the board
    text_x = WIDTH // 2  # Start in the center of the bottom area
    for idx, (move, score) in enumerate(best_moves):
        move_text = f"{idx+1}. {move.uci()} ({score:.2f})"
        text_surface = font.render(move_text, True, pygame.Color(0, 0, 0))
        text_rect = text_surface.get_rect(center=(text_x, text_y))
        WINDOW.blit(text_surface, text_rect)
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
    font = font = pygame.font.Font("assets/fonts/IosevkaSlab-Regular.ttf", 20)
    button_width = 150
    button_height = 75
    button_spacing = 25
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


def evaluate_position(engine, board):
    info = engine.analyse(board, chess.engine.Limit(time=0.1))
    score = info["score"].relative.score(mate_score=10000)
    if score is None:
        print("Evaluation score is None")
        return 0.5, 0.5, 0.0  # In case of an unknown score
    print(f"Evaluation score: {score}")
    win_prob = 1 / (1 + math.exp(-score / 400))
    loss_prob = 1 - win_prob
    draw_prob = 0.0  # For simplicity, you can refine this if needed
    print(
        f"Probabilities - Win: {win_prob:.2%}, Draw: {draw_prob:.2%}, Lose: {loss_prob:.2%}"
    )
    return win_prob, draw_prob, loss_prob


def draw_probabilities(win_prob, draw_prob, loss_prob):
    print("Drawing probabilities...")
    font = pygame.font.Font("assets/fonts/IosevkaSlab-Regular.ttf", 24)
    text_y = HEIGHT - INFO_HEIGHT + 200
    text_x = WIDTH - 250

    win_text = f"Win: {win_prob:.2%}"
    draw_text = f"Draw: {draw_prob:.2%}"
    loss_text = f"Lose: {loss_prob:.2%}"

    win_surface = font.render(win_text, True, pygame.Color(0, 0, 0))
    draw_surface = font.render(draw_text, True, pygame.Color(0, 0, 0))
    loss_surface = font.render(loss_text, True, pygame.Color(0, 0, 0))

    WINDOW.blit(win_surface, (text_x, text_y))
    WINDOW.blit(draw_surface, (text_x, text_y + 30))
    WINDOW.blit(loss_surface, (text_x, text_y + 60))


def main():
    board = chess.Board()
    clock = pygame.time.Clock()

    selected_square = None
    player_clicks = []
    last_move = None
    elo_rating = 1500
    show_menu = False

    # Move history for undo functionality
    move_history = []

    # Initialize the Maia engine with the default Elo rating
    engine = chess.engine.SimpleEngine.popen_uci(
        [
            "lc0",
            "--weights=assets/models/maia-1500.pb.gz",
        ]
    )
    engine.configure({"Threads": 2})

    stockfish_engine = chess.engine.SimpleEngine.popen_uci(
        "/opt/homebrew/bin/stockfish"
    )

    best_moves = get_best_moves(engine, board)

    input_box = pygame.Rect(WIDTH // 2 - 125, HEIGHT - INFO_HEIGHT + 100, 150, 30)
    color_inactive = pygame.Color("lightskyblue3")
    color_active = pygame.Color("dodgerblue2")
    color = color_inactive
    active = False
    text = ""
    font = pygame.font.Font("assets/fonts/IosevkaSlab-Regular.ttf", 24)

    def redraw_all():
        draw_board()
        highlight_selected_square(WINDOW, selected_square)
        highlight_legal_moves(WINDOW, board, selected_square)
        draw_pieces(board)
        draw_coordinates()
        if last_move:
            draw_move_arrow(WINDOW, last_move.from_square, last_move.to_square)
        draw_arrows(WINDOW, best_moves)
        pygame.draw.rect(
            WINDOW,
            pygame.Color(200, 200, 200),
            pygame.Rect(0, BOARD_SIZE, WIDTH, INFO_HEIGHT),
        )  # Clear the area for best moves
        pygame.draw.rect(
            WINDOW,
            pygame.Color(0, 0, 0),
            pygame.Rect(0, BOARD_SIZE, WIDTH, INFO_HEIGHT),
            3,
        )  # Black border around the bottom area
        display_best_moves_text(best_moves)
        draw_undo_button()
        draw_restart_button()
        draw_input_box()
        draw_make_move_button()
        win_prob, draw_prob, loss_prob = evaluate_position(stockfish_engine, board)
        draw_probabilities(win_prob, draw_prob, loss_prob)
        pygame.display.update()

    def draw_undo_button():
        undo_button = pygame.Rect(10, HEIGHT - INFO_HEIGHT + 10, 175, 60)
        pygame.draw.rect(WINDOW, pygame.Color(255, 0, 0), undo_button)
        font = pygame.font.Font(
            resource_path("assets/fonts/IosevkaSlab-Regular.ttf"), 36
        )
        text_surface = font.render("Undo Move", True, pygame.Color(255, 255, 255))
        WINDOW.blit(text_surface, (undo_button.x + 5, undo_button.y + 5))
        return undo_button

    def draw_restart_button():
        restart_button = pygame.Rect(WIDTH - 170, HEIGHT - INFO_HEIGHT + 10, 150, 60)
        pygame.draw.rect(WINDOW, pygame.Color(0, 0, 255), restart_button)
        font = pygame.font.Font(
            resource_path("assets/fonts/IosevkaSlab-Regular.ttf"), 36
        )
        text_surface = font.render("Restart", True, pygame.Color(255, 255, 255))
        WINDOW.blit(text_surface, (restart_button.x + 5, restart_button.y + 5))
        return restart_button

    def draw_input_box():
        pygame.draw.rect(WINDOW, color, input_box, 2)
        text_surface = font.render(text, True, color)
        WINDOW.blit(text_surface, (input_box.x + 5, input_box.y + 5))
        input_box.w = max(250, text_surface.get_width() + 5)

    def draw_make_move_button():
        make_move_button = pygame.Rect(
            WIDTH // 2 - 75, HEIGHT - INFO_HEIGHT + 140, 150, 40
        )
        pygame.draw.rect(WINDOW, pygame.Color(0, 128, 0), make_move_button)
        font = pygame.font.Font(
            resource_path("assets/fonts/IosevkaSlab-Regular.ttf"), 24
        )
        text_surface = font.render("Make Move", True, pygame.Color(255, 255, 255))
        WINDOW.blit(text_surface, (make_move_button.x + 20, make_move_button.y + 5))
        return make_move_button

    def handle_text_input(event):
        nonlocal text, active, color
        if event.type == pygame.MOUSEBUTTONDOWN:
            if input_box.collidepoint(event.pos):
                active = not active
            else:
                active = False
            color = color_active if active else color_inactive
        if event.type == pygame.KEYDOWN:
            if active:
                if event.key == pygame.K_RETURN:
                    return text
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += event.unicode
        return None

    def make_move_from_input(move_text):
        try:
            move = chess.Move.from_uci(move_text)
            if move in board.legal_moves:
                board.push(move)
                move_history.append(move)
                return True
        except Exception:
            return False
        return False

    # Initial drawing
    redraw_all()

    while not board.is_game_over():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                engine.quit()
                stockfish_engine.quit()
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
                elif draw_make_move_button().collidepoint(event.pos):
                    if make_move_from_input(text):
                        last_move = move_history[-1] if move_history else None
                        best_moves = get_best_moves(engine, board)
                        text = ""
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

            input_move = handle_text_input(event)
            if input_move:
                if make_move_from_input(input_move):
                    last_move = move_history[-1] if move_history else None
                    best_moves = get_best_moves(engine, board)
                    text = ""
                    redraw_all()

        if not show_menu:
            redraw_all()

        clock.tick(30)

    stockfish_engine.quit()
    engine.quit()


if __name__ == "__main__":
    main()
