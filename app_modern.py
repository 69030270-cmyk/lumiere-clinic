import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import mysql.connector
import qrcode
from PIL import Image, ImageTk

# =========================================================
# Database
# Set DB_PASSWORD in your environment, or enter it below.
# =========================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv("DB_PASSWORD", ""),  # ใส่รหัสผ่าน MySQL ในตัวแปร DB_PASSWORD
    "database": "doctor_booking",
}

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
except mysql.connector.Error as exc:
    # Show a friendly error instead of a raw traceback at startup.
    _error_root = tk.Tk()
    _error_root.withdraw()
    messagebox.showerror(
        "เชื่อมต่อฐานข้อมูลไม่สำเร็จ",
        "ไม่สามารถเชื่อมต่อ MySQL ได้\n\n"
        "ตรวจสอบว่า MySQL ทำงานอยู่ และตั้งค่า DB_PASSWORD ถูกต้อง\n\n"
        f"รายละเอียด: {exc}",
    )
    _error_root.destroy()
    raise SystemExit(1)

current_member_id = None
current_doctor_id = None
current_role = None
current_user_name = ""
doctor_dashboard = None

# ------------------------- Theme --------------------------
BG = "#F7F4FA"
CARD = "#FFFFFF"
PRIMARY = "#B84D83"
PRIMARY_DARK = "#963765"
PINK_LIGHT = "#FCEAF3"
TEXT = "#30283A"
MUTED = "#786F80"
BORDER = "#E9DFE9"
BLUE = "#5279B8"
GREEN = "#39856B"
RED = "#C65360"
GOLD = "#B78328"

root = tk.Tk()
root.title("Beauty Clinic | ระบบจองคิวคลินิกความงาม")
root.geometry("1120x760")
root.minsize(980, 680)
root.configure(bg=BG)

style = ttk.Style(root)
try:
    style.theme_use("clam")
except tk.TclError:
    pass

style.configure("TFrame", background=BG)
style.configure("Card.TFrame", background=CARD)
style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
style.configure("Title.TLabel", background=BG, foreground=PRIMARY_DARK,
                font=("Segoe UI", 23, "bold"))
style.configure("Subtitle.TLabel", background=BG, foreground=MUTED,
                font=("Segoe UI", 10))
style.configure("CardTitle.TLabel", background=CARD, foreground=TEXT,
                font=("Segoe UI", 12, "bold"))
style.configure("Field.TLabel", background=CARD, foreground=MUTED,
                font=("Segoe UI", 10))
style.configure("TEntry", padding=9, font=("Segoe UI", 10))
style.configure("TCombobox", padding=7, font=("Segoe UI", 10))
style.configure("Treeview", font=("Segoe UI", 10), rowheight=31,
                background=CARD, fieldbackground=CARD, foreground=TEXT)
style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                background=PINK_LIGHT, foreground=PRIMARY_DARK, padding=8)
style.map("Treeview", background=[("selected", "#F3C8DD")],
          foreground=[("selected", TEXT)])
style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"),
                padding=(14, 10), background=PRIMARY, foreground="white")
style.map("Primary.TButton", background=[("active", PRIMARY_DARK)])
style.configure("Secondary.TButton", font=("Segoe UI", 10, "bold"),
                padding=(12, 9), background=PINK_LIGHT, foreground=PRIMARY_DARK)
style.map("Secondary.TButton", background=[("active", "#F6D7E7")])
style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"),
                padding=(12, 9), background="#FBEAEC", foreground=RED)
style.map("Danger.TButton", background=[("active", "#F5D2D7")])

def clear_root():
    for widget in root.winfo_children():
        widget.destroy()

def on_close():
    try:
        if conn.is_connected():
            cursor.close()
            conn.close()
    except Exception:
        pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

def heading(parent, title, subtitle=None):
    top = ttk.Frame(parent)
    top.pack(fill="x", pady=(0, 18))
    ttk.Label(top, text=title, style="Title.TLabel").pack(anchor="w")
    if subtitle:
        ttk.Label(top, text=subtitle, style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))
    return top

