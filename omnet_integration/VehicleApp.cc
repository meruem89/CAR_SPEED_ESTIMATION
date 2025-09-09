#include "VehicleApp.h"
#include "inet/common/ModuleAccess.h"
#include "inet/common/packet/Packet.h"
#include "inet/networklayer/common/L3AddressResolver.h"
#include "inet/transportlayer/contract/udp/UdpSocket.h"
#include <fstream>
#include <json/json.h>

Define_Module(VehicleApp);

VehicleApp::VehicleApp()
{
    selfMsg = nullptr;
    socket = nullptr;
}

VehicleApp::~VehicleApp()
{
    cancelAndDelete(selfMsg);
    delete socket;
}

void VehicleApp::initialize(int stage)
{
    cSimpleModule::initialize(stage);
    
    if (stage == INITSTAGE_LOCAL) {
        // Get parameters
        messageInterval = par("messageInterval");
        maxSpeed = par("maxSpeed").doubleValue();
        messageLength = par("messageLength");
        messageName = par("messageName").stdstringValue();
        enableSpeedSharing = par("enableSpeedSharing");
        communicationRange = par("communicationRange").doubleValue();
        useRealPositions = par("useRealPositions");
        
        // Get vehicle parameters
        vehicleId = getParentModule()->par("vehicleId");
        vehicleType = getParentModule()->par("vehicleType").stdstringValue();
        
        // Initialize real-time parameters
        realSpeed = 0.0;
        realPositionX = 0.0;
        realPositionY = 0.0;
        
        // Statistics
        packetsSent = 0;
        packetsReceived = 0;
        totalDelay = 0.0;
        
        // Create self message for periodic broadcasting
        selfMsg = new cMessage("sendMessage");
        
        // Initialize socket
        socket = new UdpSocket();
        socket->setOutputGate(gate("socketOut"));
        socket->bind(5000 + vehicleId); // Unique port per vehicle
        
        EV_INFO << "Vehicle " << vehicleId << " initialized with speed sharing: " 
                << (enableSpeedSharing ? "enabled" : "disabled") << endl;
    }
    else if (stage == INITSTAGE_APPLICATION_LAYER) {
        // Start the application
        scheduleAt(simTime() + uniform(0.0, messageInterval.dbl()), selfMsg);
        
        // Load initial position from OpenCV integration file if available
        loadRealTimeData();
    }
}

void VehicleApp::handleMessage(cMessage *msg)
{
    if (msg == selfMsg) {
        // Time to send a message
        sendSpeedMessage();
        scheduleAt(simTime() + messageInterval, selfMsg);
    }
    else {
        // Received message from network
        auto packet = check_and_cast<Packet*>(msg);
        handleIncomingMessage(packet);
    }
}

void VehicleApp::sendSpeedMessage()
{
    if (!enableSpeedSharing) return;
    
    // Load real-time data from OpenCV system
    loadRealTimeData();
    
    // Create VANET speed message
    auto packet = new Packet("VANETSpeedMessage");
    auto speedMsg = makeShared<VANETSpeedMessage>();
    
    speedMsg->setVehicleId(vehicleId);
    speedMsg->setSpeed(realSpeed);
    speedMsg->setPositionX(realPositionX);
    speedMsg->setPositionY(realPositionY);
    speedMsg->setTimestamp(simTime());
    speedMsg->setVehicleType(vehicleType.c_str());
    speedMsg->setMessageType(SPEED_BROADCAST);
    
    packet->insertAtBack(speedMsg);
    packet->setByteLength(messageLength);
    
    // Broadcast to all vehicles in range
    L3Address destAddr = L3Address(Ipv4Address::ALLONES_ADDRESS);
    socket->sendTo(packet, destAddr, 5000);
    
    packetsSent++;
    
    EV_INFO << "Vehicle " << vehicleId << " broadcasted speed: " << realSpeed 
            << " m/s at position (" << realPositionX << ", " << realPositionY << ")" << endl;
}

void VehicleApp::handleIncomingMessage(Packet* packet)
{
    auto speedMsg = packet->peekAtFront<VANETSpeedMessage>();
    
    // Calculate distance to sender
    double distance = calculateDistance(realPositionX, realPositionY,
                                      speedMsg->getPositionX(), speedMsg->getPositionY());
    
    // Only process messages from vehicles within communication range
    if (distance <= communicationRange) {
        packetsReceived++;
        
        // Calculate end-to-end delay
        simtime_t delay = simTime() - speedMsg->getTimestamp();
        totalDelay += delay.dbl();
        
        // Store received speed information
        ReceivedSpeedInfo info;
        info.vehicleId = speedMsg->getVehicleId();
        info.speed = speedMsg->getSpeed();
        info.positionX = speedMsg->getPositionX();
        info.positionY = speedMsg->getPositionY();
        info.timestamp = simTime();
        info.distance = distance;
        
        receivedSpeeds[speedMsg->getVehicleId()] = info;
        
        // Clean old entries (older than 5 seconds)
        cleanOldReceivedSpeeds();
        
        EV_INFO << "Vehicle " << vehicleId << " received speed from Vehicle " 
                << speedMsg->getVehicleId() << ": " << speedMsg->getSpeed() 
                << " m/s (distance: " << distance << " m)" << endl;
        
        // Export data to integration file for OpenCV visualization
        exportToOpenCV();
    }
    
    delete packet;
}

