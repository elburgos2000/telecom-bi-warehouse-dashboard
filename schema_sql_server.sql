-- ============================================================================
-- PROYECTO: Enterprise Telecom BPO Data Warehouse & Analytics Engine
-- ARQUITECTURA: Kimball Star Schema (T-SQL / Microsoft SQL Server)
-- AUTOR: Brayan Burgos Palomino | BI Analyst & Software Engineer
-- DESCRIPCIÓN: Modelo analítico para operaciones BPO de telecomunicaciones
-- ============================================================================

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'Telecom_BI_Warehouse')
BEGIN
    CREATE DATABASE Telecom_BI_Warehouse;
END
GO

USE Telecom_BI_Warehouse;
GO

-- ----------------------------------------------------------------------------
-- 1. TABLAS DE DIMENSIONES (Star Schema)
-- ----------------------------------------------------------------------------

-- Dimensión Fecha (Dim_Date)
IF OBJECT_ID('dbo.Dim_Date', 'U') IS NOT NULL DROP TABLE dbo.Dim_Date;
CREATE TABLE dbo.Dim_Date (
    Date_Key INT PRIMARY KEY,               -- Formato YYYYMMDD
    Full_Date DATE NOT NULL,
    Day_Of_Week_Name NVARCHAR(20) NOT NULL,
    Day_Of_Month INT NOT NULL,
    Month_Number INT NOT NULL,
    Month_Name NVARCHAR(20) NOT NULL,
    Quarter_Number INT NOT NULL,
    Year_Number INT NOT NULL,
    Is_Weekend BIT NOT NULL,
    Is_Holiday BIT NOT NULL
);
GO

-- Dimensión Agentes / Operadores (Dim_Agents)
IF OBJECT_ID('dbo.Dim_Agents', 'U') IS NOT NULL DROP TABLE dbo.Dim_Agents;
CREATE TABLE dbo.Dim_Agents (
    Agent_Key INT IDENTITY(1,1) PRIMARY KEY,
    Agent_Code NVARCHAR(20) UNIQUE NOT NULL,
    Agent_Name NVARCHAR(100) NOT NULL,
    Tier_Level NVARCHAR(30) NOT NULL,       -- L1 Support, L2 Escalations, Tech Specialist, Retention VIP
    Site_Location NVARCHAR(50) NOT NULL,    -- Bogotá Hub, Madrid Operational Center
    Shift_Schedule NVARCHAR(30) NOT NULL,   -- Morning, Afternoon, Night
    Supervisor NVARCHAR(100) NOT NULL,
    Hire_Date DATE NOT NULL,
    Is_Active BIT DEFAULT 1 NOT NULL
);
GO

-- Dimensión Canales de Atención (Dim_Channels)
IF OBJECT_ID('dbo.Dim_Channels', 'U') IS NOT NULL DROP TABLE dbo.Dim_Channels;
CREATE TABLE dbo.Dim_Channels (
    Channel_Key INT IDENTITY(1,1) PRIMARY KEY,
    Channel_Code NVARCHAR(20) UNIQUE NOT NULL,
    Channel_Name NVARCHAR(50) NOT NULL,     -- Voice Inbound, Digital Chat, WhatsApp Official, Email Ticket
    Target_AHT_Seconds INT NOT NULL,        -- SLA AHT meta
    Target_FCR_Pct DECIMAL(5,2) NOT NULL,   -- SLA FCR meta %
    Cost_Per_Minute_USD DECIMAL(8,4) NOT NULL
);
GO

-- Dimensión Segmentos de Cliente (Dim_Customer_Segments)
IF OBJECT_ID('dbo.Dim_Customer_Segments', 'U') IS NOT NULL DROP TABLE dbo.Dim_Customer_Segments;
CREATE TABLE dbo.Dim_Customer_Segments (
    Segment_Key INT IDENTITY(1,1) PRIMARY KEY,
    Segment_Code NVARCHAR(20) UNIQUE NOT NULL,
    Segment_Name NVARCHAR(50) NOT NULL,     -- Prepago Standard, Postpago Ilimitado, Fibra Óptica 1Gbps, VIP Platinum
    Priority_Score INT NOT NULL,            -- 1 (Bajo) a 5 (Crítico VIP)
    Average_ARPU_USD DECIMAL(10,2) NOT NULL
);
GO

