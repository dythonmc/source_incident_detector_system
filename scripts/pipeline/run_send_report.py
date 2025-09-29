import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import markdown

def send_report_by_email(report_path: str, operation_date: str) -> bool:
    """
    Lee un archivo de reporte en formato Markdown, lo convierte a HTML y lo envía por email.
    """
    load_dotenv()
    
    sender_email = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    recipient_email = os.getenv("EMAIL_RECIPIENT")

    if not all([sender_email, password, recipient_email]):
        print("!! ERROR: Faltan variables de entorno para el email.")
        return False

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        print(f"!! ERROR: No se encontró el archivo de reporte en '{report_path}'.")
        return False

    html_content = markdown.markdown(markdown_content, extensions=['tables'])

    message = MIMEMultipart("alternative")
    subject = f"Reporte de Incidencias Automatizado - {operation_date}"
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email
    
    html_body = f"""
    <html><head><style>body {{ font-family: sans-serif; }}</style></head>
      <body><p>Hola,</p><p>Se ha generado el reporte de incidencias para la fecha <b>{operation_date}</b>.</p><hr>{html_content}<hr>
      <p><i>Reporte generado automáticamente por el Sistema de Detección de Incidencias.</i></p></body></html>"""
    message.attach(MIMEText(html_body, "html"))

    try:
        print(f"-> Conectando a smtp.gmail.com:465 para enviar a {recipient_email}...")
        # --- CAMBIO AQUÍ: Añadimos un timeout de 15 segundos ---
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15)
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()
        print("✓ ¡Reporte enviado por email exitosamente!")
        return True
    except Exception as e:
        print(f"!! ERROR: Falló el envío del email: {e}")
        return False