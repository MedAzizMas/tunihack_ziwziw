import cv2
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import time

class CameraHandler:
    def __init__(self, pose_processor, pose_analyzer):
        self.cap = cv2.VideoCapture(0)
        self.pose_processor = pose_processor
        self.pose_analyzer = pose_analyzer
        self.value_yoga_choice=0
        
        if not self.cap.isOpened():
            raise IOError("Cannot open webcam")

    def generate_frames(self, arr):
        while True:
            success, frame = self.cap.read()
            if not success:
                break
                
            frame = cv2.flip(frame, 1)
             # Initialize accuracy variables
            right_arm_acc = 0
            left_arm_acc = 0
            right_leg_acc = 0
            left_leg_acc = 0
            total_accuracy = 0
            # Process pose detection
            frame = self.pose_processor.detector.findPose(frame, False)
            lmlist = self.pose_processor.detector.getPosition(frame, False)
            
            if len(lmlist) != 0:
                # Calculate angles
                right_arm_angle = int(self.pose_processor.detector.findAngle(frame, 12, 14, 16))
                left_arm_angle = int(self.pose_processor.detector.findAngle(frame, 11, 13, 15))
                right_leg_angle = int(self.pose_processor.detector.findAngle(frame, 24, 26, 28))
                left_leg_angle = int(self.pose_processor.detector.findAngle(frame, 23, 25, 27))
                
                total_accuracy = self.pose_analyzer.calculate_total_accuracy(
                right_arm_acc, left_arm_acc, right_leg_acc, left_leg_acc)
                
                # Update the global accuracy
                from app import app
                app.current_accuracy = total_accuracy

                # Get individual accuracies
                right_arm_acc = self.pose_analyzer.compare_right_arm(right_arm_angle)
                left_arm_acc = self.pose_analyzer.compare_left_arm(left_arm_angle)
                right_leg_acc = self.pose_analyzer.compare_right_leg(right_leg_angle)
                left_leg_acc = self.pose_analyzer.compare_left_leg(left_leg_angle)
                
                # Calculate total accuracy
                total_accuracy = self.pose_analyzer.calculate_total_accuracy(
                    right_arm_acc, left_arm_acc, right_leg_acc, left_leg_acc
                )
                
                # Create semi-transparent overlay for accuracy
                overlay = frame.copy()
                # Draw a black rectangle for the accuracy display
                cv2.rectangle(overlay, (10, 10), (200, 100), (0, 0, 0), -1)
                # Add the overlay with transparency
                cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
                
                # Draw accuracy text
                cv2.putText(frame, f'Total Accuracy:', (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(frame, f'{total_accuracy:.1f}%', (20, 80), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
                
                # Draw individual accuracies if needed
                y_position = 120
                metrics = [
                    ("Right Arm", right_arm_acc),
                    ("Left Arm", left_arm_acc),
                    ("Right Leg", right_leg_acc),
                    ("Left Leg", left_leg_acc)
                ]
                
                for label, value in metrics:
                    cv2.putText(frame, f'{label}: {value:.1f}%', 
                            (20, y_position), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    y_position += 25
            
            # Convert frame to jpg
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def __del__(self):
        self.cap.release()