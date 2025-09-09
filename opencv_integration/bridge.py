# OpenCV <-> Network Simulator Bridge
# Writes vehicle detections to JSON for OMNET++/NS-3, and reads back results for overlay

import json
import os
import time
from typing import Dict, List, Tuple

IN_DIR = os.path.join(os.path.dirname(__file__), 'vehicle_data.json')
OMNET_RESULTS = os.path.join(os.path.dirname(__file__), 'omnet_results.json')
NS3_RESULTS = os.path.join(os.path.dirname(__file__), 'ns3_results.json')


def write_vehicle_data(vehicles: List[Tuple[int, int, int]]):
    """
    Write current vehicle data to JSON.
    vehicles: list of (vehicle_id, x, y). Speed optional; if available, provide (id, x, y, speed)
    """
    payload = {}
    now = time.time()
    for item in vehicles:
        if len(item) == 4:
            vid, x, y, speed = item
        else:
            vid, x, y = item
            speed = 0.0
        payload[f'vehicle_{vid}'] = {
            'id': vid,
            'x': float(x),
            'y': float(y),
            'speed': float(speed),
            'timestamp': now
        }
    tmp = IN_DIR + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(payload, f)
    os.replace(tmp, IN_DIR)


def read_omnet_results() -> Dict:
    if not os.path.exists(OMNET_RESULTS):
        return {}
    try:
        with open(OMNET_RESULTS, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def read_ns3_results() -> Dict:
    if not os.path.exists(NS3_RESULTS):
        return {}
    try:
        with open(NS3_RESULTS, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

