# Smart Semiconductor Manufacturing Using IIoT Architecture

> Real-time Defect Detection with Edge Machine Learning

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![MQTT](https://img.shields.io/badge/MQTT-Protocol-orange.svg)](https://mqtt.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-336791.svg)](https://www.postgresql.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-Educational-green.svg)](LICENSE)

---

## 📋 Project Summary

This project implements an **Industrial IoT system** for semiconductor wafer manufacturing to detect defects in real-time before expensive downstream processing and inspection. The system uses a **5-layer IIoT architecture** with edge-based machine learning (XGBoost) to predict wafer defects with:

- **79.8% Recall** - Catches 67 out of 84 defects
- **69.8% Precision** - 70% of alarms are real defects  
- **<50ms Latency** - Real-time edge inference
- **$2,500/month Savings** - For 10,000 wafers/month facility (rough business estimate)

The solution demonstrates end-to-end data flow from sensor simulation → MQTT messaging → edge ML inference → cloud storage (PostgreSQL) → real-time monitoring dashboard.

**Technologies:** `Python` `MQTT` `XGBoost` `PostgreSQL` `Streamlit` `Edge Computing`

---

## 🏗️ System Architecture

```
![alt text](<Screenshot 2025-12-01 000151.png>)
```

**Data Flow:**  
`Sensor Data → MQTT (JSON) → Edge ML Processing → PostgreSQL → Real-time Dashboard`

---

## 📊 ML Model Performance

**Validation Set:** 844 wafers  
**Model:** XGBoost Classifier  

| Metric | Score | Interpretation |
|:-------|:-----:|:---------------|
| **Recall** | 79.8% | Catches 67 out of 84 defects |
| **Precision** | 69.8% | 70% of alarms are real defects |
| **Accuracy** | 94.5% | 798 out of 844 correct predictions |
| **F1-Score** | 0.744 | Balanced performance metric |

### Confusion Matrix

|  | **Predicted: No Defect** | **Predicted: Defect** |
|:---|:---:|:---:|
| **Actual: No Defect** | 731 (TN) | 29 (FP) |
| **Actual: Defect** | 17 (FN) | 67 (TP) |

- ✅ **True Positives (TP):** 67 - Defects Caught
- ❌ **False Negatives (FN):** 17 - Missed Defects  
- ⚠️ **False Positives (FP):** 29 - False Alarms
- ✅ **True Negatives (TN):** 731 - Good Wafers Identified

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 13 or higher
- MQTT Broker (HiveMQ Cloud or local Mosquitto)

### Installation

#### 1. Clone Repository

```bash
git clone https://github.com/Vishavjit-Khinda/IIOT Wafer Manufacturing.git
cd IIOT Wafer Manufacturing
```

#### 2. Install Dependencies

```bash
pip install pandas numpy scikit-learn xgboost paho-mqtt psycopg2-binary streamlit plotly
```

Or use requirements file:

```bash
pip install -r requirements.txt
```

#### 3. Setup PostgreSQL Database

Create database:

```bash
psql -U postgres
```

```sql
CREATE DATABASE final_project1;
\q
```

Run schema:

```bash
psql -U postgres -d final_project1 -f database_setup.sql
```

#### 4. Configure Credentials

Update **both files** with your PostgreSQL password:

**`edge_gateway.py` (line 15):**

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'final_project1',
    'user': 'postgres',
    'password': 'YOUR_PASSWORD_HERE'  # ← Change this
}
```

**`dashboard.py` (line 30):**

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'final_project1',
    'user': 'postgres',
    'password': 'YOUR_PASSWORD_HERE'  # ← Change this
}
```

Configure MQTT in **both** `device_publisher.py` and `edge_gateway.py`:

```python
MQTT_BROKER = "your-broker.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "your_username"
MQTT_PASSWORD = "your_password"
```

