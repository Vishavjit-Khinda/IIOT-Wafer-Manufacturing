"""
Layer 1: MQTT Publisher - Physical Device Layer Simulation
Publishes sensor data from wafer datset to MQTT broker
Simulates three production lines based on Tool_Type
"""
import pandas as pd
import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime

# MQTT Configuration (HiveMQ Public Broker)
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPICS = {
    'Lithography': 'factory/line1/lithography',
    'Etching': 'factory/line2/etching',
    'Deposition': 'factory/line3/deposition'
}

# Publishing configuration
PUBLISH_INTERVAL = 8 # seconds between messages 

class WaferSensorSimulator:
    def __init__(self):
        self.client = mqtt.Client(client_id="wafer_sensor_simulator")
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to MQTT Broker (HiveMQ)")
            self.connected = True
        else:
            print(f"❌ Failed to connect, return code {rc}")
            
    def on_publish(self, client, userdata, mid):
        pass  # Silent publishing
        
    def connect_broker(self):
        """Connect to MQTT broker"""
        print("🔌 Connecting to HiveMQ broker...")
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            start = time.time()
            while not self.connected and (time.time() - start) < timeout:
                time.sleep(0.1)
                
            if not self.connected:
                print("❌ Connection timeout")
                return False
            return True
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def publish_sensor_data(self, row, production_line):
        """Publish single sensor reading to MQTT"""
        topic = MQTT_TOPICS[production_line]
        
        # Prepare sensor data payload
        payload = {
            'process_id': row['Process_ID'],
            'timestamp': row['Timestamp'].isoformat() if hasattr(row['Timestamp'], 'isoformat') else str(row['Timestamp']),
            'production_line': production_line,
            'wafer_id': row['Wafer_ID'],
            'chamber_temperature': float(row['Chamber_Temperature']),
            'gas_flow_rate': float(row['Gas_Flow_Rate']),
            'rf_power': float(row['RF_Power']),
            'etch_depth': float(row['Etch_Depth']),
            'rotation_speed': float(row['Rotation_Speed']),
            'vacuum_pressure': float(row['Vacuum_Pressure']),
            'stage_alignment_error': float(row['Stage_Alignment_Error']),
            'vibration_level': float(row['Vibration_Level']),
            'uv_exposure_intensity': float(row['UV_Exposure_Intensity']),
            'particle_count': int(row['Particle_Count']),
            'join_status': row['Join_Status'],
            'actual_defect': int(row['Defect'])  
        }
        
        # Publish to MQTT
        result = self.client.publish(topic, json.dumps(payload), qos=1)
        
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    
    def run_simulation(self):
        """Run continuous simulation from dataset"""
        # Load simulation data
        sim_df = pd.read_csv('data_simulation.csv')
        sim_df['Timestamp'] = pd.to_datetime(sim_df['Timestamp'])
        
        # Group by Tool_Type (production line)
        line_data = {
            'Lithography': sim_df[sim_df['Tool_Type'] == 'Lithography'].reset_index(drop=True),
            'Etching': sim_df[sim_df['Tool_Type'] == 'Etching'].reset_index(drop=True),
            'Deposition': sim_df[sim_df['Tool_Type'] == 'Deposition'].reset_index(drop=True)
        }
        
        print("\n" + "="*60)
        print("SIMULATION DATA LOADED")
        print("="*60)
        for line, data in line_data.items():
            defects = data['Defect'].sum()
            print(f"{line:15s}: {len(data):4d} wafers, {defects:3d} defects")
        
        print("\n" + "="*60)
        print("STARTING SENSOR DATA SIMULATION")
        print("="*60)
        print(f"Publishing to MQTT topics:")
        for line, topic in MQTT_TOPICS.items():
            print(f"  {line:15s} → {topic}")
        print(f"\nPublish interval: {PUBLISH_INTERVAL} seconds")
        print("Press Ctrl+C to stop\n")
        
        # Track indices for each production line
        indices = {line: 0 for line in line_data.keys()}
        max_index = max(len(data) for data in line_data.values())
        
        try:
            msg_count = 0
            while any(idx < len(line_data[line]) for line, idx in indices.items()):
                # Publish data from each active production line
                for line, idx in indices.items():
                    if idx < len(line_data[line]):
                        row = line_data[line].iloc[idx]
                        
                        if self.publish_sensor_data(row, line):
                            msg_count += 1
                            wafer_id = row['Wafer_ID']
                            print(f"[{msg_count:4d}] {line:15s} | Wafer: {wafer_id}")
                        
                        indices[line] += 1
                
                time.sleep(PUBLISH_INTERVAL)
            
            print("\n" + "="*60)
            print(f"✅ Device Simulation complete! Published {msg_count} messages") 
            print("="*60)
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Device Simulation stopped by user")
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            print("🔌 Disconnected from MQTT broker")

def main():
    print("="*60)
    print("PHYSICAL DEVICE LAYER: SENSOR SIMULATOR")
    print("="*60)
    
    simulator = WaferSensorSimulator()
    
    if simulator.connect_broker():
        simulator.run_simulation()
    else:
        print("❌ Failed to start device simulation")

if __name__ == "__main__":
    main()