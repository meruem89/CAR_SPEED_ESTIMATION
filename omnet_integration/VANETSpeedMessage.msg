//
// VANET Speed Message Definition for OMNET++
//
cplusplus {{
#include "inet/common/INETDefs.h"
}}

namespace vanet;

enum MessageType
{
    SPEED_BROADCAST = 1;
    EMERGENCY_BRAKE = 2;
    TRAFFIC_JAM = 3;
    WEATHER_UPDATE = 4;
}

//
// VANET Speed Sharing Message
// This message carries vehicle speed and position information
//
packet VANETSpeedMessage
{
    // Vehicle identification
    int vehicleId;
    string vehicleType;
    
    // Speed and position data
    double speed;           // m/s
    double positionX;       // meters
    double positionY;       // meters
    
    // Message metadata
    simtime_t timestamp;
    int messageType @enum(MessageType) = SPEED_BROADCAST;
    int sequenceNumber;
    
    // Additional VANET data
    double acceleration;    // m/s²
    double heading;        // degrees (0-360)
    int laneId;           // Lane identifier
    string roadId;        // Road segment identifier
    
    // Traffic conditions
    double density;       // vehicles per km
    string weather;       // weather conditions
    bool emergencyBrake;  // emergency braking flag
    
    // Network performance
    int hopCount = 0;     // Number of hops (for multi-hop)
    double signalStrength; // Signal strength (dBm)
}
