import mediapipe as mp
from mediapipe import solutions
import numpy as np
import cv2
from cv2 import waitKey, imshow, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, COLOR_BGR2RGB, cvtColor
import time

mp_drawing = solutions.drawing_utils
mp_pose = solutions.pose
mp_hands = solutions.hands

class SquatAnalyser():
    def __init__(self, *, mode: int, file_path: str = None):
        '''
            mode 0 -> Inbuilt Webcam
            mode 1 -> Video File
        '''
        self.frame_width = 640
        self.frame_height = 480
        self.frame_size = np.array([self.frame_width, self.frame_height])
        
        self.joints = {}
        self.reps = 0
        self.initial_back_length = 0
        self.initial_heel_angle = 0
        self.stage = "up"
        
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0
        )
        
        # Add hands detector
        self.hands = mp_hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            max_num_hands=1  # We only need one hand for the button
        )
        
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.line_type = cv2.LINE_AA
        
        # Add back button parameters
        self.back_button = {
            'x': 10,
            'y': self.frame_height - 50,
            'width': 100,
            'height': 40,
            'text': 'Back (Q)'
        }
        self.should_return = False
        self.return_to = 'select_mode'  # Specify where to return to
        
        # Add button interaction parameters
        self.button_clicked = False
        self.click_start_time = 0
        self.CLICK_DURATION = 1.0  # Duration in seconds to hold for click
        
    def initialise_bounds(self, shoulder, hip, heel, foot_index):
        left_upper_back_pixel = np.multiply(shoulder, self.frame_size)
        left_lower_back_pixel = np.multiply(hip, self.frame_size)
        self.initial_back_length = np.linalg.norm(left_upper_back_pixel-left_lower_back_pixel)
        self.initial_heel_angle = np.abs(180*np.arctan2(heel[1]-foot_index[1],heel[0]-foot_index[0])/np.pi)      
          
    def calculate_joint_angle(self, *, j1, j2, j3):
        '''
            Calculates angle between j1 j2 and j3
        '''
        v1 = np.array(j1-j2)
        v2 = np.array(j3-j2)
        cos_angle = np.dot(v1,v2)/(np.linalg.norm(v1)*np.linalg.norm(v2))
        radians = np.arccos(np.clip(cos_angle, -1, 1))
        angle = np.abs(radians*180.0/np.pi)
        if angle > 180:
            angle = 360 - angle
        return angle
    
    def back_slacking(self, image):
        upper_back = np.multiply(self.joints['shoulder'],self.frame_size)
        lower_back = np.multiply(self.joints['hip'],self.frame_size)
        distance = np.linalg.norm(upper_back - lower_back)
        mid_back = ((upper_back + lower_back)/2).astype(int)
        if distance+7< self.initial_back_length:
            cv2.circle(image, mid_back, 3, (22, 35, 219), -1)
            cv2.line(image, mid_back, [mid_back[0]+10, mid_back[1]-10], (255, 255, 255), 1, cv2.LINE_AA)
            cv2.line(image, [mid_back[0]+10, mid_back[1]-10], [mid_back[0]+60, mid_back[1]-10], (255, 255, 255), 1, cv2.LINE_AA)
            text = "Excessive Spine Flexion"
            position = (int(mid_back[0] + 60), int(mid_back[1] - 10))
            (text_width, text_height), baseline = cv2.getTextSize(text, self.font, 0.5, 1)
            rect_start = (position[0] - 5, position[1] - text_height - 5)
            rect_end = (position[0] + text_width + 5, position[1] + baseline + 5)
            cv2.rectangle(image, rect_start, rect_end, (0, 0, 0), cv2.FILLED)
            cv2.putText(image, text, position, self.font, 0.5, (255, 255, 255), 1, self.line_type)
            return False
        return True
       
    def heels_off_ground(self, image):
        heel = self.joints['heel']
        foot_index = self.joints['foot index']
        radians = np.arctan2(heel[1]-foot_index[1], heel[0]-foot_index[0])
        angle = np.abs(radians*180/np.pi)
        if angle > self.initial_heel_angle + 3:
            mid = np.multiply(heel, self.frame_size).astype(int)
            cv2.circle(image, mid, 3, (22, 35, 219), -1)
            cv2.line(image, mid, [mid[0]+10, mid[1]-10], (255, 255, 255), 1, cv2.LINE_AA)
            cv2.line(image, [mid[0]+10, mid[1]-10], [mid[0]+60, mid[1]-10], (255, 255, 255), 1, cv2.LINE_AA)
            text = "Heels Off Ground"
            position = (int(mid[0] + 60), int(mid[1] - 10))
            (text_width, text_height), baseline = cv2.getTextSize(text, self.font, 0.5, 1)
            rect_start = (position[0] - 5, position[1] - text_height - 5)
            rect_end = (position[0] + text_width + 5, position[1] + baseline + 5)
            cv2.rectangle(image, rect_start, rect_end, (0, 0, 0), cv2.FILLED)
            cv2.putText(image, text, position, self.font, 0.5, (255, 255, 255), 1, self.line_type)
        
    def knee_over_toes(self, image):
        lower_back = self.joints['hip']
        knee = self.joints['knee']
        foot_index = self.joints['foot index']
        radians = np.arctan2(lower_back[1]-knee[1], lower_back[0]-knee[0])
        angle = np.abs(radians*180.0/np.pi)
        if angle < 44 and knee[0] > foot_index[0]:
            mid = np.multiply(knee, self.frame_size).astype(int)
            cv2.circle(image, mid, 3, (22, 35, 219), -1)
            cv2.line(image, mid, [mid[0]+10, mid[1]-10], (255, 255, 255), 1, cv2.LINE_AA)
            cv2.line(image, [mid[0]+10, mid[1]-10], [mid[0]+60, mid[1]-10], (255, 255, 255), 1, cv2.LINE_AA)
            text = "Knees Behind Toes"
            position = (int(mid[0] + 60), int(mid[1] - 10))
            (text_width, text_height), baseline = cv2.getTextSize(text, self.font, 0.5, 1)
            rect_start = (position[0] - 5, position[1] - text_height - 5)
            rect_end = (position[0] + text_width + 5, position[1] + baseline + 5)
            cv2.rectangle(image, rect_start, rect_end, (0, 0, 0), cv2.FILLED)
            cv2.putText(image, text, position, self.font, 0.5, (255, 255, 255), 1, self.line_type)
            return False
        else:
            return True
        
    def ensure_proper_depth(self, image):
        lower_back = self.joints['hip']
        knee = self.joints['knee']
        radians = np.arctan2(lower_back[1]-knee[1], lower_back[0]-knee[0])
        angle = np.abs(radians*180.0/np.pi)
        if angle < 20:
            text = "Awesome Depth"
            position = (10, 70)
            (text_width, text_height), baseline = cv2.getTextSize(text, self.font, 1, 1)
            rect_start = (position[0] - 5, position[1] - text_height - 5)
            rect_end = (position[0] + text_width + 5, position[1] + baseline + 5)
            cv2.rectangle(image, rect_start, rect_end, (0, 0, 0), cv2.FILLED)
            cv2.putText(image, text, position, self.font, 1, (23, 185, 43), 1, self.line_type)
            return True
        return False
      
    def show_reps_on_screen(self,image,knee_hip_angle):
        if(knee_hip_angle<25 and self.stage=="up"):
            self.stage = "down"
        elif(knee_hip_angle>30 and self.stage=="down"):
            self.reps+=1
            self.stage= "up"
        cv2.putText(image,"Reps: "+str(self.reps),(10,30),
                    self.font,1,(255,255,255),2,self.line_type)
          
    def draw_landmarks(self,image):
        #draw Circles on joints
        for joint in self.joints.values():
            cv2.circle(image,np.multiply(joint,self.frame_size).astype(int),3,(135, 53, 3),-1)
            cv2.circle(image,np.multiply(joint,self.frame_size).astype(int),6,(194, 99, 41),1)
        # draw lines between joints
        pairs = [['shoulder','hip'],['hip','knee'],['knee','ankle'],['heel','foot index'],['ankle','heel']]
        COLOR = (237, 185, 102)
        for pair in pairs:
            cv2.line(image,np.multiply(self.joints[pair[0]],self.frame_size).astype(int),
                     np.multiply(self.joints[pair[1]],self.frame_size).astype(int),COLOR,1,self.line_type)
    
    def check_button_press(self, image, index_finger, thumb):
        """Check if index finger is hovering over button and handle press"""
        # Convert to pixel coordinates
        x, y = int(index_finger[0] * self.frame_width), int(index_finger[1] * self.frame_height)
        thumb_x, thumb_y = int(thumb[0] * self.frame_width), int(thumb[1] * self.frame_height)
        
        # Calculate distance between thumb and index finger
        distance = np.sqrt((thumb_x - x)**2 + (thumb_y - y)**2)
        
        # Check if finger is over button
        btn = self.back_button
        is_over_button = (btn['x'] <= x <= btn['x'] + btn['width'] and 
                         btn['y'] <= y <= btn['y'] + btn['height'])
        
        current_time = time.time()
        
        if is_over_button:
            # Draw indicator dot
            cv2.circle(image, (x, y), 10, (0, 255, 0), -1)
            
            if distance > 10:  # New condition
                if not self.button_clicked:
                    self.button_clicked = True
                    self.click_start_time = current_time
                    
                # Draw progress circle
                elapsed_time = current_time - self.click_start_time
                progress = min(elapsed_time / self.CLICK_DURATION, 1.0)
                
                center = (x, y)
                radius = 20
                angle = int(360 * progress)
                
                # Draw progress circle
                if progress < 1:
                    cv2.circle(image, center, radius, (255, 255, 255), 2)
                    if angle > 0:
                        cv2.ellipse(image, center, (radius, radius), 
                                  0, 0, angle, (0, 255, 0), 2)
                
                # Check if button held long enough
                if elapsed_time >= self.CLICK_DURATION:
                    self.should_return = True
                    
            else:
                self.button_clicked = False
        else:
            self.button_clicked = False

    def process_frame(self, frame):
        """Process a single frame and return the processed image."""
        # Mirror the frame first
        frame = cv2.flip(frame, 1)
        
        # Resize frame to target size
        frame = cv2.resize(frame, (self.frame_width, self.frame_height))
        
        # Process frame for pose and hands
        image = cvtColor(frame, COLOR_BGR2RGB)
        image.flags.writeable = False
        
        # Process pose
        pose_results = self.pose.process(image)
        
        # Process hands
        hand_results = self.hands.process(image)
        
        image.flags.writeable = True
        image = cvtColor(image, COLOR_BGR2RGB)

        # Draw hand landmarks if detected
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                    mp_drawing.DrawingSpec(color=(250, 44, 250), thickness=2, circle_radius=2)
                )
                
                # Get index finger and thumb positions
                index_finger = [
                    hand_landmarks.landmark[8].x,  # INDEX_FINGER_TIP
                    hand_landmarks.landmark[8].y
                ]
                thumb = [
                    hand_landmarks.landmark[4].x,  # THUMB_TIP
                    hand_landmarks.landmark[4].y
                ]
                
                # Check for button press with hand landmarks
                self.check_button_press(image, index_finger, thumb)

        if pose_results.pose_landmarks:
            landmarks = pose_results.pose_landmarks.landmark
            landmark_positions = {
                'shoulder': [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y],
                'hip': [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                       landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y],
                'knee': [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                        landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y],
                'ankle': [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y],
                'heel': [landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value].x,
                        landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value].y],
                'foot index': [landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].y]
            }
            
            self.joints = {k: np.array(v) for k, v in landmark_positions.items()}

            self.draw_landmarks(image)

            knee_hip_angle = np.abs(180*np.arctan2(self.joints['hip'][1]-self.joints['knee'][1],
                                                  self.joints['hip'][0]-self.joints['knee'][0])/np.pi)

            if 167 < self.calculate_joint_angle(j1=self.joints['hip'], 
                                              j2=self.joints['knee'],
                                              j3=self.joints['ankle']) < 180:
                self.initialise_bounds(self.joints['shoulder'],
                                     self.joints['hip'],
                                     self.joints['heel'],
                                     self.joints['foot index'])

            self.back_slacking(image)
            self.knee_over_toes(image)
            self.heels_off_ground(image)
            self.ensure_proper_depth(image)
            self.show_reps_on_screen(image, knee_hip_angle)

        # Draw back button
        self.draw_back_button(image)
        
        return image

    def draw_back_button(self, image):
        """Draw the back button on the frame"""
        x, y = self.back_button['x'], self.back_button['y']
        w, h = self.back_button['width'], self.back_button['height']
        
        # Draw button rectangle
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), cv2.FILLED)
        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 255), 1)
        
        # Add text
        text_size = cv2.getTextSize(self.back_button['text'], self.font, 0.7, 2)[0]
        text_x = x + (w - text_size[0]) // 2
        text_y = y + (h + text_size[1]) // 2
        cv2.putText(image, self.back_button['text'], (text_x, text_y), 
                   self.font, 0.7, (255, 255, 255), 2, self.line_type)

    def get_return_state(self):
        """Returns the current return state and destination."""
        return self.should_return, self.return_to

    def __del__(self):
        self.pose.close()
        self.hands.close()
