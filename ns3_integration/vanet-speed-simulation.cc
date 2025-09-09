#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/wifi-module.h"
#include "ns3/wave-module.h"
#include "ns3/applications-module.h"
#include "ns3/netanim-module.h"
#include <fstream>
#include <json/json.h>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("VANETSpeedSimulation");

class VANETSpeedApp : public Application
{
public:
  VANETSpeedApp ();
  virtual ~VANETSpeedApp ();
  
  void Setup (Ptr<Socket> socket, Address address, uint32_t packetSize, 
              uint32_t nPackets, DataRate dataRate, uint32_t vehicleId);
  
  void SetVehicleData(double speed, double x, double y);
  void SendSpeedMessage();
  void HandleRead (Ptr<Socket> socket);
  
private:
  virtual void StartApplication (void);
  virtual void StopApplication (void);
  
  void ScheduleTx (void);
  void LoadOpenCVData (void);
  void ExportToOpenCV (void);
  
  Ptr<Socket>     m_socket;
  Address         m_peer;
  uint32_t        m_packetSize;
  uint32_t        m_nPackets;
  DataRate        m_dataRate;
  EventId         m_sendEvent;
  bool            m_running;
  uint32_t        m_packetsSent;
  uint32_t        m_packetsReceived;
  uint32_t        m_vehicleId;
  
  // Vehicle data
  double          m_speed;
  double          m_positionX;
  double          m_positionY;
  
  // Received data from other vehicles
  std::map<uint32_t, double> m_receivedSpeeds;
  std::map<uint32_t, Time>   m_lastReceived;
};

VANETSpeedApp::VANETSpeedApp ()
  : m_socket (0),
    m_peer (),
    m_packetSize (0),
    m_nPackets (0),
    m_dataRate (0),
    m_sendEvent (),
    m_running (false),
    m_packetsSent (0),
    m_packetsReceived (0),
    m_vehicleId (0),
    m_speed (0.0),
    m_positionX (0.0),
    m_positionY (0.0)
{
}

VANETSpeedApp::~VANETSpeedApp ()
{
  m_socket = 0;
}

void
VANETSpeedApp::Setup (Ptr<Socket> socket, Address address, uint32_t packetSize, 
                      uint32_t nPackets, DataRate dataRate, uint32_t vehicleId)
{
  m_socket = socket;
  m_peer = address;
  m_packetSize = packetSize;
  m_nPackets = nPackets;
  m_dataRate = dataRate;
  m_vehicleId = vehicleId;
}

void
VANETSpeedApp::StartApplication (void)
{
  m_running = true;
  m_packetsSent = 0;
  m_packetsReceived = 0;
  
  if (InetSocketAddress::IsMatchingType (m_peer))
    {
      m_socket->Bind ();
    }
  else
    {
      m_socket->Bind6 ();
    }

  m_socket->SetRecvCallback (MakeCallback (&VANETSpeedApp::HandleRead, this));
  
  // Start sending speed messages
  ScheduleTx ();
}

void
VANETSpeedApp::StopApplication (void)
{
  m_running = false;

  if (m_sendEvent.IsRunning ())
    {
      Simulator::Cancel (m_sendEvent);
    }

  if (m_socket)
    {
      m_socket->Close ();
    }
}

void
VANETSpeedApp::ScheduleTx (void)
{
  if (m_running)
    {
      Time tNext (Seconds (m_packetSize * 8 / static_cast<double> (m_dataRate.GetBitRate ())));
      m_sendEvent = Simulator::Schedule (tNext, &VANETSpeedApp::SendSpeedMessage, this);
    }
}

void
VANETSpeedApp::LoadOpenCVData (void)
{
  // Load real-time vehicle data from OpenCV integration
  std::ifstream file("opencv_integration/vehicle_data.json");
  if (file.is_open()) {
    Json::Value root;
    Json::Reader reader;
    
    if (reader.parse(file, root)) {
      std::string vehicleKey = "vehicle_" + std::to_string(m_vehicleId);
      if (root.isMember(vehicleKey)) {
        Json::Value vehicleData = root[vehicleKey];
        m_speed = vehicleData.get("speed", 0.0).asDouble();
        m_positionX = vehicleData.get("x", 0.0).asDouble();
        m_positionY = vehicleData.get("y", 0.0).asDouble();
        
        // Update NS-3 mobility model
        Ptr<MobilityModel> mobility = GetNode()->GetObject<MobilityModel>();
        if (mobility) {
          Vector pos(m_positionX, m_positionY, 0);
          mobility->SetPosition(pos);
        }
      }
    }
    file.close();
  }
}

