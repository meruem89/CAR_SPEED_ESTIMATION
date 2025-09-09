//
// VANET Simulation Network for OMNET++
// Integrates with OpenCV vehicle detection system
//
package vanet.simulation;

import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.node.inet.ManetRouter;
import inet.physicallayer.ieee80211.packetlevel.Ieee80211ScalarRadioMedium;
import inet.environment.common.PhysicalEnvironment;
import inet.mobility.single.LinearMobility;

network VANETHighwayScenario
{
    parameters:
        @display("bgb=1400,700;bgi=background/highway");
        int numVehicles = default(10);
        
    submodules:
        radioMedium: Ieee80211ScalarRadioMedium {
            parameters:
                @display("p=50,50");
        }
        
        configurator: Ipv4NetworkConfigurator {
            parameters:
                @display("p=50,100");
        }
        
        physicalEnvironment: PhysicalEnvironment {
            parameters:
                @display("p=50,150");
        }
        
        // Dynamic vehicle nodes - will be created based on OpenCV detection
        vehicle[numVehicles]: VehicleNode {
            parameters:
                @display("i=device/car");
        }
}

//
// Enhanced Vehicle Node with VANET capabilities
//
simple VehicleApp
{
    parameters:
        // VANET application parameters
        double messageInterval @unit(s) = default(1s);
        double maxSpeed @unit(mps) = default(30mps);
        int messageLength @unit(B) = default(512B);
        string messageName = default("VANETMessage");
        
        // Speed sharing parameters
        bool enableSpeedSharing = default(true);
        double communicationRange @unit(m) = default(300m);
        
        // Integration with OpenCV system
        bool useRealPositions = default(true);
        string positionUpdateMode = default("external"); // "external" or "mobility"
        
    gates:
        input socketIn;
        output socketOut;
}

module VehicleNode
{
    parameters:
        @networkNode();
        @display("i=device/car;is=s");
        
        // Vehicle identification
        int vehicleId;
        string vehicleType = default("car");
        
        // Real-time parameters from OpenCV
        double realSpeed @unit(mps) = default(0mps);
        double realPositionX @unit(m) = default(0m);
        double realPositionY @unit(m) = default(0m);
        
    gates:
        input radioIn @directIn;
        
    submodules:
        // Application layer - VANET speed sharing
        app: VehicleApp {
            parameters:
                @display("p=147,54");
        }
        
        // Network stack
        manetRouter: ManetRouter {
            parameters:
                @display("p=147,207");
        }
        
    connections:
        app.socketOut --> manetRouter.appIn++;
        app.socketIn <-- manetRouter.appOut++;
        manetRouter.radioIn <-- radioIn;
}