def card(parent, padding=20):
    frame = ttk.Frame(parent, style="Card.TFrame", padding=padding)
    return frame

def db_error(exc):
    messagebox.showerror("เกิดข้อผิดพลาด", f"ดำเนินการไม่สำเร็จ\n\n{exc}", parent=root)

# -------------------------- Login -------------------------
def show_login():
    global current_member_id, current_doctor_id, current_role, current_user_name
    current_member_id = current_doctor_id = current_role = None
    current_user_name = ""
    clear_root()

    shell = ttk.Frame(root, padding=(35, 24))
    shell.pack(fill="both", expand=True)

    brand = ttk.Frame(shell)
    brand.pack(fill="x", pady=(10, 25))
    ttk.Label(brand, text="BEAUTY CLINIC", style="Title.TLabel").pack()
    ttk.Label(brand, text="ระบบจองคิวคลินิกความงาม • จัดการนัดหมายได้ในที่เดียว",
              style="Subtitle.TLabel").pack(pady=(5, 0))

    login_card = card(shell, 30)
    login_card.pack(anchor="center", ipadx=35, ipady=8)
    ttk.Label(login_card, text="ยินดีต้อนรับกลับ", style="CardTitle.TLabel",
              font=("Segoe UI", 17, "bold")).pack(anchor="w")
    ttk.Label(login_card, text="เข้าสู่ระบบเพื่อจัดการนัดหมายของคุณ",
              style="Field.TLabel").pack(anchor="w", pady=(4, 22))

    form = ttk.Frame(login_card, style="Card.TFrame")
    form.pack(fill="x")
    ttk.Label(form, text="ประเภทบัญชี", style="Field.TLabel").pack(anchor="w", pady=(0, 6))
    role_var = tk.StringVar(value="Member")
    role_box = ttk.Combobox(form, textvariable=role_var, values=("Member", "Doctor"),
                            state="readonly", width=34)
    role_box.pack(fill="x", pady=(0, 14))

    ttk.Label(form, text="อีเมล", style="Field.TLabel").pack(anchor="w", pady=(0, 6))
    email_entry = ttk.Entry(form, width=38)
    email_entry.pack(fill="x", pady=(0, 14))

    ttk.Label(form, text="รหัสผ่าน", style="Field.TLabel").pack(anchor="w", pady=(0, 6))
    password_entry = ttk.Entry(form, width=38, show="●")
    password_entry.pack(fill="x", pady=(0, 20))

    def do_login(event=None):
        global current_member_id, current_doctor_id, current_role, current_user_name
        email = email_entry.get().strip()
        password = password_entry.get()
        role = role_var.get()

        if not email or not password:
            messagebox.showwarning("ข้อมูลไม่ครบ", "กรุณากรอกอีเมลและรหัสผ่าน", parent=root)
            return

        try:
            if role == "Member":
                cursor.execute("""
                    SELECT member_id, full_name
                    FROM Member
                    WHERE email=%s AND password=%s
                """, (email, password))
                result = cursor.fetchone()
                if result:
                    current_member_id = result[0]
                    current_user_name = result[1]
                    current_role = "Member"
                    show_member_dashboard()
                else:
                    messagebox.showerror("เข้าสู่ระบบไม่สำเร็จ", "อีเมลหรือรหัสผ่านไม่ถูกต้อง", parent=root)
            else:
                cursor.execute("""
                    SELECT d.doctor_id, d.doctor_name
                    FROM DoctorAccount a
                    JOIN Doctor d ON a.doctor_id = d.doctor_id
                    WHERE a.email=%s AND a.password=%s
                """, (email, password))
                result = cursor.fetchone()
                if result:
                    current_doctor_id = result[0]
                    current_user_name = result[1]
                    current_role = "Doctor"
                    show_doctor_dashboard()
                else:
                    messagebox.showerror("เข้าสู่ระบบไม่สำเร็จ", "อีเมลหรือรหัสผ่านไม่ถูกต้อง", parent=root)
        except mysql.connector.Error as exc:
            db_error(exc)

    ttk.Button(login_card, text="เข้าสู่ระบบ", style="Primary.TButton",
               command=do_login).pack(fill="x")
    password_entry.bind("<Return>", do_login)
    email_entry.focus_set()

    ttk.Label(shell, text="Beauty Clinic Booking System © 2026",
              style="Subtitle.TLabel").pack(side="bottom", pady=(15, 0))

