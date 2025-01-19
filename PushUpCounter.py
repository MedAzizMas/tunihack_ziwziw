import cv2
import numpy as np
import PoseModule_menu as pm
from hand_pointer_detector import HandPointerDetector
from squat_analyser import SquatAnalyser
def setup_camera():
    """Initializes the video capture object."""
    return cv2.VideoCapture(0)

def handle_3d_visualization(img, finger_controller, hand_detector, showing_3d, button_cooldown):
    """
    Handles 3D model visualization and interaction for both pushup and squat modes.
    """
    if not showing_3d:
        return img, showing_3d, button_cooldown, finger_controller, False

    # Initialize 3D controller if needed
    if finger_controller is None:
        from finger_controller_3d import FingerController3D
        finger_controller = FingerController3D("GingerPerson.stl")
    
    # Ensure image is flipped for 3D mode
    img = cv2.flip(img, 1) if not isinstance(img, np.ndarray) else img
    rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = finger_controller.hands.process(rgb_frame)
    
    # Process hand landmarks and draw connections
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            finger_controller.mp_draw.draw_landmarks(
                img, 
                hand_landmarks, 
                finger_controller.mp_hands.HAND_CONNECTIONS
            )
            finger_controller.process_hand_landmarks(hand_landmarks)
    
    # Render 3D model
    gl_surface = finger_controller.draw_model()
    mask = gl_surface[:, :, 3] > 0
    img[mask] = gl_surface[mask][:, :3]
    
    # Draw back button only (no help button in 3D mode)
    back_bounds, _ = draw_control_buttons(img, show_help=False)
    
    # Check for back button press
    if results.multi_hand_landmarks and button_cooldown == 0:
        hand_landmarks = results.multi_hand_landmarks[0]
        if check_button_press(hand_landmarks, back_bounds, img.shape):
            showing_3d = False
            button_cooldown = 20
            return img, showing_3d, button_cooldown, finger_controller, True
    
    return img, showing_3d, button_cooldown, finger_controller, False

def update_feedback_and_count(elbow, shoulder, hip, direction, count, form):
    """Determines the feedback message and updates the count based on the angles."""
    feedback = "Fix Form"
    if elbow > 160 and shoulder > 40 and hip > 160:
        form = 1
    if form == 1:
        if elbow <= 90 and hip > 160:
            feedback = "Up"
            if direction == 0:
                count += 0.5
                direction = 1
        elif elbow > 160 and shoulder > 40 and hip > 160:
            feedback = "Down"
            if direction == 1:
                count += 0.5
                direction = 0
        else:
            feedback = "Fix Form"
    return feedback, count, direction, form

