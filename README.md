# ARCoach

## 1. Project Overview

### Description
ARCoach is a cutting-edge educational tool that enhances learning and teaching experiences through Augmented Reality (AR) technology and computer vision. Designed to assist teachers in managing large classrooms, it streamlines student engagement and provides actionable insights. For students, ARCoach offers an interactive and adaptive platform to develop skills effectively, making learning more engaging and personalized. The application also features a user-friendly statistics section, enabling deeper insight into athletic performances.

This project was inspired by the challenges of overcrowded classrooms and the lack of individualized attention in traditional education. By leveraging AR technology, ARCoach aims to transform education, empowering teachers with smarter tools and enabling students to thrive in an immersive and skill-focused learning environment.

---

## 2. Features

- **Real-Life Coaching Sessions**
  Engage in interactive sessions for activities like push-ups and squats. A computer vision system ensures correct form and tracks repetitions accurately.

- **3D Model Viewer with Gesture-Based Interaction**
  Interact with a 3D model viewer using camera-detected gestures, eliminating the need for traditional input devices.

- **Yoga Pose Practice and Tutorials**
  Learn and refine yoga poses with detailed tutorials and accuracy breakdowns for improved technique.

- **Statistics Breakdown for Decision Making**
  Access comprehensive statistics for both students and teachers to guide learning strategies and classroom management.

---

## 3. Technology Stack

### Frontend
- **HTML/CSS**: For creating a simple and responsive user interface.
- **Camera-Based Interaction**: Gesture-based system for interacting with the application.

### Backend
- **Flask**: Manages server-side functionality, rendering templates, and API routes.

### Database
- **N/A**: Currently, live data processing and in-memory computation are used.

### Core Tools and Libraries
- **OpenCV**: Real-time camera feed processing and computer vision tasks.
- **TensorFlow & TensorFlow Hub**: Implements and runs ML models for pose detection and analysis.
- **Matplotlib**: Visualizes statistics and analytical data.
- **Threading & Queue**: Enables asynchronous processing for efficient performance.

### Custom Modules and Scripts
- **PoseProcessor & PoseAnalyzer**: Process and analyze user poses in real-time.
- **CameraHandler**: Manages live camera feeds.
- **PushUpCounter & SquatAnalyser**: Specialized for activity-specific form verification and repetition counting.
- **HandPointerDetector**: Enables gesture-based interaction with the 3D menu system.
- **PoseModule & PoseModule_menu**: Core modules for pose detection and gesture-based interaction.

### Other Tools
- **NumPy**: For numerical computations and array manipulations.
- **Time**: Tracks and manages time-based processes within the application.

---

## 4. Installation and Usage



### Installation Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/MedAzizMas/tunihack_ziwziw.git
   ```

2. Navigate to the project directory:
   ```bash
   cd tunihack_ziwziw
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

4. Activate the virtual environment:
   - **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

6. Run the application:
   ```bash
   python app.py
   ```

7. Deactivate the virtual environment when done:
   ```bash
   deactivate
   ```

---

## 5. Usage Instructions

### Step 1: Access the Application
- Open your web browser and navigate to:
  ```
  http://localhost:5000
  ```

### Step 2: Interact with the Features
- **Main Functionality**: Use features like form verification, repetition counting, and statistics analysis.
- **Navigation**: Access different sections via the intuitive interface.

### Step 3: Troubleshooting
- Check the console for error messages if issues arise.
- Ensure all configuration files and dependencies are properly set up.

---

## 6. Demo

- **Live Demo**: https://drive.google.com/file/d/1gyLBnlOzma6vv3NVdB8nexKuUgT7jXGh/view?usp=sharing
- **Screenshots**:
- 
![2025-01-19 11-30-45 00_01_12_22 Still004](https://github.com/user-attachments/assets/de3382f7-5cf1-4fc6-9c09-d51bb09bad1a)
---![2025-01-19 11-30-45 00_00_22_35 Still002](https://github.com/user-attachments/assets/ea59d8f4-9554-4f49-9eb3-0e86c656ead7)
![2025-01-19 11-30-45 00_01_41_37 Still003](https://github.com/user-attachments/assets/e4667c79-84db-441a-894c-6d6e198c6c97)
![2025-01-19 11-30-45 00_00_49_47 Still007](https://github.com/user-attachments/assets/4f38365b-0a15-45c5-ab22-74c5dec35657)


## 7. Team Members

- **Name 1**: Mohamed aziz masmoudi
- **Name 2**: Nour chokri
- **Name 3**: Hazem mbarek
- **Name 4**: Abdessattar ben hsan

---

## 8. Challenges Faced

1. **Dependency Conflicts**
   - **Challenge**: Version conflicts caused issues during setup.
   - **Solution**: Locked dependencies in `requirements.txt` and used virtual environments.

2. **Environment Configuration Issues**
   - **Challenge**: Difficulties in configuring the environment correctly.
   - **Solution**: Documented the setup process and created automation scripts.

3. **UI/UX Design**
   - **Challenge**: Initial designs were cluttered.
   - **Solution**: Iterated on feedback and focused on simplicity and usability.

---

## 9. Future Improvements

- **Hand Motion System for Teachers**: Enable hands-free access to student data using gestures.
- **Integration with Mobile and AR Glasses**: Expand functionality to mobile devices and AR wearables.
- **Hologram Technology for Wearables**: Introduce interactive holograms for real-time feedback.
- **Data Collection and Analytics**: Generate detailed, personalized insights for students and teachers.
- **Real-Time Feedback via Camera Feeds**: Pair camera and sensor data for enhanced analysis.
- **Expansion into New Markets**: Target small clubs, schools, and educational institutions.
- **Incorporate Audio/Visual Feedback**: Enhance interactivity with real-time cues.

---

## 10. License

This project is licensed under the MIT License.

```
Copyright (c) [Year] [Your Name/Team Name]

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is provided to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

---

## 11. Acknowledgments

- **Mentors and Advisors**: For their invaluable guidance and feedback.
- **Hackathon Organizers**: For providing the platform to develop and showcase the project.
- **Team Members**: For their dedication and collaboration.
- **Libraries and Tools**: Special thanks to the developers of TensorFlow, OpenCV, Flask, and other tools.
- **Community Resources**: Gratitude to online communities and contributors for tutorials and support.


