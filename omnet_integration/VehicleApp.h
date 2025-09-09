#ifndef __VANET_VEHICLEAPP_H
#define __VANET_VEHICLEAPP_H

#include <omnetpp.h>
#include "inet/applications/base/ApplicationBase.h"
#include "inet/transportlayer/contract/udp/UdpSocket.h"
#include "VANETSpeedMessage_m.h"
#include <map>

using namespace omnetpp;
using namespace inet;

struct ReceivedSpeedInfo {
    int vehicleId;
    double speed;
    double positionX;
    double positionY;
    simtime_t timestamp;
    double distance;
};

class VehicleApp : public cSimpleModule
{
  private:
    // Parameters
    simtime_t messageInterval;
    double maxSpeed;
    int messageLength;
    std::string messageName;
    bool enableSpeedSharing;
    double communicationRange;
    bool useRealPositions;
    
    // Vehicle properties
    int vehicleId;
    std::string vehicleType;
    
    // Real-time data from OpenCV
    double realSpeed;
    double realPositionX;
    double realPositionY;
    
    // Network components
    UdpSocket* socket;
    cMessage* selfMsg;
    
    // Statistics
    int packetsSent;
    int packetsReceived;
    double totalDelay;
    
    // Received speed information from other vehicles
    std::map<int, ReceivedSpeedInfo> receivedSpeeds;
    
  protected:
    virtual void initialize(int stage) override;
    virtual int numInitStages() const override { return NUM_INIT_STAGES; }
    virtual void handleMessage(cMessage *msg) override;
    virtual void finish() override;
    
    // Application-specific methods
    virtual void sendSpeedMessage();
    virtual void handleIncomingMessage(Packet* packet);
    virtual void loadRealTimeData();
    virtual void exportToOpenCV();
    virtual void updatePosition();
    virtual double calculateDistance(double x1, double y1, double x2, double y2);
    virtual void cleanOldReceivedSpeeds();
    
  public:
    VehicleApp();
    virtual ~VehicleApp();
};

#endif
