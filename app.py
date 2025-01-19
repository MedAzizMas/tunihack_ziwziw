from flask import Flask, render_template, Response,jsonify
from pose_processor import PoseProcessor
from pose_analyzer import PoseAnalyzer
from camera_handler import CameraHandler
import numpy as np
import cv2
import PushUpCounter as pc
from threading import Thread
import queue
app = Flask(__name__)

def generate_frames_coach():
    # Initialize everything we need from PushUpCounter
    cap = pc.setup_camera()
    hand_detector = pc.HandPointerDetector()
    pose_detector = pc.pm.poseDetector()
    squat_analyzer = None
    
    count = 0
    direction = 0
    form = 0
    
    current_mode = "selection"
    exercise_type = None
    mode_switch_cooldown = 0
    is_paused = False
    button_cooldown = 0
    is_started = False

    while True:
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
                        squat_analyzer = pc.SquatAnalyser(mode=0)
                    mode_switch_cooldown = 30
                    is_started = True
        
        elif current_mode == "pushup":
            # Keep mirror reflection in pushup mode
            img_original = cv2.flip(img, 1)
            
            # Process both pose and hand detection
            img_original = pose_detector.findPose(img_original, False)
            lmList = pose_detector.findPosition(img_original, False)

            # Draw control buttons
            back_bounds, stop_bounds = pc.draw_control_buttons(img_original)
            
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
                    
                    if is_clicking:
                        # Check back button
                        if (back_bounds[0] < index_x < back_bounds[2] and 
                            back_bounds[1] < index_y < back_bounds[3]):
                            current_mode = "selection"
                            count = 0
                            direction = 0
                            form = 0
                            mode_switch_cooldown = 30
                            button_cooldown = 20
                        
                        # Check stop/continue button
                        elif (stop_bounds[0] < index_x < stop_bounds[2] and 
                              stop_bounds[1] < index_y < stop_bounds[3]):
                            is_paused = not is_paused
                            button_cooldown = 20

            # Process push-up detection and counting
            if len(lmList) != 0 and not is_paused:
                elbow = pose_detector.findAngle(img_original, 12, 14, 16)
                shoulder = pose_detector.findAngle(img_original, 14, 12, 24)
                hip = pose_detector.findAngle(img_original, 12, 24, 26)
                per = np.interp(elbow, (90, 160), (0, 100))
                bar = np.interp(elbow, (90, 160), (380, 50))
                feedback, count, direction, form = pc.update_feedback_and_count(
                    elbow, shoulder, hip, direction, count, form)
                pc.draw_ui(img_original, per, bar, count, feedback, form)

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

        # Convert frame to jpg format
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        
        # Yield the frame in HTTP response format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    


pose_processor = PoseProcessor()
pose_analyzer = PoseAnalyzer()
camera_handler = CameraHandler(pose_processor, pose_analyzer)
arr = np.array([])

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/coach')
def coach():
    return render_template('coach.html')

@app.route('/student')
def student():
    return render_template('student.html')

@app.route('/stats')
def stats():
    return render_template('stats.html')

@app.route('/yoga')
def yoga():
    return render_template('yoga.html')
@app.route('/analyse_yoga')
def analyse_yoga():
    return render_template('analyse_yoga.html')
@app.route('/get_accuracy')
def get_accuracy():
    return jsonify({'accuracy': getattr(app, 'current_accuracy', 0)})

@app.route('/video')
def video():
    return Response(
        camera_handler.generate_frames(arr),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames_coach(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)