> **Note:** Sign up for free MQTT broker at [HiveMQ Cloud](https://www.hivemq.com/mqtt-cloud-broker/)

---

## 🎮 How to Run

### Run the System (3 Terminals Required)

#### Terminal 1: Start Edge Gateway

```bash
python edge_gateway.py
```

**Expected Output:**
```
Connected to MQTT Broker
Subscribed to topic: factory/line1/lithography
Subscribed to topic: factory/line2/etching
Subscribed to topic: factory/line3/deposition
Waiting for sensor data...
```

#### Terminal 2: Start Sensor Simulator

```bash
python device_publisher.py
```

**Expected Output:**
```
Connected to MQTT Broker
Publishing to factory/line1/lithography
Published: {"wafer_id": "WAF12345", ...}
Publishing to factory/line2/etching
Published: {"wafer_id": "WAF67890", ...}
```

#### Terminal 3: Start Dashboard

```bash
streamlit run dashboard.py
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
Network URL: http://192.168.1.100:8501
```

Open browser: **http://localhost:8501**

---

## 📸 Expected Output

### Dashboard Features

1. **Production Line Status**
   - Real-time Idle/Running state
   - Current wafer ID being processed
   - Last updated timestamp

2. **Active Alerts**
   - Red notification boxes when defects detected
   - Wafer ID and defect probability
   - One-click acknowledgment button

3. **Real-time Parameter Trends**
   - Chamber Temperature
   - Vacuum Pressure
   - Gas Flow Rate
   - Live updating charts

4. **System Statistics**
   - Total wafers processed
   - Defects detected
   - Total alerts generated
   - Acknowledged alerts

### Sample MQTT Payload

```json
{
  "wafer_id": "WAF12345",
  "production_line": "Lithography",
  "chamber_temperature": 245.3,
  "vacuum_pressure": 0.0023,
  "gas_flow_rate": 152.8,
  "rf_power": 485.2,
  "deposition_time": 185.4,
  "etch_rate": 42.7,
  "thickness": 1.85,
  "timestamp": "2025-12-01 19:45:32"
}
```

### Edge Gateway Console Output

```
Received message on factory/line1/lithography
Processing wafer: WAF12345
ML Prediction: DEFECT (Probability: 0.87)
Alert generated for WAF12345
Data stored in database
```

---

## 📁 Project Structure

```
iiot-wafer-manufacturing/
│
├── dashboard.py                # Streamlit dashboard application
├── device_publisher.py         # MQTT publisher (sensor simulator)
├── edge_gateway.py             # MQTT subscriber + ML inference engine
├── trained_model.py            # ML model training script
├── edge_model.pkl              # Trained XGBoost model file
│
├── data_train.csv              # Training dataset (2531 wafers, 60%)
├── data_validation.csv         # Validation dataset (844 wafers, 20%)
├── data_simulation.csv         # Simulation dataset (844 wafers, 20%)
├── wafer_fault_detection.csv   # Complete dataset (4219 wafers)
│
├── database_setup.sql          # PostgreSQL database schema
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 💰 Business Value

### Cost Savings Analysis

**Assumptions:**
- Factory processes 10,000 wafers/month
- Defect rate: 10% (1,000 defects/month)
- Optical inspection cost: $5 per wafer
- Model recall: 79.8%

| Scenario | Calculation | Cost |
|:---------|:------------|:-----|
| **Without IIoT** | 1,000 defects × $5 | $5,000/month |
| **With IIoT - Savings** | 798 defects caught × $5 | $3,990/month |
| **With IIoT - False Alarms** | 300 false alarms × $5 | $1,500/month |
| **Net Savings** | $3,990 - $1,500 | **$2,490/month** |

**Annual ROI: $30,000**

---

## 🔧 Configuration

### Adjust Simulation Speed

**File:** `device_publisher.py` (line 85)

```python
time.sleep(8)  # Default: 8 seconds per wafer

# Options:
time.sleep(3)   # Faster: 3 seconds (realistic)
time.sleep(15)  # Slower: 15 seconds (easier to observe)
```

### Change Dashboard Refresh Rate

**File:** `dashboard.py` (line 45)

```python
refresh_rate = 2  # Default: 2 seconds

# Range: 1-10 seconds
```

---

## 🐛 Troubleshooting

### Database Connection Error

**Problem:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**
1. Verify PostgreSQL is running
2. Check credentials in `edge_gateway.py` and `dashboard.py`
3. Test connection: `psql -U postgres -d final_project1`

### MQTT Connection Failed

**Problem:** `Connection refused` or `Authentication failed`

**Solutions:**
1. Verify broker URL and port
2. Check username and password
3. For HiveMQ Cloud: Verify cluster is active
4. Test with: `mosquitto_sub -h broker-url -t "test" -u username -P password`

### Module Not Found Error

**Problem:** `ModuleNotFoundError: No module named 'paho'`

**Solution:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Dashboard Not Loading

**Problem:** Streamlit shows errors

**Solution:**
```bash
pip install --upgrade streamlit
streamlit cache clear
streamlit run dashboard.py
```

---

## 👥 Contributors

**Group 3**

- Sameerjeet Chhabra
- Vishavjit Singh Khinda
- Jose Moreno-Virgil

**Course:** MFG 598 - Industrial Internet of Things  
**Institution:** Arizona State University  
**Date:** December 2025

---

## 📄 License

This project is developed for educational purposes as part of the MFG 598 course at Arizona State University.

---

## 🙏 Acknowledgments

- **Dataset:** [Kaggle - Semiconductor Wafer Fault Detection](https://www.kaggle.com/datasets/arbazkhan971/semiconductor-wafer-fault-detection)
- **MQTT Broker:** [HiveMQ Cloud](https://www.hivemq.com/)
- **Dashboard Framework:** [Streamlit](https://streamlit.io/)
- **ML Framework:** [XGBoost](https://xgboost.ai/)

---

## 📞 Contact

For questions or collaboration:
- Open an issue on GitHub
- Email: [your-email@asu.edu]

---

<div align="center">

**⭐ If you found this project helpful, please star this repository! ⭐**

Made with ❤️ by Group 3

</div>
