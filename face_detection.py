import cv2
import numpy as np
import customtkinter as ctk
import PIL.Image
import PIL.ImageTk
import os
from ultralytics import YOLO
from datetime import datetime

class AdvancedDetectionSystem:
    def __init__(self):
        # Set theme and color scheme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Initialize main window
        self.window = ctk.CTk()
        self.window.title("Advanced Detection System")
        self.window.geometry("1200x800")

        # Initialize detection models
        self.yolo_model = self.load_yolo_model()
        self.yolo_model.conf = 0.25  # Lower confidence threshold for better performance
        self.yolo_model.iou = 0.45  # Adjust IOU threshold

        # Initialize variables
        self.camera_active = False
        self.current_frame = None
        self.face_detection_active = True
        self.object_detection_active = True
        self.last_time = datetime.now()
        self.frame_count = 0
        
        # Create UI
        self.create_ui()

        # Update status with loaded model information
        self.update_status(f"YOLO model loaded with {len(self.yolo_model.names)} classes")

    def load_yolo_model(self):
        model_name = 'yolov8n.pt'
        try:
            # Attempt to load the model, which will download it if not present
            model = YOLO(model_name)
            print(f"YOLOv11 model loaded successfully: {model_name}")
        except Exception as e:
            print(f"Error loading YOLOv11 model: {e}")
            print("Falling back to YOLOv8n model")
            model = YOLO('yolov8n.pt')
        return model

    def create_ui(self):
        # Create main container
        self.main_container = ctk.CTkFrame(self.window)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Create left panel for controls
        self.left_panel = ctk.CTkFrame(self.main_container, width=250)
        self.left_panel.pack(side="left", fill="y", padx=5, pady=5)

        # Create title in left panel
        ctk.CTkLabel(
            self.left_panel, 
            text="Advanced Detection Controls",
            font=("Helvetica", 18, "bold")
        ).pack(pady=15)

        # Create control buttons
        self.create_control_buttons()

        # Create detection toggles
        self.create_detection_toggles()

        # Create statistics section
        self.create_statistics_section()

        # Create right panel for display
        self.right_panel = ctk.CTkFrame(self.main_container)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # Create display area
        self.display = ctk.CTkLabel(self.right_panel, text="")
        self.display.pack(padx=10, pady=10, fill="both", expand=True)

        # Create status bar
        self.status_bar = ctk.CTkLabel(
            self.window,
            text="Status: Ready",
            font=("Helvetica", 12)
        )
        self.status_bar.pack(side="bottom", fill="x", padx=10, pady=5)

    def create_control_buttons(self):
        # Button container
        button_frame = ctk.CTkFrame(self.left_panel)
        button_frame.pack(fill="x", padx=10, pady=10)

        # Camera button
        self.camera_button = ctk.CTkButton(
            button_frame,
            text="Start Camera",
            command=self.toggle_camera,
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        self.camera_button.pack(pady=5, fill="x")

        # Load Image button
        self.load_button = ctk.CTkButton(
            button_frame,
            text="Load Image",
            command=self.load_image,
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.load_button.pack(pady=5, fill="x")

        # Video Upload button
        self.video_upload_button = ctk.CTkButton(
            button_frame,
            text="Upload Video",
            command=self.upload_video,
            fg_color="#9C27B0",
            hover_color="#7B1FA2"
        )
        self.video_upload_button.pack(pady=5, fill="x")

        # Screenshot button
        self.screenshot_button = ctk.CTkButton(
            button_frame,
            text="Save Screenshot",
            command=self.save_screenshot,
            fg_color="#FF9800",
            hover_color="#F57C00"
        )
        self.screenshot_button.pack(pady=5, fill="x")

    def create_detection_toggles(self):
        # Toggle container
        toggle_frame = ctk.CTkFrame(self.left_panel)
        toggle_frame.pack(fill="x", padx=10, pady=10)

        # Face Detection toggle
        ctk.CTkLabel(toggle_frame, text="Person Detection", font=("Helvetica", 14)).pack()
        self.face_toggle = ctk.CTkSwitch(
            toggle_frame,
            text="",
            command=self.toggle_face_detection,
            onvalue=True,
            offvalue=False,
            progress_color="#4CAF50"
        )
        self.face_toggle.pack(pady=5)
        self.face_toggle.select()  # Enable by default

        # Object Detection toggle
        ctk.CTkLabel(toggle_frame, text="Object Detection", font=("Helvetica", 14)).pack()
        self.object_toggle = ctk.CTkSwitch(
            toggle_frame,
            text="",
            command=self.toggle_object_detection,
            onvalue=True,
            offvalue=False,
            progress_color="#2196F3"
        )
        self.object_toggle.pack(pady=5)
        self.object_toggle.select()  # Enable by default

    def create_statistics_section(self):
        # Stats container
        stats_frame = ctk.CTkFrame(self.left_panel)
        stats_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            stats_frame,
            text="Detection Statistics",
            font=("Helvetica", 16, "bold")
        ).pack(pady=5)

        # Face count
        self.face_count_label = ctk.CTkLabel(stats_frame, text="Persons Detected: 0", font=("Helvetica", 14))
        self.face_count_label.pack(pady=2)

        # Object count
        self.object_count_label = ctk.CTkLabel(stats_frame, text="Objects Detected: 0", font=("Helvetica", 14))
        self.object_count_label.pack(pady=2)

        # FPS counter
        self.fps_label = ctk.CTkLabel(stats_frame, text="FPS: 0", font=("Helvetica", 14))
        self.fps_label.pack(pady=2)

    def process_frame(self, frame):
        detected_faces = 0
        detected_objects = 0
        
        if self.face_detection_active or self.object_detection_active:
            # Object detection using YOLO (including persons)
            results = self.yolo_model(frame, stream=True)  # Enable streaming mode for better performance
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    # Get class name and confidence
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    name = result.names[cls]
                    
                    if name == 'person' and self.face_detection_active:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f'Person {conf:.2f}', (x1, y1-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        detected_faces += 1
                    elif self.object_detection_active:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                        cv2.putText(frame, f'{name} {conf:.2f}', (x1, y1-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                        detected_objects += 1

        # Update statistics
        self.face_count_label.configure(text=f"Persons Detected: {detected_faces}")
        self.object_count_label.configure(text=f"Objects Detected: {detected_objects}")
        
        # Calculate and update FPS
        self.frame_count += 1
        current_time = datetime.now()
        time_diff = (current_time - self.last_time).total_seconds()
        if time_diff >= 1.0:
            fps = self.frame_count / time_diff
            self.fps_label.configure(text=f"FPS: {fps:.2f}")
            self.frame_count = 0
            self.last_time = current_time
        
        return frame

    def toggle_camera(self):
        if not self.camera_active:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.show_error("Could not open camera")
                return
            self.camera_active = True
            self.camera_button.configure(text="Stop Camera", fg_color="#F44336", hover_color="#D32F2F")
            self.update_camera()
            self.update_status("Camera Active")
        else:
            self.camera_active = False
            self.cap.release()
            self.camera_button.configure(text="Start Camera", fg_color="#4CAF50", hover_color="#45a049")
            self.update_status("Camera Stopped")

    def update_camera(self):
        if self.camera_active:
            ret, frame = self.cap.read()
            if ret:
                # Resize frame for better performance
                frame = cv2.resize(frame, (640, 480))
                
                # Process frame
                processed_frame = self.process_frame(frame)
                
                # Convert to PhotoImage
                image = PIL.Image.fromarray(cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB))
                photo = PIL.ImageTk.PhotoImage(image)
                
                # Update display
                self.display.configure(image=photo)
                self.current_frame = photo
                
                # Schedule next update
                self.window.after(40, self.update_camera)

    def toggle_face_detection(self):
        self.face_detection_active = self.face_toggle.get()
        status = "enabled" if self.face_detection_active else "disabled"
        self.update_status(f"Person detection {status}")

    def toggle_object_detection(self):
        self.object_detection_active = self.object_toggle.get()
        status = "enabled" if self.object_detection_active else "disabled"
        self.update_status(f"Object detection {status}")

    def load_image(self):
        file_path = ctk.filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff")]
        )
        if file_path:
            image = cv2.imread(file_path)
            if image is None:
                self.show_error("Could not load image")
                return
                
            # Resize if too large
            max_size = 800
            height, width = image.shape[:2]
            if height > max_size or width > max_size:
                scale = max_size / max(height, width)
                image = cv2.resize(image, None, fx=scale, fy=scale)
            
            # Process and display image
            processed_image = self.process_frame(image)
            photo = PIL.ImageTk.PhotoImage(
                image=PIL.Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))
            )
            self.display.configure(image=photo)
            self.current_frame = photo
            self.update_status("Image loaded and processed")

    def upload_video(self):
        file_path = ctk.filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")]
        )
        if file_path:
            self.process_video(file_path)

    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.show_error("Could not open video file")
            return

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % 3 != 0:  # Process every 3rd frame for smoother playback
                continue

            # Resize frame for better performance
            frame = cv2.resize(frame, (640, 480))
            
            # Process frame
            processed_frame = self.process_frame(frame)
            
            # Convert to PhotoImage
            image = PIL.Image.fromarray(cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB))
            photo = PIL.ImageTk.PhotoImage(image)
            
            # Update display
            self.display.configure(image=photo)
            self.current_frame = photo
            self.window.update()

            # Add delay for smoother playback (approximately 40ms per frame)
            self.window.after(40)

        cap.release()
        self.update_status("Video processing completed")

    def save_screenshot(self):
        if not hasattr(self, 'current_frame'):
            self.show_error("No image to save")
            return
            
        # Create screenshots directory
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")
        
        # Save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/detection_{timestamp}.png"
        
        image = PIL.ImageTk.getimage(self.current_frame)
        image.save(filename)
        self.update_status(f"Screenshot saved as {filename}")

    def update_status(self, message):
        self.status_bar.configure(text=f"Status: {message}")

    def show_error(self, message):
        ctk.messagebox.showerror("Error", message)

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = AdvancedDetectionSystem()
    app.run()

