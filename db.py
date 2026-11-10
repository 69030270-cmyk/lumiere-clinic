import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="S_iceice188",  # เปลี่ยนเป็นรหัสของคุณ
    database="doctor_booking"
)

cursor = conn.cursor()

print("เชื่อมต่อฐานข้อมูลสำเร็จ")