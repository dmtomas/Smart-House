import cv2
import numpy as np
import time
from datetime import datetime
import os

# Configuration
STREAM_URL = "rtsp://192.168.1.143:8554/mystream"
# MediaMTX converts WebRTC to RTSP automatically on port 8554

MAX_IMAGES = 10  # Maximum number of images to keep in list
CAPTURE_INTERVAL = 1.0  # Seconds between captures

# Alert file for website notifications
ALERT_FILE = "/var/www/html/motion_alert.txt"

# Initialize video capture using FFmpeg
print(f"Connecting to stream: {STREAM_URL}")

# Use FFmpeg environment variable for better RTSP support
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|timeout;5000000"

cap = cv2.VideoCapture(STREAM_URL, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("ERROR: Cannot open video stream")
    print("Make sure:")
    print("  1. Stream is active (check in VLC)")
    print("  2. FFmpeg is installed: sudo apt install ffmpeg")
    print("  3. URL is correct:", STREAM_URL)
    exit(1)

print("Stream opened successfully!")
print(f"Capturing {MAX_IMAGES} images with {CAPTURE_INTERVAL}s interval")
print("Images will be stored in RAM only (no disk writes)\n")

# List to store images in RAM
images = []

last_capture_time = time.time()
frame_count = 0

while True:
    # Read frame from stream
    ret, frame = cap.read()

    if not ret or frame is None or frame.size == 0:
        print("Warning: Cannot read frame or corrupted frame. Reconnecting...")
        time.sleep(2)
        cap.release()
        cap = cv2.VideoCapture(STREAM_URL, cv2.CAP_FFMPEG)
        continue

    current_time = time.time()

    # Capture frame at intervals
    if current_time - last_capture_time >= CAPTURE_INTERVAL:
        # Convert to grayscale (black and white) for efficiency
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Add grayscale frame to list
        images.append(gray_frame.copy())  # .copy() to ensure independent copy
        frame_count += 1

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Captured image {frame_count} | List size: {len(images)}")

        # Keep only last MAX_IMAGES frames
        if len(images) > MAX_IMAGES:
            images.pop(0)  # Remove oldest image
            print(f"  → Removed oldest image (keeping last {MAX_IMAGES})")

        # MOTION DETECTION - Robust localized movement detection
        if len(images) >= 2:
            # Get last two frames
            previous_frame = images[-2]
            current_frame = images[-1]

            # Apply stronger Gaussian blur to reduce camera noise
            prev_blur = cv2.GaussianBlur(previous_frame, (21, 21), 0)
            curr_blur = cv2.GaussianBlur(current_frame, (21, 21), 0)

            # Calculate absolute difference
            diff = cv2.absdiff(prev_blur, curr_blur)

            # Use higher threshold to ignore subtle changes
            threshold_value = 50  # Increased from 30 (higher = less sensitive)
            _, thresh = cv2.threshold(diff, threshold_value, 255, cv2.THRESH_BINARY)

            # Aggressive noise reduction
            # Erosion removes small specks
            kernel_erode = np.ones((5,5), np.uint8)  # Larger kernel
            thresh = cv2.erode(thresh, kernel_erode, iterations=2)  # More iterations

            # Dilation connects nearby regions
            kernel_dilate = np.ones((7,7), np.uint8)
            thresh = cv2.dilate(thresh, kernel_dilate, iterations=2)

            # Find contours (connected regions of motion)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Much stricter filtering
            MIN_CONTOUR_AREA = 2000  # Increased from 500 - ignore small objects
            MAX_CONTOUR_AREA = 50000  # Ignore if object is too large (likely noise/lighting)
            MIN_ASPECT_RATIO = 0.3  # Width/height ratio (filters out thin lines)
            MAX_ASPECT_RATIO = 3.0  # Filters out very wide/tall shapes

            significant_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)

                if area < MIN_CONTOUR_AREA or area > MAX_CONTOUR_AREA:
                    continue

                # Check aspect ratio (real objects have reasonable proportions)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h if h > 0 else 0

                if aspect_ratio < MIN_ASPECT_RATIO or aspect_ratio > MAX_ASPECT_RATIO:
                    continue

                # Check if contour is solid enough (not just edges)
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    if circularity < 0.1:  # Too irregular = noise
                        continue

                significant_contours.append(contour)

            # Calculate total motion area
            total_motion_area = sum(cv2.contourArea(c) for c in significant_contours)

            # Strict motion detection
            motion_detected = False

            # Require:
            # 1. At least 1 significant object
            # 2. Not too many objects (camera shake)
            # 3. Substantial total area
            # 4. Objects not too close to edges (often false positives)

            if 1 <= len(significant_contours) <= 5:  # Between 1-5 objects
                if total_motion_area > 3000:  # Substantial area

                    # Check if objects are in central area (not edges)
                    height, width = current_frame.shape
                    edge_margin = 30  # pixels from edge

                    valid_objects = []
                    for contour in significant_contours:
                        x, y, w, h = cv2.boundingRect(contour)
                        # Check if not too close to edges
                        if (x > edge_margin and
                            y > edge_margin and
                            x + w < width - edge_margin and
                            y + h < height - edge_margin):
                            valid_objects.append((x, y, w, h))

                    if len(valid_objects) > 0:
                        motion_detected = True

                        print(f"  🚨 MOTION! {len(valid_objects)} object(s) detected")
                        print(f"     Total area: {total_motion_area} pixels")
                        for i, (x, y, w, h) in enumerate(valid_objects[:3]):
                            print(f"     Object {i+1}: position ({x},{y}), size {w}x{h}")

                        try:
                            with open(ALERT_FILE, "w") as f:
                                f.write(f"{time.time()}\n")
                                print(f"     ✓ Alert written to {ALERT_FILE}")
                        except Exception as e:
                            print(f"     ⚠️  Warning: Could not write alert file: {e}")
                        # YOUR CUSTOM ACTIONS HERE:
                        # - Save frame: cv2.imwrite(f"/tmp/motion_{timestamp}.jpg", current_frame)
                        # - Send notification via API
                        # - Trigger external alarm
                        # - Run AI analysis
                        # - etc.
                    else:
                        print(f"  ⚠️  Edge motion ignored ({len(significant_contours)} objects)")
            else:
                if len(significant_contours) > 5:
                    print(f"  ⚠️  Too many objects ({len(significant_contours)}) - likely noise")
                else:
                    print(f"  ✓ No motion")

        last_capture_time = current_time

    # Small delay to reduce CPU usage
    time.sleep(0.01)

# Cleanup (this won't run unless you Ctrl+C, but good practice)
cap.release()
print("\nCapture stopped.")
print(f"Final list contains {len(images)} images")