-- Dimensión Categorías de Incidencia (Dim_Incident_Categories)
IF OBJECT_ID('dbo.Dim_Incident_Categories', 'U') IS NOT NULL DROP TABLE dbo.Dim_Incident_Categories;
CREATE TABLE dbo.Dim_Incident_Categories (
    Category_Key INT IDENTITY(1,1) PRIMARY KEY,
    Category_Code NVARCHAR(30) UNIQUE NOT NULL,
    Category_Name NVARCHAR(100) NOT NULL,   -- Facturación, Falla Técnica Fibra, Portabilidad, Roaming, Retención Churn
    Severity_Level NVARCHAR(20) NOT NULL,   -- Low, Medium, High, Critical
    Escalation_Department NVARCHAR(50) NOT NULL
);
GO

-- ----------------------------------------------------------------------------
-- 2. TABLA DE HECHOS (Fact Table)
-- ----------------------------------------------------------------------------

IF OBJECT_ID('dbo.Fact_Interactions', 'U') IS NOT NULL DROP TABLE dbo.Fact_Interactions;
CREATE TABLE dbo.Fact_Interactions (
    Interaction_ID BIGINT IDENTITY(100000,1) PRIMARY KEY,
    Date_Key INT NOT NULL FOREIGN KEY REFERENCES dbo.Dim_Date(Date_Key),
    Agent_Key INT NOT NULL FOREIGN KEY REFERENCES dbo.Dim_Agents(Agent_Key),
    Channel_Key INT NOT NULL FOREIGN KEY REFERENCES dbo.Dim_Channels(Channel_Key),
    Segment_Key INT NOT NULL FOREIGN KEY REFERENCES dbo.Dim_Customer_Segments(Segment_Key),
    Category_Key INT NOT NULL FOREIGN KEY REFERENCES dbo.Dim_Incident_Categories(Category_Key),
    
    -- Métricas Operacionales
    Contact_Timestamp DATETIME2 NOT NULL,
    Handling_Time_Seconds INT NOT NULL,     -- AHT
    Hold_Time_Seconds INT NOT NULL,
    Queue_Wait_Seconds INT NOT NULL,
    
    -- Calidad & Satisfacción
    FCR_Flag BIT NOT NULL,                  -- First Contact Resolution (1: Resuelto en primer contacto, 0: Reabierto)
    CSAT_Score INT NOT NULL CHECK (CSAT_Score BETWEEN 1 AND 5),
    Sentiment_Score DECIMAL(4,3) NOT NULL,  -- Rango [-1.000, 1.000] analizado por NLP
    SLA_Adherence_Flag BIT NOT NULL,        -- 1: Dentro de SLA, 0: Incumplido
    
    -- Impacto de Negocio
    Churn_Risk_Prob DECIMAL(4,3) NOT NULL,  -- Probabilidad predictiva de baja
    Customer_Retained_Flag BIT NOT NULL,
    Operational_Cost_USD DECIMAL(10,2) NOT NULL,
    Retained_Revenue_USD DECIMAL(10,2) NOT NULL,

    -- Índices
    INDEX IX_Fact_Date (Date_Key),
    INDEX IX_Fact_Agent (Agent_Key),
    INDEX IX_Fact_Channel (Channel_Key),
    INDEX IX_Fact_Category (Category_Key)
);
GO

-- ----------------------------------------------------------------------------
-- 3. VISTAS ANALÍTICAS PARA REPORTES & DASHBOARDS
-- ----------------------------------------------------------------------------

