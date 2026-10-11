import http.server
import socketserver
import sqlite3
import json
import urllib.parse
import os

PORT = int(os.environ.get("PORT", 8085))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "telecom_bi.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class BIDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/api/kpis":
            self.handle_kpis(params)
        elif parsed.path == "/api/charts":
            self.handle_charts(params)
        elif parsed.path == "/api/agents":
            self.handle_agents()
        elif parsed.path == "/" or parsed.path == "/index.html":
            self.send_file("index.html", "text/html")
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/query":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            try:
                payload = json.loads(body)
                query = payload.get("query", "").strip()
                
                # Seguridad: Solo consultas SELECT permitidas
                if not query.lower().startswith("select"):
                    self.send_json({"error": "Solo se permiten consultas analíticas de lectura (SELECT)."}, 400)
                    return
                
                conn = get_db()
                cur = conn.cursor()
                cur.execute(query)
                columns = [d[0] for d in cur.description]
                rows = [list(r) for r in cur.fetchall()[:100]] # Limit 100
                conn.close()
                self.send_json({"columns": columns, "rows": rows, "count": len(rows)})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

    def handle_kpis(self, params):
        channel = params.get("channel", [None])[0]
        segment = params.get("segment", [None])[0]

        sql = """
            SELECT 
                COUNT(*) AS total_interactions,
                ROUND(AVG(Handling_Time_Seconds), 0) AS avg_aht,
                ROUND(AVG(Hold_Time_Seconds), 0) AS avg_hold,
                ROUND(SUM(CASE WHEN FCR_Flag = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 1) AS fcr_pct,
                ROUND(AVG(CSAT_Score), 2) AS avg_csat,
                ROUND(AVG(Sentiment_Score), 3) AS avg_sentiment,
                ROUND(SUM(CASE WHEN SLA_Adherence_Flag = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 1) AS sla_pct,
                ROUND(SUM(Retained_Revenue_USD), 2) AS total_retained_rev,
                ROUND(SUM(Operational_Cost_USD), 2) AS total_cost
            FROM Fact_Interactions f
            JOIN Dim_Channels c ON f.Channel_Key = c.Channel_Key
            JOIN Dim_Customer_Segments s ON f.Segment_Key = s.Segment_Key
            WHERE 1=1
        """
        args = []
        if channel and channel != "ALL":
            sql += " AND c.Channel_Code = ?"
            args.append(channel)
        if segment and segment != "ALL":
            sql += " AND s.Segment_Code = ?"
            args.append(segment)

        conn = get_db()
        cur = conn.cursor()
        cur.execute(sql, args)
        row = dict(cur.fetchone())
        conn.close()
        self.send_json(row)

    def handle_charts(self, params):
        conn = get_db()
        cur = conn.cursor()

        # 1. Distribución por Canal
        cur.execute("""
            SELECT c.Channel_Name, COUNT(f.Interaction_ID) AS volume,
                   ROUND(SUM(CASE WHEN f.FCR_Flag = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 1) AS fcr
            FROM Fact_Interactions f
            JOIN Dim_Channels c ON f.Channel_Key = c.Channel_Key
            GROUP BY c.Channel_Name
            ORDER BY volume DESC
        """)
        channel_data = [dict(r) for r in cur.fetchall()]

        # 2. Categorías vs Churn Risk
        cur.execute("""
            SELECT cat.Category_Name, 
                   COUNT(f.Interaction_ID) AS volume,
                   ROUND(AVG(f.Churn_Risk_Prob) * 100.0, 1) AS churn_risk_pct,
                   ROUND(AVG(f.CSAT_Score), 2) AS avg_csat
            FROM Fact_Interactions f
            JOIN Dim_Incident_Categories cat ON f.Category_Key = cat.Category_Key
            GROUP BY cat.Category_Name
            ORDER BY churn_risk_pct DESC
        """)
        category_data = [dict(r) for r in cur.fetchall()]

        # 3. Tendencia por Hora del Día
        cur.execute("""
            SELECT strftime('%H', Contact_Timestamp) AS hour, COUNT(*) AS volume
            FROM Fact_Interactions
            GROUP BY hour
            ORDER BY hour ASC
        """)
        hourly_data = [dict(r) for r in cur.fetchall()]

        conn.close()
        self.send_json({
            "channels": channel_data,
            "categories": category_data,
            "hourly": hourly_data
        })

    def handle_agents(self):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                a.Agent_Code,
                a.Agent_Name,
                a.Tier_Level,
                a.Site_Location,
                COUNT(f.Interaction_ID) AS total_handled,
                ROUND(AVG(f.Handling_Time_Seconds), 0) AS avg_aht,
                ROUND(SUM(CASE WHEN f.FCR_Flag = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 1) AS fcr_rate,
                ROUND(AVG(f.CSAT_Score), 2) AS avg_csat,
                ROUND(SUM(f.Retained_Revenue_USD), 0) AS value_protected
            FROM Fact_Interactions f
            JOIN Dim_Agents a ON f.Agent_Key = a.Agent_Key
            GROUP BY a.Agent_Code, a.Agent_Name, a.Tier_Level, a.Site_Location
            ORDER BY avg_csat DESC, fcr_rate DESC
        """)
        agents = [dict(r) for r in cur.fetchall()]
        conn.close()
        self.send_json(agents)

    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, filename, content_type):
        path = os.path.join(BASE_DIR, filename)
        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return
        with open(path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

if __name__ == "__main__":
    os.chdir(BASE_DIR)
    print(f"Iniciando Servidor BI Analytics en http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), BIDashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
