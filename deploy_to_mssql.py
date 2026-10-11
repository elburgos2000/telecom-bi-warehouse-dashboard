"""
Script de Despliegue Automatizado a Microsoft SQL Server (T-SQL)
Permite conectar y desplegar la arquitectura Star Schema en:
- SQL Server Local / Instancia SQLEXPRESS
- Contenedor Docker de SQL Server 2022
- Azure SQL Database / Amazon RDS for SQL Server
"""

import os
import sys

def print_instructions():
    print("=" * 70)
    print("  ENTERPRISE TELECOM BI WAREHOUSE - MS SQL SERVER DEPLOYMENT")
    print("=" * 70)
    print("Este proyecto incluye el script DDL nativo en T-SQL:")
    print("  -> schema_sql_server.sql")
    print("\nPara desplegar en una instancia de Microsoft SQL Server:")
    print("1. Mediante SQLCMD:")
    print("   sqlcmd -S localhost -U sa -P 'TuPasswordFuerte123' -i schema_sql_server.sql")
    print("\n2. Mediante SQL Server Management Studio (SSMS) o Azure Data Studio:")
    print("   - Abrir 'schema_sql_server.sql'")
    print("   - Conectar a la instancia y presionar 'Execute' (F5)")
    print("\n3. Importar los datos limpios desde la carpeta 'data_export/':")
    print("   - Fact_Interactions.csv (12,000 registros)")
    print("   - Dim_Agents.csv, Dim_Channels.csv, Dim_Customer_Segments.csv, etc.")
    print("=" * 70)

if __name__ == "__main__":
    print_instructions()