-- Vista Ejecutiva de KPIs Globales
CREATE OR ALTER VIEW dbo.vw_Executive_KPIs AS
SELECT 
    COUNT(f.Interaction_ID) AS Total_Interactions,
    AVG(f.Handling_Time_Seconds) AS Avg_AHT_Seconds,
    CAST(SUM(CASE WHEN f.FCR_Flag = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(f.Interaction_ID) AS DECIMAL(5,2)) AS FCR_Percentage,
    CAST(AVG(CAST(f.CSAT_Score AS DECIMAL(4,2))) AS DECIMAL(4,2)) AS Avg_CSAT_Score,
    CAST(AVG(f.Sentiment_Score) AS DECIMAL(4,3)) AS Avg_Sentiment_Score,
    CAST(SUM(CASE WHEN f.SLA_Adherence_Flag = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(f.Interaction_ID) AS DECIMAL(5,2)) AS SLA_Adherence_Pct,
    SUM(f.Retained_Revenue_USD) AS Total_Retained_Revenue_USD,
    SUM(f.Operational_Cost_USD) AS Total_Operational_Cost_USD,
    SUM(f.Retained_Revenue_USD) - SUM(f.Operational_Cost_USD) AS Net_Operational_ROI_USD
FROM dbo.Fact_Interactions f;
GO

-- Vista de Scorecard de Agentes
CREATE OR ALTER VIEW dbo.vw_Agent_Performance AS
SELECT 
    a.Agent_Code,
    a.Agent_Name,
    a.Tier_Level,
    a.Site_Location,
    COUNT(f.Interaction_ID) AS Total_Handled,
    AVG(f.Handling_Time_Seconds) AS Avg_AHT,
    CAST(SUM(CASE WHEN f.FCR_Flag = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(f.Interaction_ID) AS DECIMAL(5,2)) AS FCR_Rate,
    CAST(AVG(CAST(f.CSAT_Score AS DECIMAL(4,2))) AS DECIMAL(4,2)) AS Avg_CSAT,
    SUM(f.Retained_Revenue_USD) AS Value_Protected_USD,
    CASE 
        WHEN AVG(CAST(f.CSAT_Score AS DECIMAL(4,2))) >= 4.5 AND SUM(CASE WHEN f.FCR_Flag = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(f.Interaction_ID) >= 85.0 THEN 'Top Performer (Champion)'
        WHEN AVG(CAST(f.CSAT_Score AS DECIMAL(4,2))) >= 4.0 THEN 'Solid Contributor'
        ELSE 'Coaching Required'
    END AS Performance_Tier
FROM dbo.Fact_Interactions f
JOIN dbo.Dim_Agents a ON f.Agent_Key = a.Agent_Key
GROUP BY a.Agent_Code, a.Agent_Name, a.Tier_Level, a.Site_Location;
GO

-- Vista de Eficiencia por Canal
CREATE OR ALTER VIEW dbo.vw_Channel_Efficiency AS
SELECT 
    c.Channel_Name,
    COUNT(f.Interaction_ID) AS Volume,
    AVG(f.Handling_Time_Seconds) AS Avg_AHT,
    c.Target_AHT_Seconds AS SLA_Target_AHT,
    CAST(SUM(CASE WHEN f.FCR_Flag = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(f.Interaction_ID) AS DECIMAL(5,2)) AS Actual_FCR_Pct,
    c.Target_FCR_Pct AS Target_FCR_Pct,
    SUM(f.Operational_Cost_USD) AS Channel_Cost_USD,
    CAST(SUM(f.Operational_Cost_USD) / COUNT(f.Interaction_ID) AS DECIMAL(8,2)) AS Cost_Per_Contact_USD
FROM dbo.Fact_Interactions f
JOIN dbo.Dim_Channels c ON f.Channel_Key = c.Channel_Key
GROUP BY c.Channel_Name, c.Target_AHT_Seconds, c.Target_FCR_Pct;
GO

-- ----------------------------------------------------------------------------
-- 4. PROCEDIMIENTOS ALMACENADOS (Stored Procedures)
-- ----------------------------------------------------------------------------

CREATE OR ALTER PROCEDURE dbo.usp_GetExecutiveSummary
    @StartDate DATE,
    @EndDate DATE,
    @ChannelCode NVARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        d.Year_Number,
        d.Month_Name,
        c.Channel_Name,
        COUNT(f.Interaction_ID) AS Interactions,
        AVG(f.Handling_Time_Seconds) AS AHT_Seconds,
        CAST(SUM(CASE WHEN f.FCR_Flag = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(f.Interaction_ID) AS DECIMAL(5,2)) AS FCR_Pct,
        CAST(AVG(CAST(f.CSAT_Score AS DECIMAL(4,2))) AS DECIMAL(4,2)) AS CSAT,
        SUM(f.Retained_Revenue_USD) AS Revenue_Saved_USD
    FROM dbo.Fact_Interactions f
    JOIN dbo.Dim_Date d ON f.Date_Key = d.Date_Key
    JOIN dbo.Dim_Channels c ON f.Channel_Key = c.Channel_Key
    WHERE d.Full_Date BETWEEN @StartDate AND @EndDate
      AND (@ChannelCode IS NULL OR c.Channel_Code = @ChannelCode)
    GROUP BY d.Year_Number, d.Month_Name, d.Month_Number, c.Channel_Name
    ORDER BY d.Year_Number, d.Month_Number, Interactions DESC;
END;
GO
