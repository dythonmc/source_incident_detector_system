import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

def send_report_by_email(report_path: str, operation_date: str) -> bool:
    """
    Lee un archivo de reporte y lo envía por email.

    Args:
        report_path (str): La ruta al archivo de reporte (ej. el .md).
        operation_date (str): La fecha de la operación para el asunto del email.

    Returns:
        bool: True si el email se envió con éxito, False en caso contrario.
    """
    load_dotenv()
    
    # --- Cargar credenciales desde el .env ---
    sender_email = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    recipient_email = os.getenv("EMAIL_RECIPIENT")

    if not all([sender_email, password, recipient_email]):
        print("!! ERROR: Faltan variables de entorno para el email (EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT).")
        return False

    # --- Leer el contenido del reporte ---
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content_html = f.read().replace('\n', '<br>')
    except FileNotFoundError:
        print(f"!! ERROR: No se encontró el archivo de reporte en '{report_path}'.")
        return False

    # --- Construir el email ---
    message = MIMEMultipart("alternative")
    subject = f"Reporte de Incidencias Automatizado - {operation_date}"
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email
    
    # Creamos una versión en HTML del reporte para que se vea bien en el correo
    html_body = f"""
    <html>
      <body>
        <p>Hola,</p>
        <p>Se ha generado un nuevo reporte de incidencias de procesamiento para la fecha <b>{operation_date}</b>.</p>
        <hr>
        {report_content_html}
        <hr>
        <p><i>Este es un reporte generado automáticamente por el Sistema de Detección de Incidencias.</i></p>
      </body>
    </html>
    """
    message.attach(MIMEText(html_body, "html"))

    # --- Enviar el email usando el servidor SMTP de Gmail ---
    try:
        print(f"-> Conectando al servidor SMTP para enviar el reporte a {recipient_email}...")
        # Usamos el servidor de Gmail. Si usas otro proveedor, estos valores cambiarán.
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()
        print("✓ ¡Reporte enviado por email exitosamente!")
        return True
    except Exception as e:
        print(f"!! ERROR: Falló el envío del email: {e}")
        return False