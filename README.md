# 📊 Enterprise Telecom BI Warehouse & Executive Analytics Dashboard

[![SQL Server](https://img.shields.io/badge/Database-Microsoft%20SQL%20Server%20%7C%20T--SQL-CC292B?style=for-the-badge&logo=microsoftsqlserver&logoColor=white)](https://microsoft.com/sql-server)
[![DuckDB](https://img.shields.io/badge/OLAP-DuckDB%20Engine-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)](https://duckdb.org)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Chart.js](https://img.shields.io/badge/Visualization-Chart.js%20%7C%20Tailwind-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://chartjs.org)

Plataforma analítica empresarial de Inteligencia de Negocios (BI) para operaciones de Contact Center / BPO de Telecomunicaciones. Implementa un modelo dimensional **Star Schema** (metodología Kimball) en T-SQL (Microsoft SQL Server), almacenamiento analítico en DuckDB/SQLite, y un Dashboard Ejecutivo interactivo en tiempo real con consola de consultas SQL en el navegador.

---

## 🏛️ Modelo Dimensional (Star Schema)

```mermaid
erDiagram
    Dim_Date ||--o{ Fact_Interactions : "Date_Key"
    Dim_Agents ||--o{ Fact_Interactions : "Agent_Key"
    Dim_Channels ||--o{ Fact_Interactions : "Channel_Key"
    Dim_Customer_Segments ||--o{ Fact_Interactions : "Segment_Key"
    Dim_Incident_Categories ||--o{ Fact_Interactions : "Category_Key"

    Dim_Date {
        int Date_Key PK
        date Full_Date
        string Month_Name
        int Year_Number
        bit Is_Weekend
    }

    Dim_Agents {
        int Agent_Key PK
        string Agent_Code UK
        string Agent_Name
        string Tier_Level
        string Site_Location
    }

    Dim_Channels {
        int Channel_Key PK
        string Channel_Name
        int Target_AHT_Seconds
        decimal Target_FCR_Pct
        decimal Cost_Per_Minute_USD
    }

    Dim_Customer_Segments {
        int Segment_Key PK
        string Segment_Name
        int Priority_Score
        decimal Average_ARPU_USD
    }

    Dim_Incident_Categories {
        int Category_Key PK
        string Category_Name
        string Severity_Level
        string Escalation_Department
    }

    Fact_Interactions {
        bigint Interaction_ID PK
        int Date_Key FK
        int Agent_Key FK
        int Channel_Key FK
        int Segment_Key FK
        int Category_Key FK
        datetime Contact_Timestamp
        int Handling_Time_Seconds
        bit FCR_Flag
        int CSAT_Score
        decimal Sentiment_Score
        bit SLA_Adherence_Flag
        decimal Churn_Risk_Prob
        decimal Operational_Cost_USD
        decimal Retained_Revenue_USD
    }
```

---

## ✨ Características de la Plataforma

- **⚡ Arquitectura Star Schema de Alto Rendimiento:** DDL nativo para Microsoft SQL Server (`schema_sql_server.sql`) con llaves foráneas, índices agrupados/no agrupados, vistas precalculadas (`vw_Executive_KPIs`, `vw_Agent_Performance`, `vw_Channel_Efficiency`) y procedimientos almacenados.
- **🦆 Doble Almacén Analítico (DuckDB & SQLite):** Incluye base de datos columnar en DuckDB (`telecom_bi.duckdb`) para agregaciones OLAP sub-segundo y SQLite (`telecom_bi.db`) para portabilidad inmediata.
- **🖥️ Dashboard Ejecutivo Web:**
  - **KPIs en Vivo:** Volumen total de interacciones, AHT promedio, FCR %, CSAT Score y valor económico retenido de Churn.
  - **Filtros Dinámicos:** Segmentación instantánea por Canal (Voz, Chat, WhatsApp, Escalaciones) y Segmento de Cliente (VIP, Fibra, Postpago, Prepago).
  - **Scorecard de Agentes:** Ranking de productividad, adherencia a SLA y clasificación automática (*Top Performer / Coaching Required*).
  - **Consola SQL en el Navegador:** Ejecución interactiva de sentencias analíticas `SELECT` con visualización tabular instantánea.
- **📂 Exportación Power BI Ready:** Carpeta `data_export/` con archivos CSV estructurados (`Fact_Interactions.csv`, `Dim_*.csv`) listos para importar a Power BI Desktop, Tableau o Excel.

---

## 🚀 Puesta en Marcha Rápida

### 1. Clonar el repositorio
```bash
git clone https://github.com/elburgos2000/telecom-bi-warehouse-dashboard.git
cd telecom-bi-warehouse-dashboard
```

### 2. Generar el Warehouse y los datos maestros (12,000 interacciones)
```bash
python build_and_seed_warehouse.py
```

### 3. Iniciar el Dashboard Ejecutivo y la API Analítica
```bash
python server.py
```
Abrir en el navegador: [http://localhost:8085](http://localhost:8085)

---

## 🗄️ Despliegue en Microsoft SQL Server

Para desplegar en una instancia de SQL Server (Local, Azure SQL o Docker):
```bash
sqlcmd -S localhost -U sa -P 'TuPasswordFuerte123' -i schema_sql_server.sql
```
O abrir y ejecutar `schema_sql_server.sql` en **SQL Server Management Studio (SSMS)** o **Azure Data Studio**.

---

## 👨‍💻 Autor

**Brayan Burgos Palomino**  
- **Rol:** Software Engineer & BI Analyst  
- **GitHub:** [@elburgos2000](https://github.com/elburgos2000)  
- **Email:** [motocrossloco@gmail.com](mailto:motocrossloco@gmail.com)  
- **Ubicación:** Bogotá, Colombia  
