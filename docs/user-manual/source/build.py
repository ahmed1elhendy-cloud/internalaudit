import re, subprocess, sys
from playwright.sync_api import sync_playwright
body=open('body.html').read()
heads=re.findall(r'<h1 id="(\w+)" class="sec">(.*?)</h1>',body)
CSS="""
@page{size:A4;margin:0}
*{box-sizing:border-box}
body{font-family:'Liberation Sans',Arial,sans-serif;font-size:10.5pt;line-height:1.5;color:#1d2433;margin:0}
.cover{height:297mm;background:#1F2A44;color:#fff;padding:60mm 25mm 25mm;page-break-after:always;position:relative}
.cover .bar{width:60mm;height:3mm;background:#C9A24B;margin-bottom:12mm}
.cover h1{font-size:34pt;line-height:1.15;margin:0 0 6mm;color:#fff}
.cover .sub{font-size:15pt;color:#C9A24B;margin-bottom:30mm}
.cover .meta{font-size:10.5pt;line-height:1.9;color:#dfe3ec}
.cover .foot{position:absolute;bottom:20mm;left:25mm;font-size:9pt;color:#aab2c4}
.page{padding:0}
.toc{page-break-after:always}
.toc h1{font-size:20pt;color:#1F2A44;border-bottom:2px solid #C9A24B;padding-bottom:3mm}
.toc .row{display:flex;font-size:10.5pt;padding:1.6mm 0;border-bottom:1px dotted #bbb}
.toc .row span:first-child{flex:1}
h1.sec{font-size:19pt;color:#1F2A44;border-bottom:2px solid #C9A24B;padding-bottom:2mm;margin:0 0 5mm;page-break-before:always}
h1.sec#s0{page-break-before:avoid}
h2{font-size:13pt;color:#1F2A44;margin:6mm 0 2mm;page-break-after:avoid}
h3{font-size:11pt;color:#8a6d1f;margin:5mm 0 2mm;page-break-after:avoid}
p{margin:0 0 3mm}
ul,ol{margin:0 0 3mm;padding-left:6mm}
li{margin-bottom:1.2mm}
table{border-collapse:collapse;width:100%;margin:2mm 0 4mm;page-break-inside:auto}
tr{page-break-inside:avoid}
th{background:#1F2A44;color:#fff;text-align:left;padding:2mm 2.5mm;font-size:9pt}
td{border:1px solid #d5d9e2;padding:1.8mm 2.5mm;vertical-align:top;font-size:9.3pt}
table.small td{font-size:9pt}
tr:nth-child(even) td{background:#f5f6f9}
.tag{background:#C9A24B;color:#1F2A44;font-size:8pt;font-weight:bold;padding:.5mm 2mm;border-radius:2mm}
.note{background:#fbf5e4;border-left:3px solid #C9A24B;padding:2.5mm 3.5mm}
.mono{font-family:'Liberation Mono',monospace;font-size:8.5pt;background:#eef0f5;padding:0 1mm}
.tabs{background:#1F2A44;color:#fff;padding:3mm;border-radius:2mm;font-size:9pt}
"""
def html(toc):
    t='<div class="toc"><h1>Contents</h1>'+''.join(f'<div class="row"><span>{h}</span><span>{toc.get(i,"")}</span></div>' for i,h in heads)+'</div>'
    cover='''<div class="cover"><div class="bar"></div><h1>MHAO Internal Audit Portal</h1><div class="sub">User Manual &ndash; Full System Guide</div>
<div class="meta">Mohamed Hareb Al Otaiba Group (MHAO)<br>Group Internal Audit<br>Version 2.0 &middot; 18 November 2026<br>Audience: audit team, management and executives</div>
<div class="foot">Support: ahmed.elhendy@mhao.ae &middot; Confidential &ndash; for internal use</div></div>'''
    return f'<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{cover}<div class="page">{t}{body}</div></body></html>'
def render(toc,out):
    open('m.html','w').write(html(toc))
    with sync_playwright() as p:
        b=p.chromium.launch();pg=b.new_page();pg.goto('file://'+__import__('os').getcwd()+'/m.html')
        pg.pdf(path=out,format='A4',print_background=True,margin={'top':'18mm','bottom':'18mm','left':'18mm','right':'18mm'},display_header_footer=True,
          header_template='<div></div>',footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#777;font-family:Liberation Sans">MHAO Internal Audit Portal &ndash; User Manual v2.0 &nbsp;|&nbsp; Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>')
        b.close()
render({}, 'p1.pdf')
n=int(re.search(r'Pages:\s+(\d+)',subprocess.run(['pdfinfo','p1.pdf'],capture_output=True,text=True).stdout).group(1))
toc={}
for pg in range(3,n+1):
    t=subprocess.run(['pdftotext','-f',str(pg),'-l',str(pg),'p1.pdf','-'],capture_output=True,text=True).stdout
    for i,h in heads:
        hh=h.replace('&amp;','&')[:30]
        if i not in toc and any(l.strip().startswith(hh) for l in t.splitlines()[:8]): toc[i]=pg
print(toc,len(heads))
render(toc,'IAMS_User_Manual.pdf')
