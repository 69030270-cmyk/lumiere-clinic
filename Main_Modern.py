"""Beauty Clinic Booking — modern Tkinter interface (MySQL backend)."""
import os
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

BG = '#FFF7FA'
WHITE = '#FFFFFF'
PINK = '#D91F69'
PINK_DARK = '#AE1551'
INK = '#273044'
MUTED = '#798094'
BORDER = '#F0DFE7'
FONT = 'Tahoma'

class BookingApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Beauty Clinic | ระบบจองคิว')
        self.root.geometry('1080x720')
        self.root.minsize(850, 610)
        self.root.configure(bg=BG)
        self.conn = None
        self.rows = {}
        self.build_styles()
        self.build_ui()
        self.connect()
        self.root.protocol('WM_DELETE_WINDOW', self.close)

    def build_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Schedule.Treeview', font=(FONT, 11), rowheight=43,
                        background=WHITE, fieldbackground=WHITE, foreground=INK,
                        borderwidth=0)
        style.configure('Schedule.Treeview.Heading', font=(FONT, 10, 'bold'),
                        background='#FFF0F5', foreground=PINK_DARK, relief='flat', padding=(10, 13))
        style.map('Schedule.Treeview', background=[('selected', '#FBD9E7')],
                  foreground=[('selected', INK)])
        style.map('Schedule.Treeview.Heading', background=[('active', '#FFE2ED')])
        style.configure('Vertical.TScrollbar', background='#E9B7CA', troughcolor=WHITE)

    def label(self, parent, text, size=11, color=INK, bold=False, bg=WHITE, **kw):
        return tk.Label(parent, text=text, bg=bg, fg=color,
                        font=(FONT, size, 'bold' if bold else 'normal'), **kw)

    def button(self, parent, text, command, primary=True):
        bg = PINK if primary else '#FCE6EF'
        fg = WHITE if primary else PINK_DARK
        hover = PINK_DARK if primary else '#F8D3E2'
        btn = tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                        activebackground=hover, activeforeground=fg,
                        font=(FONT, 11, 'bold'), relief='flat', bd=0,
                        cursor='hand2', padx=24, pady=13)
        btn.bind('<Enter>', lambda e: btn.configure(bg=hover))
        btn.bind('<Leave>', lambda e: btn.configure(bg=bg))
        return btn

    def build_ui(self):
        header = tk.Frame(self.root, bg=WHITE, height=95, highlightbackground=BORDER, highlightthickness=1)
        header.pack(fill='x')
        header.pack_propagate(False)
        header_inner = tk.Frame(header, bg=WHITE)
        header_inner.pack(fill='both', expand=True, padx=45)
        self.label(header_inner, '✦  BEAUTY CLINIC', 19, PINK, True).pack(side='left', pady=25)
        self.label(header_inner, 'Appointment Booking System', 10, MUTED).pack(side='right')

        content = tk.Frame(self.root, bg=BG)
        content.pack(fill='both', expand=True, padx=45, pady=28)
        self.label(content, 'จองคิวเข้ารับบริการ', 23, INK, True, BG).pack(anchor='w')
        self.label(content, 'เลือกวันและเวลาที่สะดวก แล้วกดยืนยันการจอง', 11, MUTED, bg=BG).pack(anchor='w', pady=(5, 22))

        member_card = tk.Frame(content, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        member_card.pack(fill='x', pady=(0, 18))
        member_inner = tk.Frame(member_card, bg=WHITE)
        member_inner.pack(fill='x', padx=24, pady=20)
        self.label(member_inner, 'ข้อมูลผู้จอง', 13, INK, True).pack(anchor='w', pady=(0, 12))
        line = tk.Frame(member_inner, bg=WHITE)
        line.pack(fill='x')
        self.label(line, 'Member ID', 11, MUTED).pack(side='left', padx=(0, 14))
        self.member_entry = tk.Entry(line, font=(FONT, 12), bg='#FFFAFC', fg=INK,
                                     relief='flat', highlightthickness=1,
                                     highlightbackground=BORDER, highlightcolor=PINK, width=25)
        self.member_entry.pack(side='left', ipady=9, ipadx=10)
        self.label(line, 'กรอกหมายเลขสมาชิกก่อนจอง', 10, MUTED).pack(side='left', padx=18)

        schedule_card = tk.Frame(content, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        schedule_card.pack(fill='both', expand=True)
        top = tk.Frame(schedule_card, bg=WHITE)
        top.pack(fill='x', padx=24, pady=(20, 16))
        self.label(top, 'ตารางนัดหมายแพทย์', 14, INK, True).pack(side='left')
        self.button(top, '↻  รีเฟรชตาราง', self.load_schedules, False).pack(side='right')

        table_frame = tk.Frame(schedule_card, bg=WHITE)
        table_frame.pack(fill='both', expand=True, padx=24)
        cols = ('id', 'doctor', 'date', 'time', 'status')
        self.table = ttk.Treeview(table_frame, columns=cols, show='headings',
                                  style='Schedule.Treeview', selectmode='browse')
        for key, title, width, anchor in [
            ('id', 'รหัสนัด', 100, 'center'), ('doctor', 'แพทย์', 260, 'w'),
            ('date', 'วันที่', 160, 'center'), ('time', 'เวลา', 140, 'center'),
            ('status', 'สถานะ', 140, 'center')]:
            self.table.heading(key, text=title)
            self.table.column(key, width=width, minwidth=80, anchor=anchor, stretch=True)
        scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.table.pack(side='left', fill='both', expand=True)
        self.table.tag_configure('booked', foreground='#9BA1AE')
        self.table.bind('<<TreeviewSelect>>', self.update_selection)

        footer = tk.Frame(schedule_card, bg=WHITE)
        footer.pack(fill='x', padx=24, pady=20)
        self.status_label = self.label(footer, 'กำลังเชื่อมต่อฐานข้อมูล...', 10, MUTED)
        self.status_label.pack(side='left')
        self.book_button = self.button(footer, 'ยืนยันการจองคิว  →', self.book_queue)
        self.book_button.pack(side='right')
        self.book_button.configure(state='disabled')

        self.label(self.root, 'BEAUTY CLINIC  •  YOUR BEAUTY, OUR CARE', 9, MUTED, bg=BG).pack(pady=(0, 16))

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'doctor_booking'),
            )
            self.load_schedules()
        except mysql.connector.Error as e:
            self.status_label.config(text='เชื่อมต่อฐานข้อมูลไม่สำเร็จ')
            messagebox.showerror('Database Error', f'ไม่สามารถเชื่อมต่อ MySQL ได้\n\n{e}\n\nตรวจสอบ DB_PASSWORD และการเปิด MySQL')

    def load_schedules(self):
        if not self.conn:
            return
        try:
            self.conn.ping(reconnect=True, attempts=2, delay=1)
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT s.schedule_id, d.doctor_name, s.schedule_date, s.schedule_time,
                       CASE WHEN EXISTS (
                           SELECT 1 FROM QueueBooking q WHERE q.schedule_id = s.schedule_id
                       ) THEN 1 ELSE 0 END AS booked
                FROM Schedule s
                JOIN Doctor d ON s.doctor_id = d.doctor_id
                ORDER BY s.schedule_date, s.schedule_time, d.doctor_name
            ''')
            records = cursor.fetchall()
            cursor.close()
            for item in self.table.get_children():
                self.table.delete(item)
            self.rows.clear()
            free_count = 0
            for schedule_id, doctor, date, time, booked in records:
                free_count += not booked
                item = self.table.insert('', 'end', values=(schedule_id, doctor, str(date), str(time),
                                            'จองแล้ว' if booked else 'ว่าง'),
                                         tags=('booked',) if booked else ())
                self.rows[item] = (schedule_id, bool(booked))
            self.status_label.config(text=f'ทั้งหมด {len(records)} ช่วงเวลา  •  ว่าง {free_count} ช่วงเวลา')
            self.book_button.config(state='disabled')
        except mysql.connector.Error as e:
            self.status_label.config(text='โหลดตารางไม่สำเร็จ')
            messagebox.showerror('Database Error', str(e))

    def update_selection(self, event=None):
        selected = self.table.selection()
        allowed = bool(selected and selected[0] in self.rows and not self.rows[selected[0]][1])
        self.book_button.config(state='normal' if allowed else 'disabled')

    def book_queue(self):
        raw_id = self.member_entry.get().strip()
        if not raw_id.isdigit() or int(raw_id) < 1:
            messagebox.showwarning('ข้อมูลไม่ครบ', 'กรุณากรอก Member ID เป็นตัวเลขจำนวนเต็มบวก')
            return
        selected = self.table.selection()
        if not selected or selected[0] not in self.rows:
            messagebox.showwarning('ข้อมูลไม่ครบ', 'กรุณาเลือกช่วงเวลาที่ต้องการจอง')
            return
        schedule_id, booked = self.rows[selected[0]]
        if booked:
            messagebox.showwarning('ไม่สามารถจองได้', 'ช่วงเวลานี้ถูกจองแล้ว')
            return
        values = self.table.item(selected[0], 'values')
        if not messagebox.askyesno('ยืนยันการจอง',
                f'แพทย์: {values[1]}\nวันที่: {values[2]}\nเวลา: {values[3]}\nMember ID: {raw_id}\n\nยืนยันการจองคิว?'):
            return
        cursor = None
        try:
            self.conn.ping(reconnect=True, attempts=2, delay=1)
            cursor = self.conn.cursor()
            cursor.execute('SELECT 1 FROM QueueBooking WHERE schedule_id = %s LIMIT 1', (schedule_id,))
            if cursor.fetchone():
                messagebox.showwarning('ไม่สามารถจองได้', 'ช่วงเวลานี้ถูกจองแล้ว กรุณาเลือกเวลาอื่น')
                self.load_schedules()
                return
            cursor.execute('''
                INSERT INTO QueueBooking (member_id, schedule_id, queue_number, status)
                VALUES (%s, %s, 1, 'Confirmed')
            ''', (int(raw_id), schedule_id))
            self.conn.commit()
            messagebox.showinfo('จองสำเร็จ', 'จองคิวสำเร็จแล้ว ✓')
            self.load_schedules()
        except mysql.connector.Error as e:
            if self.conn:
                self.conn.rollback()
            messagebox.showerror('จองไม่สำเร็จ', str(e))
        finally:
            if cursor:
                cursor.close()

    def close(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    BookingApp(root)
    root.mainloop()
