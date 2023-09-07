import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER_EMAIL = 'XXX@gmail.com'
SENDER_PASSWORD = 'XXX'


def send_email(recipient_email, subject, message):
    # Создаем объект MIMEMultipart
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Добавляем текст сообщения в MIMEMultipart объект
    msg.attach(MIMEText(message, 'plain'))

    try:
        # Создаем SMTP объект для отправки письма
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        # Авторизуемся на почтовом сервере
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        # Отправляем письмо
        server.send_message(msg)
        print("Письмо успешно отправлено!")
        # Закрываем соединение с сервером
        server.quit()
    except Exception as e:
        print("Ошибка при отправке письма:", str(e))