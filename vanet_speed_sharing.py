"""
Simple VANET Speed Sharing System
Shows vehicles communicating their speeds to each other
"""

import time
import math
from typing import Dict, List, Tuple

class VehicleNode:
    def __init__(self, vehicle_id: int, x: float, y: float, speed: float):
        self.vehicle_id = vehicle_id
        self.x = x
        self.y = y
        self.speed = speed
        self.shared_speeds = {}  # Dictionary to store received speeds from other vehicles
        self.last_broadcast = time.time()
        self.communication_range = 100  # pixels (communication range)
        
    def update_position(self, x: float, y: float, speed: float):
        """Update vehicle position and speed"""
        self.x = x
        self.y = y
        self.speed = speed
        
    def can_communicate_with(self, other_vehicle) -> bool:
        """Check if this vehicle can communicate with another vehicle"""
        distance = math.sqrt((self.x - other_vehicle.x)**2 + (self.y - other_vehicle.y)**2)
        return distance <= self.communication_range
    
    def broadcast_speed(self) -> dict:
        """Broadcast this vehicle's speed information"""
        self.last_broadcast = time.time()
        return {
            'sender_id': self.vehicle_id,
            'speed': self.speed,
            'position': (self.x, self.y),
            'timestamp': self.last_broadcast
        }
    
    def receive_speed_info(self, sender_id: int, speed: float, position: Tuple[float, float]):
        """Receive speed information from another vehicle"""
        self.shared_speeds[sender_id] = {
            'speed': speed,
            'position': position,
            'received_at': time.time()
        }
        
    def get_nearby_speeds(self) -> Dict:
        """Get speeds from nearby vehicles (clean up old data)"""
        current_time = time.time()
        # Remove speed data older than 5 seconds
        self.shared_speeds = {
            vid: data for vid, data in self.shared_speeds.items()
            if current_time - data['received_at'] < 5.0
        }
        return self.shared_speeds

class VANETSpeedSharing:
    def __init__(self):
        self.vehicles: Dict[int, VehicleNode] = {}
        self.message_log = []
        
    def add_or_update_vehicle(self, vehicle_id: int, x: float, y: float, speed: float):
        """Add new vehicle or update existing one"""
        if vehicle_id in self.vehicles:
            self.vehicles[vehicle_id].update_position(x, y, speed)
        else:
            self.vehicles[vehicle_id] = VehicleNode(vehicle_id, x, y, speed)
            
    def simulate_communication(self):
        """Simulate V2V communication between all vehicles"""
        messages_sent = 0
        
        # Each vehicle broadcasts its speed
        for vehicle_id, vehicle in self.vehicles.items():
            # Broadcast every 1 second
            if time.time() - vehicle.last_broadcast >= 1.0:
                speed_message = vehicle.broadcast_speed()
                
                # Send to all nearby vehicles
                for other_id, other_vehicle in self.vehicles.items():
                    if other_id != vehicle_id and vehicle.can_communicate_with(other_vehicle):
                        other_vehicle.receive_speed_info(
                            vehicle_id, 
                            vehicle.speed, 
                            (vehicle.x, vehicle.y)
                        )
                        messages_sent += 1
                        
                        # Log the communication
                        self.message_log.append({
                            'timestamp': time.time(),
                            'from': vehicle_id,
                            'to': other_id,
                            'speed_shared': vehicle.speed,
                            'distance': math.sqrt((vehicle.x - other_vehicle.x)**2 + (vehicle.y - other_vehicle.y)**2)
                        })
        
        return messages_sent
    
    def get_communication_pairs(self) -> List[Tuple]:
        """Get list of vehicles that can communicate with each other"""
        pairs = []
        vehicle_ids = list(self.vehicles.keys())
        
        for i, vid1 in enumerate(vehicle_ids):
            for vid2 in vehicle_ids[i+1:]:
                if self.vehicles[vid1].can_communicate_with(self.vehicles[vid2]):
                    pairs.append((vid1, vid2))
                    
        return pairs
    
    def get_recent_messages(self, last_n_seconds: int = 5) -> List[dict]:
        """Get recent communication messages"""
        current_time = time.time()
        return [
            msg for msg in self.message_log
            if current_time - msg['timestamp'] <= last_n_seconds
        ]
    
    def cleanup_old_vehicles(self, timeout_seconds: int = 10):
        """Remove vehicles that haven't been updated recently"""
        # This would be called periodically to clean up inactive vehicles
        pass
