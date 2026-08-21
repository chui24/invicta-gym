import re
with open('static/js/dashboard.js', 'r') as f:
    content = f.read()

content = re.sub(r'// Funcionalidad del Reloj en Vivo.*?setInterval\(actualizarReloj, 1000\);\nactualizarReloj\(\);\n', '', content, flags=re.DOTALL)

with open('static/js/dashboard.js', 'w') as f:
    f.write(content)