def draw_ui(img, per, bar, count, feedback, form):
    """Draws the UI elements on the image."""
    if form == 1:
        cv2.rectangle(img, (580, 50), (600, 380), (0, 255, 0), 3)
        cv2.rectangle(img, (580, int(bar)), (600, 380), (0, 255, 0), cv2.FILLED)
        cv2.putText(img, f'{int(per)}%', (565, 430), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)

    cv2.rectangle(img, (0, 380), (100, 480), (0, 255, 0), cv2.FILLED)
    cv2.putText(img, str(int(count)), (25, 455), cv2.FONT_HERSHEY_PLAIN, 5, (255, 0, 0), 5)
    
    cv2.rectangle(img, (500, 0), (640, 40), (255, 255, 255), cv2.FILLED)
    cv2.putText(img, feedback, (500, 40), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

def draw_control_buttons(img, show_help=True):
    """Draws Back and optionally Help button."""
    back_x, back_y = 50, 30
    back_w, back_h = 100, 40
    cv2.rectangle(img, (back_x, back_y), (back_x + back_w, back_y + back_h), (0, 200, 0), cv2.FILLED)
    cv2.rectangle(img, (back_x, back_y), (back_x + back_w, back_y + back_h), (0, 255, 0), 2)
    cv2.putText(img, "BACK", (back_x + 20, back_y + 28), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    if show_help:
        help_x, help_y = 170, 30
        help_w, help_h = 40, 40
        cv2.rectangle(img, (help_x, help_y), (help_x + help_w, help_y + help_h), (0, 200, 200), cv2.FILLED)
        cv2.rectangle(img, (help_x, help_y), (help_x + help_w, help_y + help_h), (0, 255, 255), 2)
        cv2.putText(img, "?", (help_x + 15, help_y + 28), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return (back_x, back_y, back_x + back_w, back_y + back_h), \
               (help_x, help_y, help_x + help_w, help_y + help_h)
    
    return (back_x, back_y, back_x + back_w, back_y + back_h), None

def check_button_press(hand_landmarks, bounds, img_shape):
    """Helper function to check if a button is being pressed"""
    if not hand_landmarks or not bounds:
        return False
        
    h, w, _ = img_shape
    index_finger = hand_landmarks.landmark[8]
    thumb = hand_landmarks.landmark[4]
    middle_finger = hand_landmarks.landmark[12]
    
    index_x, index_y = int(index_finger.x * w), int(index_finger.y * h)
    thumb_x, thumb_y = int(thumb.x * w), int(thumb.y * h)
    middle_x, middle_y = int(middle_finger.x * w), int(middle_finger.y * h)
    
    if not (bounds[0] < index_x < bounds[2] and bounds[1] < index_y < bounds[3]):
        return False
    
    thumb_index_dist = np.sqrt((thumb_x - index_x)**2 + (thumb_y - index_y)**2)
    middle_index_dist = np.sqrt((middle_x - index_x)**2 + (middle_y - index_y)**2)
    
    return thumb_index_dist > 30 and middle_index_dist < 30

def generate_frames_coach():
    cap = setup_camera()
    hand_detector = HandPointerDetector()
    pose_detector = pm.poseDetector()
    squat_analyzer = None
    finger_controller = None
    
    count = 0
    direction = 0
    form = 0
    
    current_mode = "selection"
    exercise_type = None
    mode_switch_cooldown = 0
    is_paused = False
    button_cooldown = 0
    is_started = False
    showing_3d = False

    while True:
        ret, img = cap.read()
        if not ret:
            break
            
        if current_mode == "selection":
            # Reset 3D-related variables when returning to selection mode
            showing_3d = False
            finger_controller = None
            hand_detector.reset_state()
            img, selected_mode = hand_detector.process_frame(img)
            
            if mode_switch_cooldown == 0:
                if selected_mode == "Push-up Counter":
                    exercise_type = "pushup"
                elif selected_mode == "Squat Analyzer":
                    exercise_type = "squat"
                elif selected_mode == "Start Exercise" and exercise_type:
                    current_mode = exercise_type
                    if exercise_type == "squat":
                        squat_analyzer = SquatAnalyser(mode=0)
                    mode_switch_cooldown = 30
                    is_started = True

        elif current_mode == "pushup":
            img_original = cv2.flip(img, 1)
            
            if showing_3d:
                img_original, showing_3d, button_cooldown, finger_controller, should_exit_3d = handle_3d_visualization(
                    img_original, finger_controller, hand_detector, showing_3d, button_cooldown
                )
                if should_exit_3d:
                    continue
            else:
                img_original = pose_detector.findPose(img_original, False)
                lmList = pose_detector.findPosition(img_original, False)
                
                if len(lmList) != 0:
                    elbow = pose_detector.findAngle(img_original, 12, 14, 16)
                    shoulder = pose_detector.findAngle(img_original, 14, 12, 24)
                    hip = pose_detector.findAngle(img_original, 12, 24, 26)
                    
                    per = np.interp(elbow, (90, 160), (0, 100))
                    bar = np.interp(elbow, (90, 160), (380, 50))
                    
                    feedback, count, direction, form = update_feedback_and_count(
                        elbow, shoulder, hip, direction, count, form)
                    draw_ui(img_original, per, bar, count, feedback, form)
                
                back_bounds, help_bounds = draw_control_buttons(img_original)
                
                hand_detector.reset_state()
                results = hand_detector.hands.process(cv2.cvtColor(img_original, cv2.COLOR_BGR2RGB))
                
                if results.multi_hand_landmarks and button_cooldown == 0:
                    for hand_landmarks in results.multi_hand_landmarks:
                        if check_button_press(hand_landmarks, help_bounds, img_original.shape):
                            showing_3d = True
                            button_cooldown = 20
                            if finger_controller is None:
                                from finger_controller_3d import FingerController3D
                                finger_controller = FingerController3D("GingerPerson.stl")
                            break
                        elif check_button_press(hand_landmarks, back_bounds, img_original.shape):
                            current_mode = "selection"
                            count = 0
                            direction = 0
                            form = 0
                            mode_switch_cooldown = 30
                            button_cooldown = 20
                            finger_controller = None
                            break

            img = img_original

        elif current_mode == "squat":
            if showing_3d:
                img, showing_3d, button_cooldown, finger_controller, should_exit_3d = handle_3d_visualization(
                    img, finger_controller, hand_detector, showing_3d, button_cooldown
                )
                if should_exit_3d:
                    continue
            else:
                img = squat_analyzer.process_frame(img)
                
                back_bounds, help_bounds = draw_control_buttons(img)
                
                hand_detector.reset_state()
                results = hand_detector.hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                
                if results.multi_hand_landmarks and button_cooldown == 0:
                    hand_landmarks = results.multi_hand_landmarks[0]
                    
                    h, w, _ = img.shape
                    index_finger = hand_landmarks.landmark[8]
                    index_x, index_y = int(index_finger.x * w), int(index_finger.y * h)
                    cv2.circle(img, (index_x, index_y), 5, (0, 255, 0), -1)
                    
                    if check_button_press(hand_landmarks, help_bounds, img.shape):
                        showing_3d = True
                        button_cooldown = 20
                        if finger_controller is None:
                            from finger_controller_3d import FingerController3D
                            finger_controller = FingerController3D("GingerPerson.stl")
                    elif check_button_press(hand_landmarks, back_bounds, img.shape):
                        current_mode = "selection"
                        mode_switch_cooldown = 30
                        button_cooldown = 20
                        finger_controller = None

        if mode_switch_cooldown > 0:
            mode_switch_cooldown -= 1
        if button_cooldown > 0:
            button_cooldown -= 1
        
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def main():
    """Main function to run the application directly"""
    cap = setup_camera()
    for frame in generate_frames_coach():
        frame_data = frame.split(b'\r\n\r\n')[1]
        frame_array = np.frombuffer(frame_data, dtype=np.uint8)
        frame_image = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        
        cv2.imshow('Exercise Counter', frame_image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()