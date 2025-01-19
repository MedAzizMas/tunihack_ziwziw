import cv2
import mediapipe as mp
import numpy as np
import time

class HandPointerDetector:
    def __init__(self):
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Define rectangles coordinates (x, y, width, height)
        self.rectangles = [
            {
                "x": 240, "y": 125,  # Adjusted position
                "w": 160, "h": 60,
                "color": (0, 200, 0),
                "count": 0,
                "name": "Push-up Counter"
            },
            {
                "x": 240, "y": 225,  # New squat button
                "w": 160, "h": 60,
                "color": (0, 200, 0),
                "count": 0,
                "name": "Squat Analyzer"
            },
            {
                "x": 240, "y": 325,  # Start button
                "w": 160, "h": 60,
                "color": (0, 200, 0),
                "count": 0,
                "name": "Start Exercise"
            }
        ]
        
        self.clicked = False
        self.MIN_DISTANCE = 50
        self.selected_mode = None
        self.hover_time = None
        self.HOVER_DURATION = 1.0  # seconds
        self.reset_state()

    def reset_state(self):
        """Reset the detector state"""
        self.clicked = False
        self.selected_mode = None

    def process_frame(self, img, return_position=False):
        """Process frame and detect hand pointer.
        Args:
            img: Input image
            return_position: If True, returns pointer position instead of selected mode
        """
        # Flip the image horizontally
        img = cv2.flip(img, 1)
        
        # Convert BGR to RGB
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Process hand detection
        results = self.hands.process(rgb_img)
        
        pointer_pos = None  # Store pointer position
        
        # Draw stylized rectangles
        for rect in self.rectangles:
            # Draw main button with gradient effect
            cv2.rectangle(img, 
                         (rect["x"], rect["y"]), 
                         (rect["x"] + rect["w"], rect["y"] + rect["h"]), 
                         (0, 180, 0), cv2.FILLED)  # Darker base
            
            # Add border glow
            cv2.rectangle(img, 
                         (rect["x"], rect["y"]), 
                         (rect["x"] + rect["w"], rect["y"] + rect["h"]), 
                         (0, 255, 0), 2)  # Bright border
            
            # Add text with better positioning
            text = rect["name"]
            font_scale = 0.8 if len(text) > 10 else 1.0
            thickness = 2
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
            
            # Center text position
            text_x = rect["x"] + (rect["w"] - text_size[0]) // 2
            text_y = rect["y"] + (rect["h"] + text_size[1]) // 2
            
            # Add text shadow for depth
            cv2.putText(img, text, 
                        (text_x + 2, text_y + 2), 
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, 
                        (0, 100, 0), thickness)  # Shadow
            
            # Main text
            cv2.putText(img, text, 
                        (text_x, text_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, 
                        (255, 255, 255), thickness)  # White text
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                self.mp_draw.draw_landmarks(img, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # Get finger coordinates
                index_finger_tip = hand_landmarks.landmark[8]
                thumb_tip = hand_landmarks.landmark[4]
                
                h, w, c = img.shape
                index_x = int(index_finger_tip.x * w)
                index_y = int(index_finger_tip.y * h)
                thumb_x = int(thumb_tip.x * w)
                thumb_y = int(thumb_tip.y * h)
                
                pointer_pos = (index_x, index_y)  # Store pointer position
                
                # Draw stylized pointer
                cv2.circle(img, (index_x, index_y), 12, (0, 255, 0), 2)  # Outer circle
                cv2.circle(img, (index_x, index_y), 4, (0, 255, 0), cv2.FILLED)  # Inner dot
                
                distance = np.sqrt((thumb_x - index_x)**2 + (thumb_y - index_y)**2)
                is_clicking = distance > self.MIN_DISTANCE
                
                # Check for hover/click on rectangles
                for rect in self.rectangles:
                    if (rect["x"] < index_x < rect["x"] + rect["w"]) and \
                       (rect["y"] < index_y < rect["y"] + rect["h"]):
                        # Add hover effect
                        cv2.rectangle(img, 
                                    (rect["x"]-2, rect["y"]-2), 
                                    (rect["x"] + rect["w"]+2, rect["y"] + rect["h"]+2), 
                                    (0, 255, 0), 2)  # Glow effect
                        
                        if is_clicking and not self.clicked:
                            self.selected_mode = rect["name"]
                            self.clicked = True
                        elif not is_clicking:
                            self.clicked = False
        
        cv2.putText(img, "Spread fingers to select!", (10, 460),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if return_position:
            return img, pointer_pos
        return img, self.selected_mode 