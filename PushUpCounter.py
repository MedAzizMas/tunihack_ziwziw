import cv2
import numpy as np
import PoseModule_menu as pm
from hand_pointer_detector import HandPointerDetector
from squat_analyser import SquatAnalyser

def setup_camera():
    """Initializes the video capture object."""
    return cv2.VideoCapture(0)

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

def draw_control_buttons(img):
    """Draws Back and Stop/Continue buttons."""
    # Back button
    back_x, back_y = 50, 30
    back_w, back_h = 100, 40
    cv2.rectangle(img, (back_x, back_y), (back_x + back_w, back_y + back_h), (0, 200, 0), cv2.FILLED)
    cv2.rectangle(img, (back_x, back_y), (back_x + back_w, back_y + back_h), (0, 255, 0), 2)
    cv2.putText(img, "BACK", (back_x + 20, back_y + 28), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Stop/Continue button
    stop_x, stop_y = 170, 30
    stop_w, stop_h = 120, 40

    return (back_x, back_y, back_x + back_w, back_y + back_h), (stop_x, stop_y, stop_x + stop_w, stop_y + stop_h)

def main():
    cap = setup_camera()
    hand_detector = HandPointerDetector()
    pose_detector = pm.poseDetector()
    squat_analyzer = None  # Will be initialized when needed
    
    count = 0
    direction = 0
    form = 0
    
    current_mode = "selection"
    exercise_type = None  # Will store either "pushup" or "squat"
    mode_switch_cooldown = 0
    is_paused = False
    button_cooldown = 0
    is_started = False

    while cap.isOpened():
        ret, img = cap.read()
        if not ret:
            break
            
        if current_mode == "selection":
            # Process hand pointer detection (includes flip)
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
            # Keep mirror reflection in pushup mode
            img_original = cv2.flip(img, 1)
            
            # Process both pose and hand detection
            img_original = pose_detector.findPose(img_original, False)
            lmList = pose_detector.findPosition(img_original, False)

            # Draw control buttons
            back_bounds, stop_bounds = draw_control_buttons(img_original)
            
            # Draw Stop/Continue button with dynamic text
            stop_text = "CONTINUE" if is_paused else "STOP"
            cv2.rectangle(img_original, (stop_bounds[0], stop_bounds[1]), 
                         (stop_bounds[2], stop_bounds[3]), (0, 200, 0), cv2.FILLED)
            cv2.rectangle(img_original, (stop_bounds[0], stop_bounds[1]), 
                         (stop_bounds[2], stop_bounds[3]), (0, 255, 0), 2)
            cv2.putText(img_original, stop_text, 
                       (stop_bounds[0] + 10, stop_bounds[1] + 28), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Process hand detection for button interaction
            hand_detector.reset_state()
            results = hand_detector.hands.process(cv2.cvtColor(img_original, cv2.COLOR_BGR2RGB))
            
            if results.multi_hand_landmarks and button_cooldown == 0:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw hand landmarks
                    hand_detector.mp_draw.draw_landmarks(
                        img_original, hand_landmarks, hand_detector.mp_hands.HAND_CONNECTIONS)
                    
                    # Get finger coordinates
                    h, w, c = img_original.shape
                    index_finger = hand_landmarks.landmark[8]
                    thumb = hand_landmarks.landmark[4]
                    
                    # Convert to pixel coordinates
                    index_x, index_y = int(index_finger.x * w), int(index_finger.y * h)
                    thumb_x, thumb_y = int(thumb.x * w), int(thumb.y * h)
                    
                    # Calculate distance between thumb and index finger
                    distance = np.sqrt((thumb_x - index_x)**2 + (thumb_y - index_y)**2)
                    is_clicking = distance > hand_detector.MIN_DISTANCE
                    
                    # Draw pointer
                    cv2.circle(img_original, (index_x, index_y), 12, (0, 255, 0), 2)
                    cv2.circle(img_original, (index_x, index_y), 4, (0, 255, 0), cv2.FILLED)
                    
                    if is_clicking:
                        # Check back button (no need to flip x-coordinate anymore)
                        if (back_bounds[0] < index_x < back_bounds[2] and 
                            back_bounds[1] < index_y < back_bounds[3]):
                            current_mode = "selection"
                            count = 0
                            direction = 0
                            form = 0
                            mode_switch_cooldown = 30
                            button_cooldown = 20
                        
                        # Check stop/continue button (no need to flip x-coordinate anymore)
                        elif (stop_bounds[0] < index_x < stop_bounds[2] and 
                              stop_bounds[1] < index_y < stop_bounds[3]):
                            is_paused = not is_paused
                            button_cooldown = 20

            # Process push-up detection and counting
            if len(lmList) != 0 and not is_paused:
                # Use right side points since image is flipped
                elbow = pose_detector.findAngle(img_original, 12, 14, 16)
                shoulder = pose_detector.findAngle(img_original, 14, 12, 24)
                hip = pose_detector.findAngle(img_original, 12, 24, 26)
                per = np.interp(elbow, (90, 160), (0, 100))
                bar = np.interp(elbow, (90, 160), (380, 50))
                feedback, count, direction, form = update_feedback_and_count(
                    elbow, shoulder, hip, direction, count, form)
                draw_ui(img_original, per, bar, count, feedback, form)

                # Check if 10 pushups are completed
                if count >= 10:
                    current_mode = "selection"
                    count = 0
                    direction = 0
                    form = 0
                    mode_switch_cooldown = 30
                    continue
            
            img = img_original

        elif current_mode == "squat":
            # Use the squat analyzer
            img = squat_analyzer.process_frame(img)
            
            # Check for return to selection
            should_return, return_to = squat_analyzer.get_return_state()
            if should_return:
                current_mode = "selection"
                exercise_type = None
                is_started = False
                mode_switch_cooldown = 30
                continue

        # Update cooldowns
        if mode_switch_cooldown > 0:
            mode_switch_cooldown -= 1
        if button_cooldown > 0:
            button_cooldown -= 1
        
        cv2.imshow('Exercise Counter', img)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()