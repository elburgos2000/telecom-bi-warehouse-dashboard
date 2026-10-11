import sqlite3
import random
import csv
import os
from datetime import datetime, timedelta

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(DATA_DIR, "data_export")
os.makedirs(CSV_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "telecom_bi.db")

print("Generando dimensiones y datos maestros...")

# 1. Dim_Agents
agents = [
    (1, "AGT-101", "Brayan Burgos", "Retention VIP", "Bogotá Hub", "Morning", "Carlos Mendoza", "2023-01-15", 1),
    (2, "AGT-102", "Daniela Morales", "L2 Escalations", "Bogotá Hub", "Morning", "Carlos Mendoza", "2023-03-10", 1),
    (3, "AGT-103", "Alejandro Gómez", "Tech Specialist", "Madrid Operational Center", "Afternoon", "Elena Navarro", "2022-11-01", 1),
    (4, "AGT-104", "Sofía Rodríguez", "L1 Support", "Bogotá Hub", "Afternoon", "Carlos Mendoza", "2024-02-01", 1),
    (5, "AGT-105", "Mateo Valencia", "Retention VIP", "Madrid Operational Center", "Morning", "Elena Navarro", "2023-05-18", 1),
    (6, "AGT-106", "Camila Restrepo", "L2 Escalations", "Bogotá Hub", "Night", "Javier Silva", "2023-08-20", 1),
    (7, "AGT-107", "Felipe Torres", "Tech Specialist", "Bogotá Hub", "Morning", "Carlos Mendoza", "2022-09-12", 1),
    (8, "AGT-108", "Valentina Castro", "L1 Support", "Madrid Operational Center", "Afternoon", "Elena Navarro", "2024-04-05", 1),
    (9, "AGT-109", "Sebastián Ortiz", "L1 Support", "Bogotá Hub", "Night", "Javier Silva", "2024-01-10", 1),
    (10, "AGT-110", "Mariana Ríos", "Retention VIP", "Madrid Operational Center", "Morning", "Elena Navarro", "2023-02-28", 1),
]

# 2. Dim_Channels
channels = [
    (1, "CHN-VOICE", "Voice Inbound", 300, 82.5, 0.4500),
    (2, "CHN-CHAT", "Digital Web Chat", 240, 88.0, 0.2200),
    (3, "CHN-WAPP", "WhatsApp Official", 180, 91.5, 0.1500),
    (4, "CHN-ESCAL", "Escalations Desk", 420, 85.0, 0.6500),
]

# 3. Dim_Customer_Segments
segments = [
    (1, "SEG-PRE", "Prepago Standard", 1, 9.50),
    (2, "SEG-POST", "Postpago Ilimitado 5G", 3, 28.00),
    (3, "SEG-FIBRA", "Fibra Óptica 1Gbps + TV", 4, 45.00),
    (4, "SEG-VIP", "VIP Platinum Corporate", 5, 120.00),
]

# 4. Dim_Incident_Categories
categories = [
    (1, "CAT-BILL", "Facturación & Cobranzas", "Medium", "Finance Operations"),
    (2, "CAT-TECH", "Soporte Técnico Fibra / WiFi", "High", "Network NOC"),
    (3, "CAT-PORT", "Portabilidad & Activación", "Medium", "Provisioning"),
    (4, "CAT-ROAM", "Roaming Internacional", "Low", "Carrier Services"),
    (5, "CAT-CHRN", "Retención / Solicitud de Baja", "Critical", "Retention VIP Desk"),
]

# 5. Generar Dim_Date (Últimos 120 días)
start_date = datetime(2026, 6, 1)
date_records = []
dates_lookup = []
for d in range(130):
    cur_date = start_date + timedelta(days=d)
    date_key = int(cur_date.strftime("%Y%m%d"))
    dates_lookup.append((date_key, cur_date))
    date_records.append((
        date_key,
        cur_date.strftime("%Y-%m-%d"),
        cur_date.strftime("%A"),
        cur_date.day,
        cur_date.month,
        cur_date.strftime("%B"),
        (cur_date.month - 1) // 3 + 1,
        cur_date.year,
        1 if cur_date.weekday() >= 5 else 0,
        0
    ))

print(f"Generando 12,000 registros de Fact_Interactions con patrones de telemetría...")
fact_records = []
random.seed(42)

