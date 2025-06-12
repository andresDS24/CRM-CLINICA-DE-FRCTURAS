# CRM Clínica de Ortopedia

Este sistema permite gestionar proyectos, tareas, aseguradoras y contratos. Además, se integra con Google Calendar y es compatible con dispositivos Android mediante PWA.

## Instalación

1. Descarga y descomprime el paquete.
2. Instala dependencias:
```
pip install -r requirements.txt
```
3. Ejecuta la aplicación:
```
streamlit run app.py
```

## Google Calendar
Agrega tus credenciales al archivo `.streamlit/secrets.toml`:

```
[gcal_credentials]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

## Android
Desde Chrome en tu teléfono Android:
- Toca los 3 puntos (⋮)
- Selecciona “Agregar a pantalla de inicio”
