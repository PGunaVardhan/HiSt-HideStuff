# Manages phase 2 : Gesture Authetication

import cv2
import numpy as np

# Global variables
drawing = False  # True when mouse is pressed
last_point = None  # Track last point for drawing
whiteboard = None  # Whiteboard
threshold = 0.25  # Contour similarity threshold (lower is better match)
star_template = cv2.imread(r"C:\Users\ASUS\OneDrive\Documents\Hyperworks_HomeTask\star_template.png", 0)  # Load star template in grayscale


# Mouse callback function
def mouse_event(event, x, y, flags, param):
    global drawing, last_point, whiteboard

    if event == cv2.EVENT_LBUTTONDOWN:  # Left mouse button down
        drawing = True
        last_point = (x, y)
    elif event == cv2.EVENT_MOUSEMOVE and drawing:  # Mouse move while holding left button
        if last_point:
            cv2.line(whiteboard, last_point, (x, y), (0, 0, 0), thickness=2)
            last_point = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:  # Left mouse button up
        drawing = False
        last_point = None


# Overlay the instruction text and template on the whiteboard
def overlay_instructions(board, template):
    # Copy the whiteboard to avoid overwriting
    annotated_board = board.copy()

    # Add instruction text
    instruction_text = "Draw a star on the whiteboard (holding Left Mouse Button) and press Enter:"
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_scale = 1
    thickness = 2
    color = (0, 0, 0)  # Black text
    y0, dy = 50, 30  # Starting position and line spacing

    for i, line in enumerate(instruction_text.splitlines()):
        y = y0 + i * dy
        cv2.putText(annotated_board, line, (50, y), font, text_scale, color, thickness)

    # Resize and position the star template on the whiteboard
    small_template = cv2.resize(template, (100, 100))  # Resize to a small size
    x_offset, y_offset = 50, 100
    annotated_board[y_offset:y_offset + small_template.shape[0], x_offset:x_offset + small_template.shape[1]] = \
         cv2.cvtColor(small_template, cv2.COLOR_GRAY2BGR)

    return annotated_board


# Check for star using contour matching
def check_for_star(board):
    global star_template

    # Convert the whiteboard to grayscale
    gray_board = cv2.cvtColor(board, cv2.COLOR_BGR2GRAY)

    # Threshold the whiteboard to isolate the drawing
    _, binary_board = cv2.threshold(gray_board, 240, 255, cv2.THRESH_BINARY_INV)

    # Threshold the star template to isolate the black star
    _, binary_star = cv2.threshold(star_template, 240, 255, cv2.THRESH_BINARY_INV)

    # Find contours in the whiteboard drawing
    board_contours, _ = cv2.findContours(binary_board, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Find contours in the star template
    star_contours, _ = cv2.findContours(binary_star, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not star_contours or not board_contours:
        return False  # No valid contours found

    star_contour = star_contours[0]  # Assume a single star in the template

    # Compare each board contour with the star contour
    for contour in board_contours:
        similarity = cv2.matchShapes(star_contour, contour, cv2.CONTOURS_MATCH_I1, 0)
        print(f"Similarity between your gesture and actual template: {(1-similarity)*100}")
        if similarity < threshold:  # Lower similarity indicates a better match
            return True

    return False


def gesture_auth():
    global whiteboard

    # Create a whiteboard
    screen_width, screen_height = 1920, 1080  # Set screen size (or get dynamically)
    whiteboard = np.ones((screen_height, screen_width, 3), dtype=np.uint8) * 255

    # Display whiteboard
    cv2.namedWindow("Whiteboard", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Whiteboard", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.setMouseCallback("Whiteboard", mouse_event)

    while True:
        # Overlay instructions on the current whiteboard
        annotated_board = overlay_instructions(whiteboard, star_template)

        # Show the whiteboard with instructions
        cv2.imshow("Whiteboard", annotated_board)

        # Check for 'Enter' key press
        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # Enter key
            break

    # Check for star presence
    result = check_for_star(whiteboard)

    # Close the window
    cv2.destroyAllWindows()

    return result

# Test the function
# if __name__ == "__main__":
#     result = gesture_auth()
#     print("Star detected:", result)