# --------------------- Member dashboard -------------------
def show_member_dashboard():
    clear_root()
    shell = ttk.Frame(root, padding=(26, 22))
    shell.pack(fill="both", expand=True)

    top = ttk.Frame(shell)
    top.pack(fill="x", pady=(0, 18))
    left = ttk.Frame(top)
    left.pack(side="left", fill="x", expand=True)
    ttk.Label(left, text="ระบบจองคิวคลินิก", style="Title.TLabel").pack(anchor="w")
    ttk.Label(left, text=f"สวัสดีคุณ {current_user_name} • เลือกแพทย์และเวลาที่สะดวก",
              style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))
    ttk.Button(top, text="ออกจากระบบ", style="Danger.TButton",
               command=logout).pack(side="right", anchor="n")

    content = ttk.Frame(shell)
    content.pack(fill="both", expand=True)

    # Doctor card
    doctor_card = card(content, 18)
    doctor_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
    ttk.Label(doctor_card, text="แพทย์ของเรา", style="CardTitle.TLabel").pack(anchor="w")
    ttk.Label(doctor_card, text="เลือกแพทย์เพื่อดูเวลานัดหมาย", style="Field.TLabel").pack(anchor="w", pady=(4, 12))

    global doctor_list, schedule_tree, member_action_frame
    doctor_list = tk.Listbox(doctor_card, height=12, font=("Segoe UI", 10),
                             bg="#FFFBFD", fg=TEXT, selectbackground="#F3C8DD",
                             selectforeground=TEXT, relief="flat", highlightthickness=1,
                             highlightbackground=BORDER, activestyle="none",
                             exportselection=False)
    doctor_list.pack(fill="both", expand=True)
    doctor_list.bind("<Double-Button-1>", lambda event: show_schedule())

    # Schedule card
    schedule_card = card(content, 18)
    schedule_card.pack(side="left", fill="both", expand=True, padx=(10, 0))
    ttk.Label(schedule_card, text="เวลานัดหมายที่ว่าง", style="CardTitle.TLabel").pack(anchor="w")
    ttk.Label(schedule_card, text="เลือกเวลาจากตาราง แล้วกดจองคิว", style="Field.TLabel").pack(anchor="w", pady=(4, 12))

    schedule_columns = ("schedule_id", "date", "time")
    schedule_tree = ttk.Treeview(schedule_card, columns=schedule_columns, show="headings",
                                 height=12, selectmode="browse")
    schedule_tree.heading("schedule_id", text="รหัส")
    schedule_tree.heading("date", text="วันที่")
    schedule_tree.heading("time", text="เวลา")
    schedule_tree.column("schedule_id", width=65, anchor="center")
    schedule_tree.column("date", width=150, anchor="center")
    schedule_tree.column("time", width=110, anchor="center")
    schedule_tree.pack(fill="both", expand=True)
    schedule_tree.bind("<Double-Button-1>", lambda event: book_queue())

    actions = ttk.Frame(shell)
    actions.pack(fill="x", pady=(18, 0))
    ttk.Button(actions, text="ดูตารางเวลา", style="Secondary.TButton",
               command=show_schedule).pack(side="left", padx=(0, 8))
    ttk.Button(actions, text="จองคิว", style="Primary.TButton",
               command=book_queue).pack(side="left", padx=8)
    ttk.Button(actions, text="ประวัติการจอง", style="Secondary.TButton",
               command=show_booking_history).pack(side="left", padx=8)
    ttk.Button(actions, text="ชำระเงิน", style="Secondary.TButton",
               command=payment).pack(side="left", padx=8)
    ttk.Button(actions, text="ยกเลิกการจอง", style="Danger.TButton",
               command=cancel_booking).pack(side="left", padx=8)

    ttk.Label(shell, text="Beauty Clinic Booking System © 2026",
              style="Subtitle.TLabel").pack(side="bottom", pady=(14, 0))
    load_doctors()

