import urllib.request
import urllib.error
import ssl

def main():
    url = "https://antapaccay.sam.glencore.net/ReportViewer/Reserved.ReportViewerWebControl.axd?ReportSession=1xzksh55fgfv5iqsiz2zwf55&Culture=10250&CultureOverrides=True&UICulture=1033&UICultureOverrides=True&ReportStack=1&ControlID=6b9d062bb5cd467db6d88cfb97758359&RSProxy=http%3a%2f%2f10.151.193.13%2fPBIReportServer&OpType=ReportImage&IterationId=ce9b338b373440e593fcd4e566afae06&StreamID=70686182-9469-44a9-a3d1-42069d7e093a"
    
    headers = {
        "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "accept-language": "es-419,es;q=0.9",
        "connection": "keep-alive",
        "cookie": "ai_user=WDjM7|2026-05-27T02:40:16.209Z; ASP.NET_SessionId=lllqhto0vneapg5buuqf5sj3; ai_session=9isPl|1779936199816|1779936486446.4",
        "host": "antapaccay.sam.glencore.net",
        "referer": "https://antapaccay.sam.glencore.net/ReportViewer/Report.aspx?/PBI_Seguridad/HSEC/Capacitaciones/CursoReporteDetallado&rs:Embed=true&rc:Parameters=false&CodPersona=0060295528&rs:ParameterLanguage=en-us&rc:Toolbar=true",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    }

    print(f"Haciendo peticion GET a: {url}")
    
    # Desactivar verificación SSL por si acaso (equivalente a verify=False en requests)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            status_code = response.getcode()
            print(f"Status Code: {status_code}")
            print(f"Content-Type: {response.info().get('Content-Type')}")
            print(f"Content-Length: {response.info().get('Content-Length')}")
            
            content = response.read()
            out_file = "test_report_image.jpg"
            with open(out_file, "wb") as f:
                f.write(content)
            print(f"Exito! Archivo guardado como {out_file} (Tamano: {len(content)} bytes)")
            
    except urllib.error.HTTPError as e:
        print(f"HTTPError: Status Code {e.code}")
        print(e.read()[:500])
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    main()