void
VANETSpeedApp::SendSpeedMessage (void)
{
  // Load latest data from OpenCV
  LoadOpenCVData();
  
  NS_LOG_FUNCTION (this);
  
  // Create VANET speed message
  Ptr<Packet> packet = Create<Packet> ();
  
  // Add custom header with speed and position
  VANETSpeedHeader header;
  header.SetVehicleId(m_vehicleId);
  header.SetSpeed(m_speed);
  header.SetPositionX(m_positionX);
  header.SetPositionY(m_positionY);
  header.SetTimestamp(Simulator::Now());
  
  packet->AddHeader(header);
  packet->SetSize(m_packetSize);
  
  // Broadcast message
  m_socket->SendTo(packet, 0, m_peer);
  
  ++m_packetsSent;
  
  NS_LOG_INFO ("Vehicle " << m_vehicleId << " sent speed: " << m_speed 
               << " m/s at position (" << m_positionX << ", " << m_positionY << ")");
  
  // Export data for OpenCV visualization
  ExportToOpenCV();
  
  // Schedule next transmission
  if (m_packetsSent < m_nPackets)
    {
      ScheduleTx ();
    }
}

void
VANETSpeedApp::HandleRead (Ptr<Socket> socket)
{
  NS_LOG_FUNCTION (this << socket);
  
  Ptr<Packet> packet;
  Address from;
  
  while ((packet = socket->RecvFrom (from)))
    {
      if (packet->GetSize () > 0)
        {
          ++m_packetsReceived;
          
          // Extract VANET speed header
          VANETSpeedHeader header;
          packet->RemoveHeader(header);
          
          uint32_t senderId = header.GetVehicleId();
          double senderSpeed = header.GetSpeed();
          double senderX = header.GetPositionX();
          double senderY = header.GetPositionY();
          
          // Calculate distance to sender
          double distance = sqrt(pow(senderX - m_positionX, 2) + pow(senderY - m_positionY, 2));
          
          // Only process messages from vehicles within 300m range
          if (distance <= 300.0 && senderId != m_vehicleId) {
            // Store received speed information
            m_receivedSpeeds[senderId] = senderSpeed;
            m_lastReceived[senderId] = Simulator::Now();
            
            NS_LOG_INFO ("Vehicle " << m_vehicleId << " received speed from Vehicle " 
                         << senderId << ": " << senderSpeed << " m/s (distance: " 
                         << distance << " m)");
          }
          
          // Clean old received data (older than 5 seconds)
          Time currentTime = Simulator::Now();
          auto it = m_lastReceived.begin();
          while (it != m_lastReceived.end()) {
            if (currentTime - it->second > Seconds(5.0)) {
              m_receivedSpeeds.erase(it->first);
              it = m_lastReceived.erase(it);
            } else {
              ++it;
            }
          }
        }
    }
}

void
VANETSpeedApp::ExportToOpenCV (void)
{
  // Export NS-3 simulation data to OpenCV
  Json::Value root;
  Json::Value vehicleData;
  
  vehicleData["vehicle_id"] = m_vehicleId;
  vehicleData["speed"] = m_speed;
  vehicleData["position_x"] = m_positionX;
  vehicleData["position_y"] = m_positionY;
  vehicleData["packets_sent"] = m_packetsSent;
  vehicleData["packets_received"] = m_packetsReceived;
  vehicleData["neighbors_count"] = (int)m_receivedSpeeds.size();
  
  // Add received speeds
  Json::Value neighbors(Json::arrayValue);
  for (auto& pair : m_receivedSpeeds) {
    Json::Value neighbor;
    neighbor["id"] = pair.first;
    neighbor["speed"] = pair.second;
    neighbors.append(neighbor);
  }
  vehicleData["neighbors"] = neighbors;
  
  root["vehicles"][std::to_string(m_vehicleId)] = vehicleData;
  
  std::ofstream file("opencv_integration/ns3_results.json");
  if (file.is_open()) {
    Json::StreamWriterBuilder builder;
    std::unique_ptr<Json::StreamWriter> writer(builder.newStreamWriter());
    writer->write(root, &file);
    file.close();
  }
}

// VANET Speed Header Class
class VANETSpeedHeader : public Header
{
public:
  VANETSpeedHeader ();
  virtual ~VANETSpeedHeader ();
  
  void SetVehicleId (uint32_t id);
  uint32_t GetVehicleId (void) const;
  