def load_doctors():
    doctor_list.delete(0, tk.END)
    try:
        cursor.execute("SELECT doctor_id, doctor_name FROM Doctor ORDER BY doctor_name")
        for doctor_id, doctor_name in cursor.fetchall():
            doctor_list.insert(tk.END, f"{doctor_id}  •  {doctor_name}")
    except mysql.connector.Error as exc:
        db_error(exc)

def show_schedule():
    for item in schedule_tree.get_children():
        schedule_tree.delete(item)

    selected = doctor_list.curselection()
    if not selected:
        messagebox.showwarning("ยังไม่ได้เลือกแพทย์", "กรุณาเลือกแพทย์ก่อนดูตารางเวลา", parent=root)
        return

    try:
        doctor_text = doctor_list.get(selected[0])
        doctor_id = int(doctor_text.split("•")[0].strip())
        cursor.execute("""
            SELECT s.schedule_id, s.schedule_date, s.schedule_time
            FROM Schedule s
            WHERE s.doctor_id = %s
              AND s.schedule_id NOT IN (
                  SELECT schedule_id
                  FROM QueueBooking
                  WHERE status <> 'Cancelled'
              )
            ORDER BY s.schedule_date, s.schedule_time
        """, (doctor_id,))
        rows = cursor.fetchall()
        for row in rows:
            schedule_tree.insert("", tk.END, iid=str(row[0]), values=row)
        if not rows:
            messagebox.showinfo("ไม่มีเวลาว่าง", "แพทย์ท่านนี้ยังไม่มีช่วงเวลาว่าง", parent=root)
    except (mysql.connector.Error, ValueError) as exc:
        db_error(exc)

def book_queue():
    if current_member_id is None or current_role != "Member":
        messagebox.showwarning("แจ้งเตือน", "กรุณาเข้าสู่ระบบด้วยบัญชี Member", parent=root)
        return

    selected = schedule_tree.selection()
    if not selected:
        messagebox.showwarning("ยังไม่ได้เลือกเวลา", "กรุณาเลือกช่วงเวลาที่ต้องการจอง", parent=root)
        return

    schedule_id = int(selected[0])
    if not messagebox.askyesno("ยืนยันการจอง", "ต้องการจองช่วงเวลานี้ใช่หรือไม่?", parent=root):
        return

    try:
        cursor.execute("""
            SELECT queue_id FROM QueueBooking
            WHERE schedule_id=%s AND status <> 'Cancelled'
        """, (schedule_id,))
        if cursor.fetchone():
            messagebox.showerror("จองไม่สำเร็จ", "ช่วงเวลานี้ถูกจองแล้ว กรุณาเลือกเวลาอื่น", parent=root)
            show_schedule()
            return

        cursor.execute("""
            INSERT INTO QueueBooking (member_id, schedule_id, queue_number, status)
            VALUES (%s, %s, 1, 'Confirmed')
        """, (current_member_id, schedule_id))
        conn.commit()
        queue_id = cursor.lastrowid
        messagebox.showinfo("จองสำเร็จ", f"จองคิวเรียบร้อยแล้ว\nQueue ID: {queue_id}", parent=root)
        show_schedule()
    except mysql.connector.Error as exc:
        conn.rollback()
        db_error(exc)

