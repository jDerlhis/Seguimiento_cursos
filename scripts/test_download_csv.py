import urllib.request
import urllib.error
import ssl
import sys

def main():
    print("--- Descargando CSV directamente desde SSRS ---")
    
    # URL construida con la Estrategia A (rs:Format=CSV) y el CodPersona del iframe del usuario
    cod_persona = "0041448567"
    url = f"https://antapaccay.sam.glencore.net/ReportServer?/PBI_Seguridad/HSEC/Capacitaciones/CursoReporteDetallado&CodPersona={cod_persona}&rs:Command=Render&rs:Format=CSV"
    
    # Cookies válidas proporcionadas por el usuario
    cookie = "ai_user=WDjM7|2026-05-27T02:40:16.209Z; ASP.NET_SessionId=lllqhto0vneapg5buuqf5sj3; ai_session=9isPl|1779936199816|1779936408793.2"
    
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "es-419,es;q=0.9",
        "cookie": cookie,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    }

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            status_code = response.getcode()
            print(f"Status Code: {status_code}")
            print(f"Content-Type: {response.info().get('Content-Type')}")
            
            content = response.read().decode('utf-8-sig', errors='ignore')
            
            out_file = "reporte_capacitacion.csv"
            with open(out_file, "w", encoding="utf-8-sig") as f:
                f.write(content)
            
            print("\n================== DATOS OBTENIDOS (Primeras lineas) ==================")
            lines = content.split('\n')
            for i in range(min(15, len(lines))):
                print(lines[i].strip())
            print("=======================================================================")
            print(f"\nExito! Todos los datos fueron guardados en {out_file}")
            
    except urllib.error.HTTPError as e:
        print(f"HTTPError: Status Code {e.code}")
        print(e.read().decode('utf-8', errors='ignore')[:500])
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    main()
