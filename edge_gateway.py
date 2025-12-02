"""
Layer 3: MQTT Subscriber - Edge Layer (Gateway) + Cloud Storage
Receives sensor data, performs ML predictions, stores to database
"""
import json
import pickle
import pandas as pd
import numpy as np
import paho.mqtt.client as mqtt
import psycopg2
from datetime import datetime
import time

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPICS = [
    'factory/line1/lithography',
    'factory/line2/etching',
    'factory/line3/deposition'
]

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'Your database name',
    'user': 'postgres',
    'password': 'Your database password'  
}

class EdgeGateway:
    def __init__(self):
        # Load ML model (Edge Layer)
        print("🔧 Loading Edge ML Model...")
        with open('edge_model.pkl', 'rb') as f:
            self.model_package = pickle.load(f)
        
        self.model = self.model_package['model']
        self.scaler = self.model_package['scaler']
        self.label_encoders = self.model_package['label_encoders']
        self.feature_names = self.model_package['feature_names']
        self.threshold = self.model_package['threshold']
        
        print(f"✅ Model loaded (Threshold: {self.threshold})")
        
        # Database connection
        self.db_conn = None
        self.connect_database()
        
        # MQTT client
        self.client = mqtt.Client(client_id="edge_gateway")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'defects_detected': 0,
            'by_line': {
                'Lithography': {'total': 0, 'defects': 0},
                'Etching': {'total': 0, 'defects': 0},
                'Deposition': {'total': 0, 'defects': 0}
            }
        }
    
    def connect_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(**DB_CONFIG)
            print("✅ Connected to PostgreSQL database")
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            self.db_conn = None
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to MQTT Broker")
            # Subscribe to all production line topics
            for topic in MQTT_TOPICS:
                client.subscribe(topic)
                print(f"📡 Subscribed to: {topic}")
        else:
            print(f"❌ Connection failed with code {rc}")
    
    def predict_defect(self, sensor_data):
        """Perform ML prediction on sensor data (Edge Processing)"""
        try:
            # Prepare features in correct order
            features = {}
            
            # Numerical features
            features['Chamber_Temperature'] = sensor_data['chamber_temperature']
            features['Gas_Flow_Rate'] = sensor_data['gas_flow_rate']
            features['RF_Power'] = sensor_data['rf_power']
            features['Etch_Depth'] = sensor_data['etch_depth']
            features['Rotation_Speed'] = sensor_data['rotation_speed']
            features['Vacuum_Pressure'] = sensor_data['vacuum_pressure']
            features['Stage_Alignment_Error'] = sensor_data['stage_alignment_error']
            features['Vibration_Level'] = sensor_data['vibration_level']
            features['UV_Exposure_Intensity'] = sensor_data['uv_exposure_intensity']
            features['Particle_Count'] = sensor_data['particle_count']
            
            # Categorical features (encode)
            tool_type = sensor_data['production_line']  # Lithography/Etching/Deposition
            features['Tool_Type'] = self.label_encoders['Tool_Type'].transform([tool_type])[0]
            
            join_status = sensor_data['join_status']
            features['Join_Status'] = self.label_encoders['Join_Status'].transform([join_status])[0]
            
            # Create feature vector
            X = pd.DataFrame([features])[self.feature_names]
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Predict
            proba = self.model.predict_proba(X_scaled)[0, 1]
            prediction = 1 if proba >= self.threshold else 0
            
            return prediction, proba
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return 0, 0.0
    
    def store_to_database(self, sensor_data, prediction, probability):
        """Store sensor data and prediction to database (Cloud Layer)"""
        if not self.db_conn:
            return
        
        try:
            cursor = self.db_conn.cursor()
            
            # Convert numpy types to Python native types for PostgreSQL
            prediction = int(prediction)  # numpy.int64 -> int
            probability = float(probability)  # numpy.float32 -> float
            
            # Insert sensor data with prediction
            cursor.execute("""
                INSERT INTO sensor_data (
                    process_id, timestamp, production_line, wafer_id,
                    chamber_temperature, gas_flow_rate, rf_power, etch_depth,
                    rotation_speed, vacuum_pressure, stage_alignment_error,
                    vibration_level, uv_exposure_intensity, particle_count,
                    join_status, predicted_defect, defect_probability, actual_defect
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                sensor_data['process_id'],
                sensor_data['timestamp'],
                sensor_data['production_line'],
                sensor_data['wafer_id'],
                float(sensor_data['chamber_temperature']),
                float(sensor_data['gas_flow_rate']),
                float(sensor_data['rf_power']),
                float(sensor_data['etch_depth']),
                float(sensor_data['rotation_speed']),
                float(sensor_data['vacuum_pressure']),
                float(sensor_data['stage_alignment_error']),
                float(sensor_data['vibration_level']),
                float(sensor_data['uv_exposure_intensity']),
                int(sensor_data['particle_count']),
                sensor_data['join_status'],
                int(prediction),  # Convert numpy int to Python int
                float(probability),  # Convert numpy float32 to Python float
                int(sensor_data['actual_defect'])
            ))
            
            # Update production line status (always Running - defects don't stop production)
            status = 'Running'
            cursor.execute("""
                UPDATE production_lines 
                SET status = %s, current_wafer_id = %s, last_updated = CURRENT_TIMESTAMP
                WHERE line_name = %s
            """, (status, sensor_data['wafer_id'], sensor_data['production_line']))
            
            # Create alert if defect detected
            if prediction == 1:
                cursor.execute("""
                    INSERT INTO alerts (
                        production_line, wafer_id, alert_message, defect_probability
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    sensor_data['production_line'],
                    sensor_data['wafer_id'],
                    f"Defect detected on {sensor_data['production_line']} line",
                    float(probability)  # Convert numpy float32 to Python float
                ))
            
            self.db_conn.commit()
            cursor.close()
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            self.db_conn.rollback()
    
    def on_message(self, client, userdata, msg):
        """Process incoming MQTT messages"""
        try:
            # Parse sensor data
            sensor_data = json.loads(msg.payload.decode())
            
            # Perform edge ML prediction
            prediction, probability = self.predict_defect(sensor_data)
            
            # Store to cloud database
            self.store_to_database(sensor_data, prediction, probability)
            
            # Update statistics
            line = sensor_data['production_line']
            self.stats['total_processed'] += 1
            self.stats['by_line'][line]['total'] += 1
            
            if prediction == 1:
                self.stats['defects_detected'] += 1
                self.stats['by_line'][line]['defects'] += 1
            
            # Log processing
            status = "🔴 DEFECT" if prediction == 1 else "🟢 OK"
            print(f"[{self.stats['total_processed']:4d}] {line:15s} | "
                  f"Wafer: {sensor_data['wafer_id']} | "
                  f"Prob: {probability:.3f} | {status}")
            
        except Exception as e:
            print(f"❌ Message processing error: {e}")
    
    def run(self):
        """Start edge gateway"""
        print("\n" + "="*60)
        print("EDGE GATEWAY STARTED")
        print("="*60)
        print("Listening for sensor data from production lines...")
        print("Press Ctrl+C to stop\n")
        
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\n⏹️  Stopping edge gateway...")
        finally:
            self.print_statistics()
            self.client.disconnect()
            if self.db_conn:
                self.db_conn.close()
            print("✅ Edge gateway stopped")
    
    def print_statistics(self):
        """Print processing statistics"""
        print("\n" + "="*60)
        print("PROCESSING STATISTICS")
        print("="*60)
        print(f"Total processed: {self.stats['total_processed']}")
        print(f"Defects detected: {self.stats['defects_detected']}")
        print("\nBy Production Line:")
        for line, stats in self.stats['by_line'].items():
            if stats['total'] > 0:
                rate = (stats['defects'] / stats['total']) * 100
                print(f"  {line:15s}: {stats['total']:4d} wafers, "
                      f"{stats['defects']:3d} defects ({rate:.1f}%)")

def main():
    print("="*60)
    print("EDGE LAYER: GATEWAY + ML PREDICTION ENGINE")
    print("="*60)
    
    gateway = EdgeGateway()
    gateway.run()

if __name__ == "__main__":
    main()