# ------------------------- History ------------------------
def show_booking_history():
    window = tk.Toplevel(root)
    window.title("ประวัติการจอง")
    window.geometry("1000x470")
    window.configure(bg=BG)

    wrap = ttk.Frame(window, padding=22)
    wrap.pack(fill="both", expand=True)
    heading(wrap, "ประวัติการจอง", "รายการจองและสถานะการชำระเงิน")

    columns = ("queue", "member", "doctor", "date", "time", "status", "payment")
    tree = ttk.Treeview(wrap, columns=columns, show="headings")
    headers = {
        "queue": ("Queue ID", 80), "member": ("ลูกค้า", 160),
        "doctor": ("แพทย์", 150), "date": ("วันที่", 130),
        "time": ("เวลา", 100), "status": ("สถานะคิว", 110),
        "payment": ("ชำระเงิน", 110),
    }
    for key, (label, width) in headers.items():
        tree.heading(key, text=label)
        tree.column(key, width=width, anchor="center")
    tree.pack(fill="both", expand=True)

    try:
        if current_role == "Member":
            cursor.execute("""
                SELECT q.queue_id, m.full_name, d.doctor_name, s.schedule_date,
                       s.schedule_time, q.status, IFNULL(p.payment_status,'Unpaid')
                FROM QueueBooking q
                JOIN Member m ON q.member_id=m.member_id
                JOIN Schedule s ON q.schedule_id=s.schedule_id
                JOIN Doctor d ON s.doctor_id=d.doctor_id
                LEFT JOIN Payment p ON q.queue_id=p.queue_id
                WHERE q.member_id=%s
                ORDER BY s.schedule_date DESC, s.schedule_time
            """, (current_member_id,))
        elif current_role == "Doctor":
            cursor.execute("""
                SELECT q.queue_id, m.full_name, d.doctor_name, s.schedule_date,
                       s.schedule_time, q.status, IFNULL(p.payment_status,'Unpaid')
                FROM QueueBooking q
                JOIN Member m ON q.member_id=m.member_id
                JOIN Schedule s ON q.schedule_id=s.schedule_id
                JOIN Doctor d ON s.doctor_id=d.doctor_id
                LEFT JOIN Payment p ON q.queue_id=p.queue_id
                WHERE s.doctor_id=%s
                ORDER BY s.schedule_date DESC, s.schedule_time
            """, (current_doctor_id,))
        else:
            cursor.execute("""
                SELECT q.queue_id, m.full_name, d.doctor_name, s.schedule_date,
                       s.schedule_time, q.status, IFNULL(p.payment_status,'Unpaid')
                FROM QueueBooking q
                JOIN Member m ON q.member_id=m.member_id
                JOIN Schedule s ON q.schedule_id=s.schedule_id
                JOIN Doctor d ON s.doctor_id=d.doctor_id
                LEFT JOIN Payment p ON q.queue_id=p.queue_id
                ORDER BY s.schedule_date DESC, s.schedule_time
            """)
        for row in cursor.fetchall():
            tree.insert("", tk.END, values=row)
    except mysql.connector.Error as exc:
        db_error(exc)

