# -*- coding: utf-8 -*-
"""VANET Car Speed Estimator - Range-Based Communication"""

import cv2
import pandas as pd
from ultralytics import YOLO
from tracker import*
import time
import math

model = YOLO('yolov8n.pt')
vi = cv2.VideoCapture('highway_mini.mp4')

class_list = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven',
              'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

class RangeBasedVANET:
    def __init__(self, communication_range=200):
        self.vehicles = {}  # vehicle_id: {x, y, direction, calculated_speed, received_speeds}
        self.communication_range = communication_range  # pixels
        self.recent_broadcasts = []  # Recent speed broadcasts for visualization
        
    def add_vehicle(self, vehicle_id, x, y):
        """Add or update vehicle position"""
        if vehicle_id not in self.vehicles:
            self.vehicles[vehicle_id] = {
                'x': x, 'y': y, 'direction': None, 
                'calculated_speed': None, 'received_speeds': []
            }
        else:
            self.vehicles[vehicle_id]['x'] = x
            self.vehicles[vehicle_id]['y'] = y
    
    def broadcast_speed_to_range(self, sender_id, speed, direction):
        """Broadcast calculated speed to ALL vehicles within range"""
        if sender_id not in self.vehicles:
            return []
            
        self.vehicles[sender_id]['calculated_speed'] = speed
        self.vehicles[sender_id]['direction'] = direction
        
        sender_pos = (self.vehicles[sender_id]['x'], self.vehicles[sender_id]['y'])
        recipients = []
        
        # Send to ALL vehicles within communication range
        for receiver_id, receiver_data in self.vehicles.items():
            if receiver_id == sender_id:
                continue
                
            receiver_pos = (receiver_data['x'], receiver_data['y'])
            distance = self.calculate_distance(sender_pos, receiver_pos)
            
            if distance <= self.communication_range:
                # Add speed to receiver's received speeds
                speed_info = {
                    'from_vehicle': sender_id,
                    'speed': speed,
                    'direction': direction,
                    'timestamp': time.time(),
                    'distance': distance
                }
                
                self.vehicles[receiver_id]['received_speeds'].append(speed_info)
                recipients.append(receiver_id)
        
        # Log broadcast for visualization
        if recipients:
            self.recent_broadcasts.append({
                'sender': sender_id,
                'speed': speed,
                'direction': direction,
                'recipients': recipients,
                'sender_pos': sender_pos,
                'timestamp': time.time()
            })
            
        return recipients
    
    def calculate_distance(self, pos1, pos2):
        """Calculate distance between two positions"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def get_vehicles_in_range(self, vehicle_id):
        """Get all vehicles within communication range"""
        if vehicle_id not in self.vehicles:
            return []
            
        vehicle_pos = (self.vehicles[vehicle_id]['x'], self.vehicles[vehicle_id]['y'])
        vehicles_in_range = []
        
        for other_id, other_data in self.vehicles.items():
            if other_id == vehicle_id:
                continue
                
            other_pos = (other_data['x'], other_data['y'])
            distance = self.calculate_distance(vehicle_pos, other_pos)
            
            if distance <= self.communication_range:
                vehicles_in_range.append((other_id, distance))
                
        return vehicles_in_range
    
    def cleanup_old_speeds(self):
        """Remove old received speeds (older than 8 seconds)"""
        current_time = time.time()
        for vehicle_id in self.vehicles:
            self.vehicles[vehicle_id]['received_speeds'] = [
                speed for speed in self.vehicles[vehicle_id]['received_speeds']
                if current_time - speed['timestamp'] <= 8.0
            ]
        
        # Cleanup old broadcasts
        self.recent_broadcasts = [
            broadcast for broadcast in self.recent_broadcasts
            if current_time - broadcast['timestamp'] <= 5.0
        ]

# Initialize
tracker = Tracker()
vanet = RangeBasedVANET(communication_range=180)  # 180 pixel communication range
count = 0

# Speed calculation variables
down = {}
up = {}
counter_down = []
counter_up = []

# Colors
text_color = (255, 255, 255)  # white
red_color = (0, 0, 255)       # red
blue_color = (255, 0, 0)      # blue
green_color = (0, 255, 0)     # green
yellow_color = (0, 255, 255)  # yellow
orange_color = (0, 165, 255)  # orange
purple_color = (255, 0, 255)  # purple

def draw_all_vehicles(frame, bbox_list, vanet_system):
    """Draw all detected vehicles as green squares with red dots"""
    for bbox in bbox_list:
        x3, y3, x4, y4, vehicle_id = bbox
        cx = int((x3 + x4) / 2)
        cy = int((y3 + y4) / 2)
        
        # Draw green bounding box (square)
        cv2.rectangle(frame, (x3, y3), (x4, y4), green_color, 2)
        
        # Draw red dot in center
        cv2.circle(frame, (cx, cy), 4, red_color, -1)
        
        # Draw vehicle ID
        cv2.putText(frame, f"ID:{vehicle_id}", (x3, y3-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
        
        # Show calculated speed if available (own speed)
        if vehicle_id in vanet_system.vehicles:
            vehicle_data = vanet_system.vehicles[vehicle_id]
            if vehicle_data['calculated_speed']:
                cv2.putText(frame, f"My: {int(vehicle_data['calculated_speed'])}km/h", 
                           (x3, y3-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, green_color, 2)
        
        # Show received speeds from other vehicles (above the car)
        if vehicle_id in vanet_system.vehicles:
            received_speeds = vanet_system.vehicles[vehicle_id]['received_speeds']
            if received_speeds:
                y_offset = -35
                cv2.putText(frame, "Received:", (x3, y3 + y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.3, orange_color, 1)
                y_offset -= 15
                
                # Show up to 4 received speeds
                for i, speed_info in enumerate(received_speeds[:4]):
                    from_id = speed_info['from_vehicle']
                    speed = speed_info['speed']
                    distance = speed_info['distance']
                    
                    speed_text = f"V{from_id}: {int(speed)}km/h ({int(distance)}px)"
                    cv2.putText(frame, speed_text, (x3, y3 + y_offset), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, purple_color, 1)
                    y_offset -= 12

def draw_communication_range_circles(frame, vanet_system):
    """Draw communication range circles for vehicles that recently broadcast"""
    recent_broadcasts = vanet_system.recent_broadcasts
    
    for broadcast in recent_broadcasts:
        sender_pos = broadcast['sender_pos']
        
        # Draw communication range circle (thin, semi-transparent)
        cv2.circle(frame, (int(sender_pos[0]), int(sender_pos[1])), 
                  vanet_system.communication_range, yellow_color, 1)

def draw_communication_lines(frame, vanet_system):
    """Draw lines showing recent communications"""
    recent_broadcasts = vanet_system.recent_broadcasts
    
    for broadcast in recent_broadcasts:
        sender_id = broadcast['sender']
        sender_pos = broadcast['sender_pos']
        recipients = broadcast['recipients']
        
        for recipient_id in recipients:
            if recipient_id in vanet_system.vehicles:
                recipient = vanet_system.vehicles[recipient_id]
                recipient_pos = (int(recipient['x']), int(recipient['y']))
                
                # Draw communication line
                cv2.line(frame, (int(sender_pos[0]), int(sender_pos[1])), 
                        recipient_pos, yellow_color, 1)
                
                # Draw small circle at midpoint
                mid_x = int((sender_pos[0] + recipient_pos[0]) / 2)
                mid_y = int((sender_pos[1] + recipient_pos[1]) / 2)
                cv2.circle(frame, (mid_x, mid_y), 2, yellow_color, -1)

def draw_vanet_status(frame, vanet_system):
    """Draw VANET status panel"""
    total_vehicles = len(vanet_system.vehicles)
    recent_broadcasts = len(vanet_system.recent_broadcasts)
    
    # Count vehicles with received speeds
    vehicles_with_data = sum(1 for v in vanet_system.vehicles.values() 
                            if len(v['received_speeds']) > 0)
    
    # Status panel
    cv2.rectangle(frame, (750, 10), (1010, 120), (0, 0, 0), -1)
    cv2.rectangle(frame, (750, 10), (1010, 120), text_color, 2)
    
    cv2.putText(frame, "RANGE-BASED VANET", (760, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, yellow_color, 2)
    cv2.putText(frame, f"Total Vehicles: {total_vehicles}", (760, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
    cv2.putText(frame, f"Receiving Data: {vehicles_with_data}", (760, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
    cv2.putText(frame, f"Recent Broadcasts: {recent_broadcasts}", (760, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)
    cv2.putText(frame, f"Range: {vanet_system.communication_range}px", (760, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)

print("🚗📡 RANGE-BASED VANET SPEED SHARING 📡🚗")
print("="*55)
print("Features:")
print("✓ All cars shown as green squares with red dots")
print("✓ Speed calculated when crossing second line")
print("✓ Broadcast to ALL cars within range (180px)")
print("✓ Received speeds shown ABOVE all cars in range")
print("✓ Yellow circles show communication range")
print("✓ Yellow lines show active communications")
print("\nControls:")
print("  SPACEBAR - Next frame")
print("  'p' - Toggle auto/manual mode") 
print("  ESC - Exit")
print("="*55)

auto_play = False

while True:
    ret, frame = vi.read()
    if not ret:
        break
        
    count += 1
    frame = cv2.resize(frame, (1020, 500))

    # YOLO detection
    results = model.predict(frame)
    a = results[0].boxes.data
    a = a.detach().cpu().numpy()
    px = pd.DataFrame(a).astype("float")
    
    detected_cars = []
    for index, row in px.iterrows():
        x1, y1, x2, y2 = int(row[0]), int(row[1]), int(row[2]), int(row[3])
        d = int(row[5])
        c = class_list[d]
        if 'car' in c:
            detected_cars.append([x1, y1, x2, y2])

    # Update tracker
    bbox_id = tracker.update(detected_cars)
    
    # Add all detected vehicles to VANET
    for bbox in bbox_id:
        x3, y3, x4, y4, vehicle_id = bbox
        cx = int((x3 + x4) / 2)
        cy = int((y3 + y4) / 2)
        
        # Add vehicle to VANET system
        vanet.add_vehicle(vehicle_id, cx, cy)
        
        red_line_y = 198
        blue_line_y = 268
        offset = 7
        
        # Speed calculation for DOWNWARD traffic
        if red_line_y < (cy + offset) and red_line_y > (cy - offset):
            down[vehicle_id] = time.time()
            
        if vehicle_id in down:
            if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
                elapsed_time = time.time() - down[vehicle_id]
                if counter_down.count(vehicle_id) == 0:
                    counter_down.append(vehicle_id)
                    distance = 100  # meters
                    a_speed_ms = distance / elapsed_time
                    calculated_speed = a_speed_ms * 3.6  # km/h
                    
                    # VANET: Broadcast speed to ALL vehicles within range
                    recipients = vanet.broadcast_speed_to_range(vehicle_id, calculated_speed, "DOWN")
                    if recipients:
                        print(f"🚗 Vehicle {vehicle_id} broadcasts {int(calculated_speed)}km/h to {len(recipients)} cars: {recipients}")

        # Speed calculation for UPWARD traffic
        if blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
            up[vehicle_id] = time.time()
            
        if vehicle_id in up:
            if red_line_y < (cy + offset) and red_line_y > (cy - offset):
                elapsed1_time = time.time() - up[vehicle_id]
                if counter_up.count(vehicle_id) == 0:
                    counter_up.append(vehicle_id)
                    distance1 = 100  # meters
                    a_speed_ms1 = distance1 / elapsed1_time
                    calculated_speed = a_speed_ms1 * 3.6  # km/h
                    
                    # VANET: Broadcast speed to ALL vehicles within range
                    recipients = vanet.broadcast_speed_to_range(vehicle_id, calculated_speed, "UP")
                    if recipients:
                        print(f"🚗 Vehicle {vehicle_id} broadcasts {int(calculated_speed)}km/h to {len(recipients)} cars: {recipients}")

    # Draw all vehicles (green squares with red dots)
    draw_all_vehicles(frame, bbox_id, vanet)
    
    # Draw communication range circles
    draw_communication_range_circles(frame, vanet)
    
    # Draw communication lines
    draw_communication_lines(frame, vanet)
    
    # Draw reference lines
    cv2.line(frame, (172, 198), (774, 198), red_color, 3)
    cv2.putText(frame, ('red line'), (172, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    
    cv2.line(frame, (8, 268), (927, 268), blue_color, 3)
    cv2.putText(frame, ('blue line'), (8, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    
    # Draw counters
    cv2.putText(frame, f'Going Down - {len(counter_down)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    cv2.putText(frame, f'Going Up - {len(counter_up)}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    
    # Draw VANET status
    draw_vanet_status(frame, vanet)
    
    # Cleanup old data
    vanet.cleanup_old_speeds()

    cv2.imshow('Range-Based VANET Speed Sharing', frame)
    
    # Frame control
    wait_time = 100 if auto_play else 0
    key = cv2.waitKey(wait_time) & 0xFF
    
    if key == 27:  # ESC
        break
    elif key == ord(' '):  # SPACEBAR
        continue
    elif key == ord('p'):  # Toggle mode
        auto_play = not auto_play
        print(f"Mode: {'AUTO' if auto_play else 'MANUAL'}")

vi.release()
cv2.destroyAllWindows()
