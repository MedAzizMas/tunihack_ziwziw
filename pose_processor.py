import numpy as np
import cv2
import tensorflow as tf
import tensorflow_hub as hub
import PoseModule as pm

class PoseProcessor:
    def __init__(self):
        self.model = hub.load("https://tfhub.dev/google/movenet/multipose/lightning/1")
        self.movenet = self.model.signatures['serving_default']
        self.detector = pm.PoseDetector()
        
    def draw_keypoints(self, frame, keypoints, confidence_threshold):
        y, x, c = frame.shape
        shaped = np.squeeze(np.multiply(keypoints, [y,x,1]))
        
        for kp in shaped:
            ky, kx, kp_conf = kp
            if kp_conf > confidence_threshold:
                cv2.circle(frame, (int(kx), int(ky)), 4, (0,255,0), -1)

    EDGES = {
        (0, 1): 'm', (0, 2): 'c', (1, 3): 'm', (2, 4): 'c',
        (0, 5): 'm', (0, 6): 'c', (5, 7): 'm', (7, 9): 'm',
        (6, 8): 'c', (8, 10): 'c', (5, 6): 'y', (5, 11): 'm',
        (6, 12): 'c', (11, 12): 'y', (11, 13): 'm', (13, 15): 'm',
        (12, 14): 'c', (14, 16): 'c'
    }

    def draw_connections(self, frame, keypoints, edges, confidence_threshold):
        y, x, c = frame.shape
        shaped = np.squeeze(np.multiply(keypoints, [y,x,1]))
        
        for edge, color in edges.items():
            p1, p2 = edge
            y1, x1, c1 = shaped[p1]
            y2, x2, c2 = shaped[p2]
            
            if (c1 > confidence_threshold) & (c2 > confidence_threshold):      
                cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0,0,255), 2)

    def loop_through_people(self, frame, keypoints_with_scores, confidence_threshold):
        for person in keypoints_with_scores:
            self.draw_connections(frame, person, self.EDGES, confidence_threshold)
            self.draw_keypoints(frame, person, confidence_threshold)