# -------------------------- Payment -----------------------
def payment():
    if current_role != "Member":
        messagebox.showwarning("ไม่สามารถชำระเงินได้", "กรุณาเข้าสู่ระบบด้วยบัญชี Member", parent=root)
        return

    window = tk.Toplevel(root)
    window.title("ชำระเงิน")
    window.geometry("500x700")
    window.configure(bg=BG)
    window.transient(root)

    wrap = ttk.Frame(window, padding=24)
    wrap.pack(fill="both", expand=True)
    heading(wrap, "ชำระเงิน", "กรอก Queue ID และจำนวนเงินตามยอดที่ต้องชำระ")

    pay_card = card(wrap, 20)
    pay_card.pack(fill="both", expand=True)
    ttk.Label(pay_card, text="Queue ID", style="Field.TLabel").pack(anchor="w")
    queue_entry = ttk.Entry(pay_card)
    queue_entry.pack(fill="x", pady=(5, 12))
    ttk.Label(pay_card, text="จำนวนเงิน (บาท)", style="Field.TLabel").pack(anchor="w")
    amount_entry = ttk.Entry(pay_card)
    amount_entry.insert(0, "999")
    amount_entry.pack(fill="x", pady=(5, 14))

    # QR นี้เป็นเพียง QR ตัวอย่างตามโค้ดเดิม ไม่ใช่การยืนยันรับเงินจริง
    qr_label = ttk.Label(pay_card, text="กำลังสร้าง QR ตัวอย่าง...")
    qr_label.pack(pady=5)
    try:
        qr_image = qrcode.make("PromptPay:0999999999")
        qr_image = qr_image.resize((190, 190))
        photo = ImageTk.PhotoImage(qr_image)
        qr_label.configure(image=photo, text="")
        qr_label.image = photo
    except Exception:
        qr_label.configure(text="ไม่สามารถสร้าง QR ได้")

    ttk.Label(pay_card, text="PromptPay: 099-999-9999",
              style="CardTitle.TLabel").pack(pady=(8, 4))
    ttk.Label(pay_card, text="ยอดตัวอย่าง 999 บาท",
              foreground=RED, background=CARD,
              font=("Segoe UI", 11, "bold")).pack()
    ttk.Label(pay_card, text="หมายเหตุ: QR นี้เป็นข้อมูลจำลอง ไม่ได้ตรวจสอบการโอนเงินจริง",
              foreground=MUTED, background=CARD,
              font=("Segoe UI", 9), wraplength=390).pack(pady=(8, 12))

    def save_payment():
        queue_id = queue_entry.get().strip()
        amount_text = amount_entry.get().strip()
        if not queue_id or not amount_text:
            messagebox.showwarning("ข้อมูลไม่ครบ", "กรุณากรอก Queue ID และจำนวนเงิน", parent=window)
            return
        try:
            queue_id_int = int(queue_id)
            amount = float(amount_text)
            if amount <= 0:
                messagebox.showwarning("จำนวนเงินไม่ถูกต้อง", "จำนวนเงินต้องมากกว่า 0", parent=window)
                return

            # จำกัดให้สมาชิกชำระได้เฉพาะคิวของตัวเอง และป้องกันการบันทึกซ้ำ
            cursor.execute("""
                SELECT q.queue_id
                FROM QueueBooking q
                WHERE q.queue_id=%s AND q.member_id=%s AND q.status <> 'Cancelled'
            """, (queue_id_int, current_member_id))
            if not cursor.fetchone():
                messagebox.showerror("ไม่พบคิว", "ไม่พบ Queue ID นี้ในบัญชีของคุณ", parent=window)
                return

            cursor.execute("""
                SELECT payment_id FROM Payment
                WHERE queue_id=%s AND payment_status='Paid'
            """, (queue_id_int,))
            if cursor.fetchone():
                messagebox.showinfo("ชำระเงินแล้ว", "คิวนี้มีสถานะชำระเงินแล้ว", parent=window)
                return

            cursor.execute("""
                INSERT INTO Payment (queue_id, amount, payment_status)
                VALUES (%s, %s, 'Paid')
            """, (queue_id_int, amount))
            conn.commit()
            messagebox.showinfo(
                "บันทึกสถานะแล้ว",
                "บันทึกสถานะชำระเงินในระบบแล้ว\n"
                "โปรดทราบ: โปรแกรมนี้ยังไม่ได้เชื่อมต่อระบบตรวจสอบการโอนเงินจริง",
                parent=window,
            )
            window.destroy()
        except ValueError:
            messagebox.showwarning("ข้อมูลไม่ถูกต้อง", "Queue ID ต้องเป็นเลขจำนวนเต็ม และจำนวนเงินต้องเป็นตัวเลข", parent=window)
        except mysql.connector.Error as exc:
            conn.rollback()
            db_error(exc)

    ttk.Button(pay_card, text="บันทึกสถานะชำระเงิน", style="Primary.TButton",
               command=save_payment).pack(fill="x", pady=(4, 0))

