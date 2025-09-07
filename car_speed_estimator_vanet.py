# -*- coding: utf-8 -*-
"""Car Speed Estimator with VANET Communication"""

# Import required libraries
import cv2
import pandas as pd
from ultralytics import YOLO
from tracker import*
from vanet_speed_sharing import VANETSpeedSharing
import time
import math
import random

# Initialize YOLO model and video
model = YOLO('yolov8n.pt')
vi = cv2.VideoCapture('highway_mini.mp4')

class_list = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven',
              'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

# Initialize tracker and VANET
tracker = Tracker()
vanet = VANETSpeedSharing()
count = 0

# Speed calculation variables
down = {}
up = {}
counter_down = []
counter_up = []

# Colors for display
text_color = (255, 255, 255)  # white
red_color = (0, 0, 255)       # red
blue_color = (255, 0, 0)      # blue
green_color = (0, 255, 0)     # green
yellow_color = (0, 255, 255)  # yellow
purple_color = (255, 0, 255)  # purple

def draw_communication_lines(frame, vanet_system):
    """Draw lines between communicating vehicles"""
    pairs = vanet_system.get_communication_pairs()
    
    for vid1, vid2 in pairs:
        if vid1 in vanet_system.vehicles and vid2 in vanet_system.vehicles:
            v1 = vanet_system.vehicles[vid1]
            v2 = vanet_system.vehicles[vid2]
            
            # Draw communication line
            cv2.line(frame, (int(v1.x), int(v1.y)), (int(v2.x), int(v2.y)), yellow_color, 1)
            
            # Draw communication indicator (small circle at midpoint)
            mid_x = int((v1.x + v2.x) / 2)
            mid_y = int((v1.y + v2.y) / 2)
            cv2.circle(frame, (mid_x, mid_y), 3, yellow_color, -1)