for i in range(1, 12001):
    date_key, cur_date = random.choice(dates_lookup)
    agent = random.choice(agents)
    channel = random.choice(channels)
    segment = random.choice(segments)
    category = random.choice(categories)

    # Hora del contacto simulada
    hour = random.choices(
        [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        weights=[3, 7, 10, 10, 8, 8, 9, 10, 9, 7, 5, 3, 2]
    )[0]
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    contact_dt = cur_date.replace(hour=hour, minute=minute, second=second)

    # Duración AHT basada en canal y categoría
    base_aht = channel[3]
    if category[1] == "CAT-TECH":
        base_aht += 80
    elif category[1] == "CAT-CHRN":
        base_aht += 110
    handling_time = max(60, int(random.gauss(base_aht, 45)))
    hold_time = max(0, int(random.gauss(35, 15))) if random.random() < 0.65 else 0
    queue_wait = max(5, int(random.expovariate(1/40)))

    # FCR Flag
    fcr_prob = channel[4] / 100.0
    if category[1] == "CAT-TECH":
        fcr_prob -= 0.12
    if agent[1] == "AGT-101": # Brayan es Top Performer
        fcr_prob += 0.08
    fcr_flag = 1 if random.random() < fcr_prob else 0

    # CSAT Score (1 to 5)
    if fcr_flag == 1:
        csat = random.choices([4, 5, 3, 2, 1], weights=[45, 45, 7, 2, 1])[0]
    else:
        csat = random.choices([2, 3, 1, 4, 5], weights=[35, 30, 20, 10, 5])[0]

    # Sentiment Score (-1.0 to 1.0)
    sentiment = round((csat - 3.0) / 2.0 + random.uniform(-0.15, 0.15), 3)
    sentiment = max(-1.0, min(1.0, sentiment))

    # SLA Adherence
    sla_flag = 1 if handling_time <= channel[3] + 30 and queue_wait <= 60 else 0

    # Churn Risk
    if category[1] == "CAT-CHRN":
        churn_risk = round(random.uniform(0.60, 0.95), 3)
        retained = 1 if (csat >= 4 or (fcr_flag == 1 and random.random() < 0.8)) else 0
    else:
        churn_risk = round(random.uniform(0.02, 0.25), 3)
        retained = 1

    # Financiero
    cost_usd = round((handling_time / 60.0) * float(channel[5]) + 0.50, 2)
    if retained == 1 and category[1] == "CAT-CHRN":
        retained_rev = round(float(segment[4]) * 12.0, 2) # Valor anual salvado
    else:
        retained_rev = 0.00

    fact_records.append((
        100000 + i,
        date_key,
        agent[0],
        channel[0],
        segment[0],
        category[0],
        contact_dt.strftime("%Y-%m-%d %H:%M:%S"),
        handling_time,
        hold_time,
        queue_wait,
        fcr_flag,
        csat,
        sentiment,
        sla_flag,
        churn_risk,
        retained,
        cost_usd,
        retained_rev
    ))

print("Guardando base de datos SQLite y exportando datasets...")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Crear tablas
cur.execute("""
CREATE TABLE IF NOT EXISTS Dim_Date (
    Date_Key INTEGER PRIMARY KEY,
    Full_Date TEXT NOT NULL,
    Day_Of_Week_Name TEXT NOT NULL,
    Day_Of_Month INTEGER NOT NULL,
    Month_Number INTEGER NOT NULL,
    Month_Name TEXT NOT NULL,
    Quarter_Number INTEGER NOT NULL,
    Year_Number INTEGER NOT NULL,
    Is_Weekend INTEGER NOT NULL,
    Is_Holiday INTEGER NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS Dim_Agents (
    Agent_Key INTEGER PRIMARY KEY,
    Agent_Code TEXT UNIQUE NOT NULL,
    Agent_Name TEXT NOT NULL,
    Tier_Level TEXT NOT NULL,
    Site_Location TEXT NOT NULL,
    Shift_Schedule TEXT NOT NULL,
    Supervisor TEXT NOT NULL,
    Hire_Date TEXT NOT NULL,
    Is_Active INTEGER NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS Dim_Channels (
    Channel_Key INTEGER PRIMARY KEY,
    Channel_Code TEXT UNIQUE NOT NULL,
    Channel_Name TEXT NOT NULL,
    Target_AHT_Seconds INTEGER NOT NULL,
    Target_FCR_Pct REAL NOT NULL,
    Cost_Per_Minute_USD REAL NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS Dim_Customer_Segments (
    Segment_Key INTEGER PRIMARY KEY,
    Segment_Code TEXT UNIQUE NOT NULL,
    Segment_Name TEXT NOT NULL,
    Priority_Score INTEGER NOT NULL,
    Average_ARPU_USD REAL NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS Dim_Incident_Categories (
    Category_Key INTEGER PRIMARY KEY,
    Category_Code TEXT UNIQUE NOT NULL,
    Category_Name TEXT NOT NULL,
    Severity_Level TEXT NOT NULL,
    Escalation_Department TEXT NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS Fact_Interactions (
    Interaction_ID INTEGER PRIMARY KEY,
    Date_Key INTEGER NOT NULL,
    Agent_Key INTEGER NOT NULL,
    Channel_Key INTEGER NOT NULL,
    Segment_Key INTEGER NOT NULL,
    Category_Key INTEGER NOT NULL,
    Contact_Timestamp TEXT NOT NULL,
    Handling_Time_Seconds INTEGER NOT NULL,
    Hold_Time_Seconds INTEGER NOT NULL,
    Queue_Wait_Seconds INTEGER NOT NULL,
    FCR_Flag INTEGER NOT NULL,
    CSAT_Score INTEGER NOT NULL,
    Sentiment_Score REAL NOT NULL,
    SLA_Adherence_Flag INTEGER NOT NULL,
    Churn_Risk_Prob REAL NOT NULL,
    Customer_Retained_Flag INTEGER NOT NULL,
    Operational_Cost_USD REAL NOT NULL,
    Retained_Revenue_USD REAL NOT NULL,
    FOREIGN KEY(Date_Key) REFERENCES Dim_Date(Date_Key),
    FOREIGN KEY(Agent_Key) REFERENCES Dim_Agents(Agent_Key),
    FOREIGN KEY(Channel_Key) REFERENCES Dim_Channels(Channel_Key),
    FOREIGN KEY(Segment_Key) REFERENCES Dim_Customer_Segments(Segment_Key),
    FOREIGN KEY(Category_Key) REFERENCES Dim_Incident_Categories(Category_Key)
)
""")

# Insertar datos
cur.execute("DELETE FROM Dim_Date")
cur.executemany("INSERT INTO Dim_Date VALUES (?,?,?,?,?,?,?,?,?,?)", date_records)

cur.execute("DELETE FROM Dim_Agents")
cur.executemany("INSERT INTO Dim_Agents VALUES (?,?,?,?,?,?,?,?,?)", agents)

cur.execute("DELETE FROM Dim_Channels")
cur.executemany("INSERT INTO Dim_Channels VALUES (?,?,?,?,?,?)", channels)

cur.execute("DELETE FROM Dim_Customer_Segments")
cur.executemany("INSERT INTO Dim_Customer_Segments VALUES (?,?,?,?,?)", segments)

cur.execute("DELETE FROM Dim_Incident_Categories")
cur.executemany("INSERT INTO Dim_Incident_Categories VALUES (?,?,?,?,?)", categories)

cur.execute("DELETE FROM Fact_Interactions")
cur.executemany("INSERT INTO Fact_Interactions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", fact_records)

conn.commit()
conn.close()

# Exportar a CSV para Power BI / Excel / SSMS
def export_csv(filename, headers, rows):
    path = os.path.join(CSV_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"Exportado: {filename} ({len(rows)} filas)")

export_csv("Dim_Date.csv", ["Date_Key", "Full_Date", "Day_Of_Week_Name", "Day_Of_Month", "Month_Number", "Month_Name", "Quarter_Number", "Year_Number", "Is_Weekend", "Is_Holiday"], date_records)
export_csv("Dim_Agents.csv", ["Agent_Key", "Agent_Code", "Agent_Name", "Tier_Level", "Site_Location", "Shift_Schedule", "Supervisor", "Hire_Date", "Is_Active"], agents)
export_csv("Dim_Channels.csv", ["Channel_Key", "Channel_Code", "Channel_Name", "Target_AHT_Seconds", "Target_FCR_Pct", "Cost_Per_Minute_USD"], channels)
export_csv("Dim_Customer_Segments.csv", ["Segment_Key", "Segment_Code", "Segment_Name", "Priority_Score", "Average_ARPU_USD"], segments)
export_csv("Dim_Incident_Categories.csv", ["Category_Key", "Category_Code", "Category_Name", "Severity_Level", "Escalation_Department"], categories)
export_csv("Fact_Interactions.csv", ["Interaction_ID", "Date_Key", "Agent_Key", "Channel_Key", "Segment_Key", "Category_Key", "Contact_Timestamp", "Handling_Time_Seconds", "Hold_Time_Seconds", "Queue_Wait_Seconds", "FCR_Flag", "CSAT_Score", "Sentiment_Score", "SLA_Adherence_Flag", "Churn_Risk_Prob", "Customer_Retained_Flag", "Operational_Cost_USD", "Retained_Revenue_USD"], fact_records)

print(f"Base de datos SQLite generada con éxito en: {DB_PATH}")
