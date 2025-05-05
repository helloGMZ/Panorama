import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time  # Import time module to measure processing time

# Additional Feature 1: 
# Histogram matching function: color correction
def match_histograms(source, template):
    # Convert the source and template images to HSV color space
    source_hsv = cv2.cvtColor(source, cv2.COLOR_BGR2HSV)
    template_hsv = cv2.cvtColor(template, cv2.COLOR_BGR2HSV)
    
    # Split the HSV channels (Hue, Saturation, Value)
    source_h, source_s, source_v = cv2.split(source_hsv)
    template_h, template_s, template_v = cv2.split(template_hsv)
    
    # Perform histogram equalization on the 'Value' (brightness) channel
    source_v_matched = cv2.equalizeHist(source_v)
    template_v_matched = cv2.equalizeHist(template_v)
    
    # Merge the modified channels back
    matched_hsv = cv2.merge([source_h, source_s, source_v_matched])
    
    # Convert back to BGR color space
    matched_image = cv2.cvtColor(matched_hsv, cv2.COLOR_HSV2BGR)
    return matched_image

# Read video and extract frames at intervals
def extract_frames(video_path, num_frames):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames = []
    
    # Extract every 5th frame from the video
    for i in range(0, total_frames, 5):  
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
    cap.release()
    return frames

# Use cv2.Stitcher for stitching frames into a panorama
def generate_panorama(video_path, max_frames, progress_callback, display_callback):
    frames = extract_frames(video_path, num_frames=max_frames)
    
    if len(frames) < 2:
        print("Not enough video frames to generate panorama!")
        return None
    
    print("Starting image stitching...")
    
    stitcher = cv2.Stitcher_create()
    status, panorama = stitcher.stitch(frames)
    
    if status == cv2.Stitcher_OK:
        # If stitching is successful, apply color correction
        panorama = match_histograms(panorama, frames[0])  # Use the first frame as a template for color correction
        
        # Save the result to a file
        cv2.imwrite("panorama_result.jpg", panorama)
        print("Panorama saved as panorama_result.jpg")
        
        # Display the result in the UI
        display_callback(panorama)
        return panorama
    else:
        print(f"Stitching failed, error code: {status}")
        return None

# Additional Feature 2:
# UI function to create the interface and various buttons to interact with users
def create_ui():
    root = tk.Tk()
    root.title("Panorama Generator")
    root.geometry("800x600")

    # Instructions label
    label = tk.Label(root, text="Please select a video file to generate a panorama", font=("Arial", 14))
    label.pack(pady=10)

    # Function to open a file dialog to select a video file
    def browse_video():
        file_path = filedialog.askopenfilename(filetypes=[("MP4 Files", "*.mp4"), ("All Files", "*.*")])
        if file_path:
            entry_video_path.delete(0, tk.END)
            entry_video_path.insert(0, file_path)

    entry_video_path = tk.Entry(root, width=50)
    entry_video_path.pack(pady=10)

    btn_browse = tk.Button(root, text="Select Video", command=browse_video)
    btn_browse.pack(pady=10)

    progress_label = tk.Label(root, text="Please select a video and click generate", font=("Arial", 12))
    progress_label.pack(pady=10)

    frame_buttons = tk.Frame(root)
    frame_buttons.pack(pady=10)

    # Save button, initially hidden
    btn_save = tk.Button(frame_buttons, text="Save Panorama")
    btn_save.pack(side=tk.LEFT, padx=10)
    btn_save.pack_forget()  # Initially hidden until panorama is generated

    label_result = tk.Label(root, width=800, height=400)
    label_result.pack(pady=20)

    # Update progress text while generating the panorama
    def update_progress_text(current, total):
        progress_label.config(text=f"Generating: {int((current / total) * 100)}%")
        root.update_idletasks()

    # Function to display the generated panorama image in the UI
    def display_panorama(image):
        label_width = label_result.winfo_width()
        label_height = label_result.winfo_height()
        image_resized = cv2.resize(image, (label_width, label_height), interpolation=cv2.INTER_LINEAR)
        image_resized = cv2.cvtColor(image_resized, cv2.COLOR_BGR2RGB)  # Convert from BGR to RGB for displaying
        pil_image = Image.fromarray(image_resized)
        tk_image = ImageTk.PhotoImage(pil_image)
        label_result.config(image=tk_image)
        label_result.image = tk_image

    # Additional Feature 3: Preview of panorama and efficiency calculation of the program
    # UI function to trigger panorama generation
    def generate_panorama_ui():
        video_path = entry_video_path.get()
        if not video_path:
            messagebox.showerror("Error", "Please select a video file first!")
            return

        progress_label.config(text="Generating, please wait...")
        root.update_idletasks()

        def process_panorama():
            # Get video duration
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)  # Frames per second
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_duration = total_frames / fps  # Duration in seconds
            cap.release()

            # Print the video duration
            print(f"Video duration: {video_duration:.2f} seconds")

            # Start processing and measure the time it takes
            start_time = time.time()
            
            # Clear any previously displayed image before generating a new one
            label_result.config(image=None)
            label_result.image = None

            panorama = generate_panorama(video_path, max_frames=20, 
                                        progress_callback=update_progress_text,
                                        display_callback=display_panorama)

            # Measure processing time
            end_time = time.time()
            processing_time = end_time - start_time

            print(f"Processing time: {processing_time:.2f} seconds")

            if panorama is not None:
                display_panorama(panorama)
                progress_label.config(text="Generated")
                
                # Show the save button once the panorama is generated
                btn_save.pack(side=tk.LEFT, padx=10)

                # Function to save the generated panorama image
                def save_image():
                    cv2.imwrite("panorama_result.jpg", panorama)
                    messagebox.showinfo("Save Successful", "Panorama has been saved!")

                btn_save.config(command=save_image)
            else:
                progress_label.config(text="Generation failed, please try again")

        #Additional Feature 4: Multi-threading to ensure synchronization between program running and prompts diplay
        threading.Thread(target=process_panorama, daemon=True).start()

    # Generate button to trigger panorama generation
    btn_generate = tk.Button(frame_buttons, text="Generate Panorama", command=generate_panorama_ui)
    btn_generate.pack(side=tk.LEFT, padx=10)

    root.mainloop()

# main
create_ui()