  void SetSpeed (double speed);
  double GetSpeed (void) const;
  
  void SetPositionX (double x);
  double GetPositionX (void) const;
  
  void SetPositionY (double y);
  double GetPositionY (void) const;
  
  void SetTimestamp (Time timestamp);
  Time GetTimestamp (void) const;
  
  static TypeId GetTypeId (void);
  virtual TypeId GetInstanceTypeId (void) const;
  virtual void Print (std::ostream &os) const;
  virtual void Serialize (Buffer::Iterator start) const;
  virtual uint32_t Deserialize (Buffer::Iterator start);
  virtual uint32_t GetSerializedSize (void) const;

private:
  uint32_t m_vehicleId;
  double m_speed;
  double m_positionX;
  double m_positionY;
  uint64_t m_timestamp;
};

// Main simulation function
int
main (int argc, char *argv[])
{
  uint32_t nVehicles = 10;
  double duration = 60.0;
  bool verbose = false;
  
  CommandLine cmd;
  cmd.AddValue ("nVehicles", "Number of vehicles", nVehicles);
  cmd.AddValue ("time", "Simulation time", duration);
  cmd.AddValue ("verbose", "Enable verbose logging", verbose);
  cmd.Parse (argc, argv);
  
  if (verbose)
    {
      LogComponentEnable ("VANETSpeedSimulation", LOG_LEVEL_INFO);
    }
  
  // Create nodes
  NodeContainer vehicles;
  vehicles.Create (nVehicles);
  
  // Setup WAVE/DSRC communication
  YansWifiChannelHelper channelHelper = YansWifiChannelHelper::Default ();
  YansWavePhyHelper wavePhyHelper = YansWavePhyHelper::Default ();
  wavePhyHelper.SetChannel (channelHelper.Create ());
  
  QosWaveMacHelper waveMacHelper = QosWaveMacHelper::Default ();
  WaveHelper waveHelper = WaveHelper::Default ();
  
  NetDeviceContainer devices = waveHelper.Install (wavePhyHelper, waveMacHelper, vehicles);
  
  // Setup mobility - will be overridden by OpenCV data
  MobilityHelper mobility;
  mobility.SetPositionAllocator ("ns3::GridPositionAllocator",
                                 "MinX", DoubleValue (0.0),
                                 "MinY", DoubleValue (0.0),
                                 "DeltaX", DoubleValue (50.0),
                                 "DeltaY", DoubleValue (50.0),
                                 "GridWidth", UintegerValue (5),
                                 "LayoutType", StringValue ("RowFirst"));
  
  mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
  mobility.Install (vehicles);
  
  // Install Internet stack
  InternetStackHelper internet;
  internet.Install (vehicles);
  
  Ipv4AddressHelper ipv4;
  ipv4.SetBase ("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer interfaces = ipv4.Assign (devices);
  
  // Create VANET applications
  for (uint32_t i = 0; i < nVehicles; ++i)
    {
      Ptr<VANETSpeedApp> app = CreateObject<VANETSpeedApp> ();
      
      TypeId tid = TypeId::LookupByName ("ns3::UdpSocketFactory");
      Ptr<Socket> recvSocket = Socket::CreateSocket (vehicles.Get (i), tid);
      InetSocketAddress local = InetSocketAddress (Ipv4Address::GetAny (), 9);
      recvSocket->Bind (local);
      recvSocket->SetAllowBroadcast (true);
      
      Ptr<Socket> source = Socket::CreateSocket (vehicles.Get (i), tid);
      InetSocketAddress remote = InetSocketAddress (Ipv4Address ("255.255.255.255"), 9);
      source->SetAllowBroadcast (true);
      
      app->Setup (source, remote, 512, 1000, DataRate ("1Mbps"), i);
      vehicles.Get (i)->AddApplication (app);
      app->SetStartTime (Seconds (1.0));
      app->SetStopTime (Seconds (duration));
    }
  
  // Enable tracing
  AsciiTraceHelper ascii;
  wavePhyHelper.EnableAsciiAll (ascii.CreateFileStream ("vanet-speed-simulation.tr"));
  wavePhyHelper.EnablePcapAll ("vanet-speed-simulation");
  
  // Animation
  AnimationInterface anim ("vanet-speed-animation.xml");
  anim.SetMaxPktsPerTraceFile (500000);
  
  // Run simulation
  Simulator::Stop (Seconds (duration));
  Simulator::Run ();
  Simulator::Destroy ();
  
  return 0;
}
