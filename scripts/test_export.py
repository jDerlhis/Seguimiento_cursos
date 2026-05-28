import urllib.request
import ssl
import sys

def main():
    # URL original del ReportImage:
    # https://antapaccay.sam.glencore.net/ReportViewer/Reserved.ReportViewerWebControl.axd?ReportSession=1xzksh55fgfv5iqsiz2zwf55&Culture=10250&CultureOverrides=True&UICulture=1033&UICultureOverrides=True&ReportStack=1&ControlID=6b9d062bb5cd467db6d88cfb97758359&RSProxy=http%3a%2f%2f10.151.193.13%2fPBIReportServer&OpType=ReportImage&IterationId=ce9b338b373440e593fcd4e566afae06&StreamID=70686182-9469-44a9-a3d1-42069d7e093a
    
    # Cambiamos OpType a Export y agregamos ExportExtension=CSV
    url = "https://antapaccay.sam.glencore.net/ReportViewer/Reserved.ReportViewerWebControl.axd?ReportSession=1xzksh55fgfv5iqsiz2zwf55&Culture=10250&CultureOverrides=True&UICulture=1033&UICultureOverrides=True&ReportStack=1&ControlID=6b9d062bb5cd467db6d88cfb97758359&RSProxy=http%3a%2f%2f10.151.193.13%2fPBIReportServer&OpType=Export&ExportExtension=CSV"
    
    cookie = "ai_user=WDjM7|2026-05-27T02:40:16.209Z; ASP.NET_SessionId=lllqhto0vneapg5buuqf5sj3; ai_session=9isPl|1779936199816|1779936486446.4"
    
    headers = {
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
            print("\n--- DATOS OBTENIDOS ---")
            print(content[:1000])
            print("-----------------------")
    except Exception as e:
        print(f"Error: {e}")
        try:
            print(e.read().decode('utf-8', errors='ignore')[:500])
        except:
            pass

if __name__ == "__main__":
    main()
