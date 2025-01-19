import cv2
import mediapipe as mp
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import trimesh

class STLFile:
    def __init__(self, filename):
        # Load the STL file using trimesh
        self.mesh = trimesh.load(filename)
        self.prepare_mesh()
        
    def prepare_mesh(self):
        """Extract mesh data"""
        # Get vertices and faces
        self.vertices = np.array(self.mesh.vertices, dtype=np.float32)
        self.faces = np.array(self.mesh.faces, dtype=np.int32)
        
        # Get or generate normals
        if self.mesh.vertex_normals is not None:
            self.normals = np.array(self.mesh.vertex_normals, dtype=np.float32)
        else:
            self.normals = self.mesh.face_normals
            
        # Scale model to reasonable size
        self.scale_to_fit()
        
    def scale_to_fit(self):
        """Scale the mesh to fit in view"""
        max_size = np.max(np.abs(self.vertices))
        if max_size > 0:
            scale_factor = 0.5 / max_size
            self.vertices *= scale_factor

class FingerController3D:
    def __init__(self, model_path):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            max_num_hands=1
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Load the 3D model
        self.model = STLFile(model_path)
        
        # Initial position and rotation
        self.position = [0.0, 0.0, -2.0]
        self.rotation = [0.0, 0.0, 0.0]
        self.scale = 0.2
        
        # Gesture states
        self.last_palm_pos = None
        self.mode = 'none'
        
        # Smoothing parameters
        self.smoothing_factor = 0.15
        self.target_position = self.position.copy()
        self.target_rotation = self.rotation.copy()
        self.target_scale = self.scale
        
        # Initialize OpenGL
        self.init_gl()
    
    def init_gl(self):
        pygame.init()
        pygame.display.set_mode((self.frame_width, self.frame_height), DOUBLEBUF | OPENGL | HIDDEN)
        
        # Enable features
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_NORMALIZE)
        
        # Set up lighting
        glLightfv(GL_LIGHT0, GL_POSITION, [0, 0, 1, 0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
        
        # Set up the camera
        glViewport(0, 0, self.frame_width, self.frame_height)
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, (self.frame_width/self.frame_height), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
    
    def draw_model(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Apply transformations
        glTranslatef(*self.position)
        glRotatef(self.rotation[0], 1, 0, 0)
        glRotatef(self.rotation[1], 0, 1, 0)
        glRotatef(self.rotation[2], 0, 0, 1)
        glScalef(self.scale, self.scale, self.scale)
        
        # Draw the model
        glColor3f(1.0, 0.0, 0.0)  # Red color for visibility
        glBegin(GL_TRIANGLES)
        for face in self.model.faces:
            for vertex_id in face:
                if self.model.normals is not None:
                    glNormal3fv(self.model.normals[vertex_id])
                glVertex3fv(self.model.vertices[vertex_id])
        glEnd()
        
        # Read the OpenGL buffer
        glPixels = glReadPixels(0, 0, self.frame_width, self.frame_height, GL_RGBA, GL_UNSIGNED_BYTE)
        gl_surface = np.frombuffer(glPixels, dtype=np.uint8)
        gl_surface = gl_surface.reshape((self.frame_height, self.frame_width, 4))
        gl_surface = cv2.flip(gl_surface, 0)
        return gl_surface
    
    def lerp(self, start, end, factor):
        """Linear interpolation for smooth transitions"""
        return start + (end - start) * factor
    
    def calculate_hand_gesture(self, hand_landmarks):
        """Simplified gesture detection using number of fingers up"""
        fingers_up = []
        for tip_id in [8, 12, 16, 20]:  # Index, Middle, Ring, Pinky
            if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[tip_id - 2].y:
                fingers_up.append(1)
            else:
                fingers_up.append(0)
        
        num_fingers = sum(fingers_up)
        
        if num_fingers == 1 and fingers_up[0] == 1:  # Only index finger
            return 'move'
        elif num_fingers == 2 and fingers_up[0] == 1 and fingers_up[1] == 1:  # Index + middle
            return 'rotate'
        elif num_fingers >= 4:  # All fingers
            return 'scale'
        
        return 'none'
    
    def process_hand_landmarks(self, hand_landmarks):
        current_mode = self.calculate_hand_gesture(hand_landmarks)
        
        palm_pos = np.array([hand_landmarks.landmark[0].x, hand_landmarks.landmark[0].y])
        
        if self.last_palm_pos is not None:
            if current_mode == 'move':
                delta = palm_pos - self.last_palm_pos
                self.target_position[0] += delta[0] * 3
                self.target_position[1] -= delta[1] * 3
            elif current_mode == 'rotate':
                delta = palm_pos - self.last_palm_pos
                self.target_rotation[1] += delta[0] * 100
                self.target_rotation[0] += delta[1] * 100
            elif current_mode == 'scale':
                scale_delta = (palm_pos[1] - self.last_palm_pos[1]) * 2
                self.target_scale = max(0.1, min(2.0, self.target_scale - scale_delta))
        
        # Apply smoothing
        for i in range(3):
            self.position[i] = self.lerp(self.position[i], self.target_position[i], self.smoothing_factor)
            self.rotation[i] = self.lerp(self.rotation[i], self.target_rotation[i], self.smoothing_factor)
        self.scale = self.lerp(self.scale, self.target_scale, self.smoothing_factor)
        
        self.last_palm_pos = palm_pos
        self.mode = current_mode
        
    def run(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS
                    )
                    self.process_hand_landmarks(hand_landmarks)
                    
                    instructions = {
                        'move': 'Index finger only',
                        'rotate': 'Index + Middle fingers',
                        'scale': 'All fingers',
                        'none': 'No gesture'
                    }
                    cv2.putText(frame, f"Mode: {self.mode} ({instructions[self.mode]})", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                self.last_palm_pos = None
                self.mode = 'none'
                cv2.putText(frame, "Show hand to control", (10, 30), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Render the 3D model
            gl_surface = self.draw_model()
            mask = gl_surface[:, :, 3] > 0
            frame[mask] = gl_surface[mask][:, :3]
            
            cv2.imshow('AR View', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cap.release()
        cv2.destroyAllWindows()
        pygame.quit()

def main():
    model_path = "GingerPerson.stl"  # Change to your .stl file path
    try:
        print(f"Loading model from: {model_path}")
        controller = FingerController3D(model_path)
        controller.run()
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Make sure you have a valid .stl file in the correct path")

if __name__ == "__main__":
    main() 