# ---------------------- Cancel Booking ---------------------
def cancel_booking():
    if current_role != "Member":
        messagebox.showwarning("แจ้งเตือน", "กรุณาเข้าสู่ระบบด้วยบัญชี Member", parent=root)
        return
    queue_id = simpledialog.askstring("ยกเลิกการจอง", "กรอก Queue ID ที่ต้องการยกเลิก", parent=root)
    if not queue_id:
        return
    try:
        cursor.execute("""
            SELECT queue_id FROM QueueBooking
            WHERE queue_id=%s AND member_id=%s AND status <> 'Cancelled'
        """, (queue_id.strip(), current_member_id))
        if not cursor.fetchone():
            messagebox.showerror("ไม่พบคิว", "ไม่พบ Queue ID นี้ในบัญชีของคุณ หรือคิวถูกยกเลิกแล้ว", parent=root)
            return
        if not messagebox.askyesno("ยืนยันการยกเลิก", f"ต้องการยกเลิกคิว {queue_id} ใช่หรือไม่?", parent=root):
            return

        # ใช้สถานะ Cancelled แทนการลบแถว เพื่อรักษาประวัติการจอง
        cursor.execute("UPDATE QueueBooking SET status='Cancelled' WHERE queue_id=%s", (queue_id.strip(),))
        conn.commit()
        messagebox.showinfo("ยกเลิกสำเร็จ", "ยกเลิกการจองเรียบร้อยแล้ว", parent=root)
    except mysql.connector.Error as exc:
        conn.rollback()
        db_error(exc)

# --------------------- Doctor dashboard -------------------
def show_doctor_dashboard():
    global doctor_dashboard
    clear_root()
    shell = ttk.Frame(root, padding=(26, 22))
    shell.pack(fill="both", expand=True)

    top = ttk.Frame(shell)
    top.pack(fill="x", pady=(0, 18))
    title_frame = ttk.Frame(top)
    title_frame.pack(side="left", fill="x", expand=True)
    ttk.Label(title_frame, text="ตารางนัดหมายแพทย์", style="Title.TLabel").pack(anchor="w")
    ttk.Label(title_frame, text=f"แพทย์: {current_user_name}", style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))
    ttk.Button(top, text="ออกจากระบบ", style="Danger.TButton",
               command=logout).pack(side="right", anchor="n")

    panel = card(shell, 18)
    panel.pack(fill="both", expand=True)
    ttk.Label(panel, text="รายการนัดหมายของคุณ", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 12))

    columns = ("queue", "member", "date", "time", "status")
    tree = ttk.Treeview(panel, columns=columns, show="headings", height=15)
    definitions = [
        ("queue", "Queue ID", 100), ("member", "ชื่อลูกค้า", 260),
        ("date", "วันที่", 180), ("time", "เวลา", 150), ("status", "สถานะ", 150)
    ]
    for key, label, width in definitions:
        tree.heading(key, text=label)
        tree.column(key, width=width, anchor="center")
    tree.pack(fill="both", expand=True)

    try:
        cursor.execute("""
            SELECT q.queue_id, m.full_name, s.schedule_date, s.schedule_time, q.status
            FROM QueueBooking q
            JOIN Member m ON q.member_id=m.member_id
            JOIN Schedule s ON q.schedule_id=s.schedule_id
            WHERE s.doctor_id=%s
            ORDER BY s.schedule_date, s.schedule_time
        """, (current_doctor_id,))
        for row in cursor.fetchall():
            tree.insert("", tk.END, values=row)
    except mysql.connector.Error as exc:
        db_error(exc)

    ttk.Button(shell, text="ดูประวัติการจอง", style="Secondary.TButton",
               command=show_booking_history).pack(anchor="w", pady=(14, 0))

def logout():
    if messagebox.askyesno("ออกจากระบบ", "ต้องการออกจากระบบใช่หรือไม่?", parent=root):
        show_login()

# --------------------------- Start -------------------------
show_login()
root.mainloop()
on_close()