def draw_speed_sharing_info(frame, vehicle_id, x, y, own_speed, shared_speeds):
    """Draw speed sharing information for each vehicle"""
    # Draw own speed (in green)
    cv2.putText(frame, f"ID:{vehicle_id}", (x, y-40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    cv2.putText(frame, f"My Speed: {int(own_speed)}km/h", (x, y-25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, green_color, 1)
    
    # Draw received speeds from other vehicles
    y_offset = -10
    for other_id, speed_data in shared_speeds.items():
        received_speed = speed_data['speed']
        cv2.putText(frame, f"V{other_id}: {int(received_speed)}km/h", (x, y + y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.3, purple_color, 1)
        y_offset += 15

def draw_vanet_status(frame, vanet_system, current_frame, total_frames, auto_play):
    """Draw VANET system status with frame control info"""
    total_vehicles = len(vanet_system.vehicles)
    communication_pairs = len(vanet_system.get_communication_pairs())
    recent_messages = len(vanet_system.get_recent_messages(2))
    
    # VANET status box (make it larger)
    cv2.rectangle(frame, (750, 10), (1010, 150), (0, 0, 0), -1)  # Black background
    cv2.rectangle(frame, (750, 10), (1010, 150), text_color, 2)   # White border
    
    cv2.putText(frame, "VANET STATUS", (760, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, yellow_color, 2)
    cv2.putText(frame, f"Active Vehicles: {total_vehicles}", (760, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
    cv2.putText(frame, f"Comm. Links: {communication_pairs}", (760, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
    cv2.putText(frame, f"Msgs/2sec: {recent_messages}", (760, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
    cv2.putText(frame, "Yellow lines = Communication", (760, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.3, yellow_color, 1)
    
    # Frame control info
    mode_text = "AUTO" if auto_play else "MANUAL"
    cv2.putText(frame, f"Frame: {current_frame}/{total_frames}", (760, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
    cv2.putText(frame, f"Mode: {mode_text}", (760, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)

print("=== CAR SPEED ESTIMATION WITH VANET - FRAME CONTROL ===")
print("Features:")
print("- Yellow lines show vehicle communication")
print("- Green text shows vehicle's own speed")
print("- Purple text shows received speeds from other vehicles")
print("- VANET status panel in top-right corner")
print("")
print("Controls:")
print("  SPACEBAR - Next frame (frame-by-frame)")
print("  'p' - Toggle Play/Pause (auto-advance)")
print("  'r' - Restart video")
print("  ESC - Exit")
print("==========================================================")

auto_play = False
current_frame = 0
total_frames = int(vi.get(cv2.CAP_PROP_FRAME_COUNT))

while True:
    ret, frame = vi.read()
    if not ret:
        print("End of video reached. Press 'r' to restart or ESC to exit.")
        key = cv2.waitKey(0) & 0xFF
        if key == ord('r'):  # Reset video
            vi.set(cv2.CAP_PROP_POS_FRAMES, 0)
            current_frame = 0
            count = 0
            down.clear()
            up.clear()
            counter_down.clear()
            counter_up.clear()
            vanet = VANETSpeedSharing()  # Reset VANET
            print("Video restarted")
            continue
        elif key == 27:  # ESC
            break
        else:
            continue
            
    count += 1
    current_frame = int(vi.get(cv2.CAP_PROP_POS_FRAMES))
    frame = cv2.resize(frame, (1020, 500))

    # YOLO detection
    results = model.predict(frame)
    a = results[0].boxes.data
    a = a.detach().cpu().numpy()
    px = pd.DataFrame(a).astype("float")
    
    detected_cars = []

    # Extract car detections
    for index, row in px.iterrows():
        x1 = int(row[0])
        y1 = int(row[1])
        x2 = int(row[2])
        y2 = int(row[3])
        d = int(row[5])
        c = class_list[d]
        if 'car' in c:
            detected_cars.append([x1, y1, x2, y2])

    # Update tracker
    bbox_id = tracker.update(detected_cars)
    vehicle_speeds = {}  # Store speeds for VANET
    
    for bbox in bbox_id:
        x3, y3, x4, y4, vehicle_id = bbox
        cx = int((x3 + x4) / 2)
        cy = int((y3 + y4) / 2)
        red_line_y = 198
        blue_line_y = 268
        offset = 7
        
        current_speed = 0  # Default speed

        # Speed calculation (downward traffic)
        if red_line_y < (cy + offset) and red_line_y > (cy - offset):
            down[vehicle_id] = time.time()
        if vehicle_id in down:
            if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
                elapsed_time = time.time() - down[vehicle_id]
                if counter_down.count(vehicle_id) == 0:
                    counter_down.append(vehicle_id)
                    distance = 100  # meters
                    a_speed_ms = distance / elapsed_time
                    current_speed = a_speed_ms * 3.6  # km/h
                    vehicle_speeds[vehicle_id] = current_speed

        # Speed calculation (upward traffic)
        if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
            up[vehicle_id] = time.time()
        if vehicle_id in up:
            if red_line_y < (cy + offset) and red_line_y > (cy - offset):
                elapsed1_time = time.time() - up[vehicle_id]
                if counter_up.count(vehicle_id) == 0:
                    counter_up.append(vehicle_id)
                    distance1 = 100  # meters
                    a_speed_ms1 = distance1 / elapsed1_time
                    current_speed = a_speed_ms1 * 3.6  # km/h
                    vehicle_speeds[vehicle_id] = current_speed
        
        # If no speed calculated, use a random speed for demo (simulate sensor data)
        if vehicle_id not in vehicle_speeds:
            # Use a realistic speed range
            current_speed = random.uniform(40, 80)  # km/h
            vehicle_speeds[vehicle_id] = current_speed

        # Update VANET with vehicle position and speed
        vanet.add_or_update_vehicle(vehicle_id, cx, cy, current_speed)

        # Draw bounding box and vehicle ID
        cv2.rectangle(frame, (x3, y3), (x4, y4), green_color, 2)
        cv2.circle(frame, (cx, cy), 4, red_color, -1)
        
        # Get shared speed information from VANET
        if vehicle_id in vanet.vehicles:
            vehicle_node = vanet.vehicles[vehicle_id]
            shared_speeds = vehicle_node.get_nearby_speeds()
            
            # Draw speed sharing information
            draw_speed_sharing_info(frame, vehicle_id, x3, y3, current_speed, shared_speeds)

    # Simulate VANET communication
    messages_sent = vanet.simulate_communication()
    
    # Draw communication lines between vehicles
    draw_communication_lines(frame, vanet)
    
    # Draw reference lines
    cv2.line(frame, (172, 198), (774, 198), red_color, 3)
    cv2.putText(frame, ('red line'), (172, 198), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)
    
    cv2.line(frame, (8, 268), (927, 268), blue_color, 3)
    cv2.putText(frame, ('blue line'), (8, 268), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)
    
    # Draw traffic counters
    cv2.putText(frame, ('Going Down - ' + str(len(counter_down))), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)
    cv2.putText(frame, ('Going Up - ' + str(len(counter_up))), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)
    
    # Draw VANET status with frame info
    draw_vanet_status(frame, vanet, current_frame, total_frames, auto_play)

    cv2.imshow('Car Speed Estimation with VANET - Frame Control', frame)
    
    # Enhanced frame control
    wait_time = 100 if auto_play else 0  # Auto-play with 100ms delay, or wait for key
    key = cv2.waitKey(wait_time) & 0xFF
    
    if key == 27:  # ESC key to exit
        break
    elif key == ord(' '):  # SPACEBAR - next frame (always works)
        continue
    elif key == ord('p'):  # 'p' - toggle play/pause
        auto_play = not auto_play
        mode_text = "AUTO-PLAY" if auto_play else "MANUAL (frame-by-frame)"
        print(f"Mode changed to: {mode_text}")
    elif key == ord('r'):  # 'r' - restart video
        vi.set(cv2.CAP_PROP_POS_FRAMES, 0)
        current_frame = 0
        count = 0
        down.clear()
        up.clear()
        counter_down.clear()
        counter_up.clear()
        vanet = VANETSpeedSharing()  # Reset VANET
        print("Video restarted")

vi.release()
cv2.destroyAllWindows()
