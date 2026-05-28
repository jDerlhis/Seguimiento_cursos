import re, html as htmllib

with open('reporte_detallado.csv', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Buscar hidden inputs del ASP.NET ViewState
inputs = re.findall(r'name="(__[A-Z]+)"[^>]+value="([^"]{0,200})', content)
for name, val in inputs:
    print(f'{name} = {val[:100]}')

# Buscar el action del form
form = re.search(r'action="([^"]+)"', content)
if form:
    print(f'\nFORM ACTION: {htmllib.unescape(form.group(1))}')