void VehicleApp::loadRealTimeData()
{
    // Load real-time vehicle data from OpenCV integration file
    std::string filename = "opencv_integration/vehicle_data.json";
    std::ifstream file(filename);
    
    if (file.is_open()) {
        Json::Value root;
        Json::Reader reader;
        
        if (reader.parse(file, root)) {
            std::string vehicleKey = "vehicle_" + std::to_string(vehicleId);
            
            if (root.isMember(vehicleKey)) {
                Json::Value vehicleData = root[vehicleKey];
                
                realSpeed = vehicleData.get("speed", 0.0).asDouble();
                realPositionX = vehicleData.get("x", 0.0).asDouble();
                realPositionY = vehicleData.get("y", 0.0).asDouble();
                
                // Update OMNET++ mobility if needed
                updatePosition();
            }
        }
        file.close();
    }
}

void VehicleApp::exportToOpenCV()
{
    // Export OMNET++ simulation data back to OpenCV for visualization
    Json::Value root;
    Json::Value vehicleData;
    
    vehicleData["vehicle_id"] = vehicleId;
    vehicleData["speed"] = realSpeed;
    vehicleData["position_x"] = realPositionX;
    vehicleData["position_y"] = realPositionY;
    vehicleData["packets_sent"] = packetsSent;
    vehicleData["packets_received"] = packetsReceived;
    vehicleData["avg_delay"] = (packetsReceived > 0) ? (totalDelay / packetsReceived) : 0.0;
    vehicleData["neighbors_count"] = (int)receivedSpeeds.size();
    
    // Add received speeds information
    Json::Value neighbors(Json::arrayValue);
    for (auto& pair : receivedSpeeds) {
        Json::Value neighbor;
        neighbor["id"] = pair.second.vehicleId;
        neighbor["speed"] = pair.second.speed;
        neighbor["distance"] = pair.second.distance;
        neighbors.append(neighbor);
    }
    vehicleData["neighbors"] = neighbors;
    
    root["vehicles"][std::to_string(vehicleId)] = vehicleData;
    
    // Write to integration file
    std::string filename = "opencv_integration/omnet_results.json";
    std::ofstream file(filename);
    if (file.is_open()) {
        Json::StreamWriterBuilder builder;
        std::unique_ptr<JsonларStreamWriter> writer(builder.newStreamWriter());
        writer->write(root, &file);
        file.close();
    }
}

void VehicleApp::updatePosition()
{
    // Update OMNET++ node position based on OpenCV detection
    if (useRealPositions) {
        auto mobility = check_and_cast<IMobility*>(getParentModule()->getSubmodule("mobility"));
        if (mobility) {
            Coord newPos(realPositionX, realPositionY, 0);
            mobility->setCurrentPosition(newPos);
        }
    }
}

double VehicleApp::calculateDistance(double x1, double y1, double x2, double y2)
{
    return sqrt(pow(x2 - x1, 2) + pow(y2 - y1, 2));
}

void VehicleApp::cleanOldReceivedSpeeds()
{
    simtime_t currentTime = simTime();
    auto it = receivedSpeeds.begin();
    
    while (it != receivedSpeeds.end()) {
        if (currentTime - it->second.timestamp > 5.0) {
            it = receivedSpeeds.erase(it);
        } else {
            ++it;
        }
    }
}

void VehicleApp::finish()
{
    // Record statistics
    recordScalar("packetsSent", packetsSent);
    recordScalar("packetsReceived", packetsReceived);
    recordScalar("averageDelay", (packetsReceived > 0) ? (totalDelay / packetsReceived) : 0.0);
    recordScalar("throughput", packetsReceived / simTime().dbl());
    
    EV_INFO << "Vehicle " << vehicleId << " finished:" << endl;
    EV_INFO << "  Packets sent: " << packetsSent << endl;
    EV_INFO << "  Packets received: " << packetsReceived << endl;
    EV_INFO << "  Average delay: " << ((packetsReceived > 0) ? (totalDelay / packetsReceived) : 0.0) << " s" << endl;
}
