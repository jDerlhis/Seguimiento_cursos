import urllib.request
import urllib.error
import ssl

def make_post_request(url, headers, name, data=b""):
    print(f"--- Probando {name} ---")
    print(f"URL: {url}")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            status_code = response.getcode()
            content = response.read()
            print(f"Status Code: {status_code}")
            print(f"Content-Type: {response.info().get('Content-Type')}")
            print(f"Content-Length: {response.info().get('Content-Length')}")
            print(f"Respuesta (primeros 500 caracteres):\n{content.decode('utf-8', errors='ignore')[:500]}")
            
            # Guardar respuesta completa en archivo
            out_file = f"{name}.txt"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(content.decode('utf-8', errors='ignore'))
            print(f"-> Respuesta guardada en {out_file}\n")
            
    except urllib.error.HTTPError as e:
        print(f"HTTPError: Status Code {e.code}")
        print(e.read().decode('utf-8', errors='ignore')[:500])
        print("\n")
    except Exception as e:
        print(f"Exception: {e}\n")

def main():
    cookie = "ai_user=WDjM7|2026-05-27T02:40:16.209Z; ASP.NET_SessionId=lllqhto0vneapg5buuqf5sj3; ai_session=9isPl|1779936199816|1779936408793.2"
    
    # 1. Petición 1: SessionKeepAlive
    url1 = "https://antapaccay.sam.glencore.net/ReportViewer/Reserved.ReportViewerWebControl.axd?OpType=SessionKeepAlive&ControlID=6b9d062bb5cd467db6d88cfb97758359&RSProxy=http%3a%2f%2f10.151.193.13%2fPBIReportServer"
    headers1 = {
        "accept": "*/*",
        "accept-language": "es-419,es;q=0.9",
        "cookie": cookie,
        "origin": "https://antapaccay.sam.glencore.net",
        "referer": "https://antapaccay.sam.glencore.net/ReportViewer/Report.aspx?/PBI_Seguridad/HSEC/Capacitaciones/CursoReporteDetallado&rs:Embed=true&rc:Parameters=false&CodPersona=0060295528&rs:ParameterLanguage=en-us&rc:Toolbar=true",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
    
    make_post_request(url1, headers1, "respuesta_keepalive")

    # 2. Petición 2: Report.aspx Delta=true
    url2 = "https://antapaccay.sam.glencore.net/ReportViewer/Report.aspx?%2fPBI_Seguridad%2fHSEC%2fCapacitaciones%2fCursoReporteDetallado&rs%3aEmbed=true&rc%3aParameters=false&CodPersona=0060295528&rs%3aParameterLanguage=en-us&rc%3aToolbar=true"
    headers2 = {
        "accept": "*/*",
        "accept-language": "es-419,es;q=0.9",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "cookie": cookie,
        "origin": "https://antapaccay.sam.glencore.net",
        "referer": "https://antapaccay.sam.glencore.net/ReportViewer/Report.aspx?/PBI_Seguridad/HSEC/Capacitaciones/CursoReporteDetallado&rs:Embed=true&rc:Parameters=false&CodPersona=0060295528&rs:ParameterLanguage=en-us&rc:Toolbar=true",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "x-microsoftajax": "Delta=true",
        "x-requested-with": "XMLHttpRequest",
        "cache-control": "no-cache"
    }
    
    # Nota: El usuario no proporcionó el body (payload) de 4713 bytes, así que enviaremos un POST vacío. 
    # Es muy probable que esto devuelva un error de ASP.NET porque falta el ViewState.
    make_post_request(url2, headers2, "respuesta_report_delta")

if __name__ == "__main__":
    main()
