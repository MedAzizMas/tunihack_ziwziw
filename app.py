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
    cap = pc.setup_camera()
    hand_detector = pc.HandPointerDetector()
    pose_detector = pc.pm.poseDetector()
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
                        squat_analyzer = pc.SquatAnalyser(mode=0)
                    mode_switch_cooldown = 30
                    is_started = True

        elif current_mode == "pushup":
            img_original = cv2.flip(img, 1)
            
            if showing_3d:
                img_original, showing_3d, button_cooldown, finger_controller, should_exit_3d = pc.handle_3d_visualization(
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
                    
                    feedback, count, direction, form = pc.update_feedback_and_count(
                        elbow, shoulder, hip, direction, count, form)
                    pc.draw_ui(img_original, per, bar, count, feedback, form)
                
                back_bounds, help_bounds = pc.draw_control_buttons(img_original)
                
                hand_detector.reset_state()
                results = hand_detector.hands.process(cv2.cvtColor(img_original, cv2.COLOR_BGR2RGB))
                
                if results.multi_hand_landmarks and button_cooldown == 0:
                    for hand_landmarks in results.multi_hand_landmarks:
                        if pc.check_button_press(hand_landmarks, help_bounds, img_original.shape):
                            showing_3d = True
                            button_cooldown = 20
                            if finger_controller is None:
                                from finger_controller_3d import FingerController3D
                                finger_controller = FingerController3D("GingerPerson.stl")
                            break
                        elif pc.check_button_press(hand_landmarks, back_bounds, img_original.shape):
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
                img, showing_3d, button_cooldown, finger_controller, should_exit_3d = pc.handle_3d_visualization(
                    img, finger_controller, hand_detector, showing_3d, button_cooldown
                )
                if should_exit_3d:
                    continue
            else:
                img = squat_analyzer.process_frame(img)
                
                back_bounds, help_bounds = pc.draw_control_buttons(img)
                
                hand_detector.reset_state()
                results = hand_detector.hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                
                if results.multi_hand_landmarks and button_cooldown == 0:
                    hand_landmarks = results.multi_hand_landmarks[0]
                    
                    h, w, _ = img.shape
                    index_finger = hand_landmarks.landmark[8]
                    index_x, index_y = int(index_finger.x * w), int(index_finger.y * h)
                    cv2.circle(img, (index_x, index_y), 5, (0, 255, 0), -1)
                    
                    if pc.check_button_press(hand_landmarks, help_bounds, img.shape):
                        showing_3d = True
                        button_cooldown = 20
                        if finger_controller is None:
                            from finger_controller_3d import FingerController3D
                            finger_controller = FingerController3D("GingerPerson.stl")
                    elif pc.check_button_press(hand_landmarks, back_bounds, img.shape):
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