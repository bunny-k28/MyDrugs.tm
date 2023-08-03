import os
import json
import qrcode
import string
import random
import dotenv
import hashlib
import sqlite3
import datetime
import smtplib, ssl

from pyotp import TOTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import check_password_hash, generate_password_hash


class User:
    def __init__(self, username: str|None=None):
        self.username = username
        self.usernames = list()
        self.safeCode = '******'
        self.user_data = {'password': str(), 'userID': str(), 'fullname': str(),
                        'email': str(), 'address': str(), 'PINcode': int()}

    def allowed_file(self, filename: str):
        self.ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def filter_data(self, data_pack):
        return [data[0] for data in data_pack]

    def get_user_data(self, data: str|None=None):
        self.db = sqlite3.connect('Database/mydrugs_database.db')
        self.sql = self.db.cursor()

        try: 
            self.sql.execute(f"SELECT password_hash FROM login_dets WHERE username=?", (self.username,))
            self.secure_password = self.sql.fetchone()[0]
            
            self.sql.execute("SELECT * FROM user_dets WHERE username=?", (self.username,))
            self.data = self.sql.fetchall()[0]

        except Exception: return (False, "Invalid username")

        finally: self.sql.close(); self.db.close()

        self.user_data = {'password': self.secure_password, 
                    'userID': self.data[1], 
                    'fullname': self.data[2] ,
                    'email': self.data[3], 
                    'address': self.data[4], 
                    'PINcode': int(self.data[5])}

        if data is None: return (True, self.user_data)
        else: return (True, self.user_data[data])

    def create_userID(self, id_len: int=6, include_puntuations: bool=False):
        self.r_file = os.path.join('Database', 'user_UID_logs.txt')

        with open(self.r_file, 'r') as self.log_file:
            self.available_logs = self.log_file.readlines()

        for i in self.available_logs:
            self.available_logs[self.available_logs.index(i)] = i[:-1]

        while True:
            if include_puntuations is False:
                self.uid = ''.join(
                    random.choice(string.ascii_letters + string.digits) 
                    for _ in range(id_len))

            elif include_puntuations is True:
                self.uid = ''.join(
                    random.choice(string.ascii_letters + string.digits + string.punctuation) 
                    for _ in range(id_len))

            self.uid = str(self.username[0] + self.uid + self.username[-1])
            self.uid = hashlib.md5(self.uid.encode()).hexdigest()

            if self.uid in self.available_logs: continue
            else: 
                with open(self.r_file, 'a') as self.log_file: self.log_file.write(f'{self.uid}\n')
                break

        return self.uid

    def create_2FA_code(self, code_len: int=6, type: str="int"):
        if type == "int": self.active_type_content = string.digits
        if type == "str": self.active_type_content = string.ascii_letters
        if type == "hybrid": self.active_type_content = string.ascii_letters + string.digits

        self.safeCode = ''.join(random.choice(self.active_type_content) 
                    for _ in range(code_len))

    def get_available_users(self):
        self.db = sqlite3.connect('Database/mydrugs_database.db')
        self.sql = self.db.cursor()
        
        try:
            self.sql.execute("SELECT username FROM userLogins")
            self.usernames = self.sql.fetchall()
        except Exception: pass
        finally: self.sql.close(); self.db.close()

        try: 
            self.usernames = self.filter_data(self.usernames)
            self.usernames.remove(self.username)
        except Exception: self.usernames = []

    def login(self, password: str):
        self.pswd = self.get_user_data('password')
        if self.pswd[0]: return bool(check_password_hash(self.pswd[-1], password))
        else: return False

    def login_with_email(self, email: str):
        self.db = sqlite3.connect('Database/mydrugs_database.db')
        self.sql = self.db.cursor()

        try:
            self.sql.execute("SELECT email FROM user_dets")
            self.emails = self.sql.fetchall()
        except Exception: pass

        self.emails = self.filter_data(self.emails)
        try:
            self.sql.execute("SELECT username FROM user_dets WHERE email=?", (email,))
            self.username = self.sql.fetchone()[0]
        except Exception: pass
        finally: self.sql.close(); self.db.close();

        if email in self.emails: return True
        else: return False

    def register_user(self):
        self.signup_validity_flag = False
        
        self.db = sqlite3.connect('Database/mydrugs_database.db')
        self.sql = self.db.cursor()

        self.fullname = self.user_data["fullname"]
        self.email = self.user_data["email"]
        self.address = self.user_data["address"]
        self.PINcode = int(self.user_data["PINcode"])

        self.userID = self.create_userID()
        self.password = generate_password_hash(self.user_data["password"], 'sha256')

        try:
            self.sql.execute("""INSERT INTO login_dets(username, password_hash) 
                        VALUES(?, ?)""", (self.username, self.password))
            self.sql.execute("""INSERT INTO user_dets(username, userID, fullname, email, address, PINcode) 
                        VALUES(?, ?, ?, ?, ?, ?)""", (self.username, self.userID, 
                                                      self.fullname, self.email, 
                                                      self.address, self.PINcode))
            self.db.commit()
 
            open(f'Database/store/cart/{self.username}.json', 'x').close()
            os.mkdir(f'Database/store/Purchases/{self.username}')
            with open(f'Database/store/cart/{self.username}.json', 'w') as self.ujfile:
                json.dump({}, self.ujfile, indent=4)
            self.signup_validity_flag = True

        except Exception as E: 
            print("Error while registering the user\nError:", E)
            self.signup_validity_flag = False

        finally: self.sql.close(); self.db.close()

        return self.signup_validity_flag

    def update_user_data(self):
        self.update_status_flag = False

        self.db = sqlite3.connect("Database/mydrugs_database.db")
        self.sql = self.db.cursor()

        try:
            self.sql.execute(f"""UPDATE user_dets SET fullname='{str(self.user_data["fullname"])}' 
                        WHERE username='{self.username}'""")
            self.sql.execute(f"""UPDATE user_dets SET email='{str(self.user_data["email"])}' 
                        WHERE username='{self.username}'""")
            self.sql.execute(f"""UPDATE user_dets SET address='{str(self.user_data["address"])}' 
                        WHERE username='{self.username}'""")
            self.sql.execute(f"""UPDATE user_dets SET PINcode={int(self.user_data["PINcode"])} 
                        WHERE username='{self.username}'""")
            self.db.commit()

            self.update_status_flag = True

        except Exception as E: print("Error: ", E); self.update_status_flag = False

        finally: self.sql.close(); self.db.close()

        return self.update_status_flag

    def delete_user_account(self):
        self.delete_status_flag = False
        self.userID = self.get_user_data("userID")[-1]

        self.db = sqlite3.connect("Database/mydrugs_database.db")
        self.sql = self.db.cursor()

        try:
            self.sql.execute("DELETE FROM login_dets WHERE username=?", (self.username,))
            self.sql.execute("DELETE FROM user_dets WHERE username=?", (self.username,))
            self.sql.execute("DELETE FROM user_wallet WHERE userID=?", (self.userID,))

            self.db.commit()

            self.sql.close(); self.db.close()

            if f'{self.username}.json' in os.listdir('Database/store/cart'): 
                os.remove(f'Database/store/cart/{self.username}.json')
            else: pass

            if f'wel{self.userID}let.log' in os.listdir('Database/store/wallet'): 
                os.remove(f'Database/store/wallet/{self.userID}.log')
            else: pass

            for filename in os.listdir('static/images/User_profileImages'):
                if self.username in filename:
                    os.remove(f'static/images/User_profileImages/{filename}')
                    break
                else: continue

            self.delete_status_flag = True

        except Exception: self.delete_status_flag = False

        return self.delete_status_flag

    def greeting(self):
        self.time = datetime.datetime.now().hour

        if self.time < 12: return "Good Morning" + ", " + self.username
        elif self.time <= 15: return "Good Afternoon" + ", " + self.username
        else: return "Good Evening" + ", " + self.username

    def send_mail(self, subject: str):
        self.date = datetime.datetime.now().strftime('%d-%m-%Y')
        self.time = datetime.datetime.now().strftime('%I:%M')

        self.HOST_SSID = dotenv.get_key("Database/secrets.env", "HOST_SSID")
        self.HOST_PSWD = dotenv.get_key("Database/secrets.env", "HOST_PSWD")

        self.SMTP_SERVER = dotenv.get_key("Database/secrets.env", "SMTP_SERVER")
        self.SERVER_PORT = dotenv.get_key("Database/secrets.env", "SERVER_PORT")

        self.message = MIMEMultipart()

        try: self.user_email = self.get_user_data("email")[-1]
        except Exception as E: print(f'\nError in mail process\nError: {E}\n')

        if subject in ["2FA", "pswd-reset", 'password-reset', None]: 
            self.create_2FA_code()
            
            self.message["Subject"] = 'Password Reset Request for MyDrugs Account'
            self.body = f"""<html>
            <h3>Your 2FA Code for <em><u>Password Reset</u></em> is: </h3>
            <spam><h1 style="background-color: yellow;"><b>{self.safeCode}</b></h1></spam><br>
            <h3>Password-Reset Request generated on {self.date} at {self.time}</h3>
            </html>"""

        elif subject in ["login-2", "forgot-pswd-login", "safe-code", "forgot-password-login"]:
            self.create_2FA_code(16, 'hybrid')
            
            self.message["Subject"] = 'Login Safe-Code for MyDrugs Account'
            self.body = f"""<html>
            <h3>Your safe code for <em><u>Loggin-In</u></em> to MyDrugs account is: </h3>
            <spam><h1 style="background-color: yellow;"><b>{self.safeCode}</b></h1></spam><br>
            <h3>Safe-Code login Request generated on {self.date} at {self.time}</h3>
            </html>"""

        elif subject in ['pswd-changed', 'new-pswd', 'password-changed', 'new-password']:
            self.message["Subject"] = 'Password Changed for MyDrugs Account'
            self.body = f"""<html>
            <h2>Your password for MyDrugs account has been changed.</h2>
            If it's not you, please contact us immediately.<br>
            <h3>Password changed on {self.date} at {self.time}</h3>
            </html>"""

        elif subject in ['register', 'new-user', 'sign-up', 'signup']:
            self.message["Subject"] = 'Welcome to MyDrugs'
            self.body = f"""<html><h2>{self.greeting()}</h2><br>
            Thanks for registering with us. We sell premium quality <b>DRUGS</b> at affordable prices.<br>
            Just select the drug you want to buy and add it to your cart. We will deliver it to your doorstep.<br>
            If you have any questions, please contact us through<br>
                ~ <b><a href="mydrugs.allhelp@gmail.com">Mail</a></b> or<br>
                ~ <b><a href="https://api.whatsapp.com/send?phone=8745951248&text=MyDrugs.com">WhatsApp</a></b>

            <br><br>

            Thanks,<br>
            MyDrugs Team
            </html>"""

        elif subject in ['delete-account', 'user-delete', 'user-removed']:
            self.message["Subject"] = 'Account Deleted for MyDrugs'
            self.body = f"""<html><h2>{self.greeting()}</h2><br>
            Your account has been deleted from our database.<br>
            Hope you had a great time with us. And Hope you'll join us again soom.<br>

            <h3>Account deleted on {self.date} at {self.time}</h3>
            </html>"""

        self.message["From"] = "MyDrugs.com"
        self.message["To"] = self.user_email

        try:
            self.message.attach(MIMEText(self.body, "html"))
            
            self.text = self.message.as_string()
            self.context = ssl.create_default_context()

            with smtplib.SMTP_SSL(self.SMTP_SERVER, int(self.SERVER_PORT), context=self.context) as self.server:
                self.server.login(self.HOST_SSID, self.HOST_PSWD)
                self.server.sendmail(self.HOST_SSID, self.user_email, self.text)

            return True

        except: return False


class UserAuthentication:
    def __init__(self, username: str|None=None):
        self.OTP = TOTP('base32secret3232')
        self.username = username

    def create_auth_qr(self):
        try:
            self.qr_data = self.OTP.provisioning_uri(name=f'{self.username}', 
                                                     issuer_name=f'MyDrugs.com')
            self.QR = qrcode.make(self.qr_data)

            self.QR.save(f'static/images/archives/{self.username}.png')
            return True
        except Exception as E: print(f"Error saving QR image\nError: {E}"); return False

    def verify_user_auth(self, key):
        self.OTP.now()
        return self.OTP.verify(key)


class Shop:
    def __init__(self, username: str|None=None):
        self.username = username
        self.user_cart = dict()
        self.item_data = {"product_name": str(), 
                        "product_img": str(), 
                        "product_quantity": int(),
                        "product_price": int(),
                        "total_price": str(),
                        "product_status": str()}

    def read_json(self, file: str, key: str|None=None):
        try:
            with open("Database/store/" + file, 'r') as self.jfile: 
                self.jdata = json.load(self.jfile)
        except IOError as IOE: print(f"Error reading json file\nError: {IOE}")

        if key is None: return self.jdata
        else: return self.jdata[key]

    def get_checkout_amount(self):
        self.checkout_amount = 0
    
        self.cart_data = self.read_json(f'cart/{self.username}.json')
        for cdata in self.cart_data:
            self.checkout_amount += int(self.cart_data[cdata]['total_price'])

        return self.checkout_amount

    def add_item_to_cart(self, pid: str):
        try:
            self.cart_data = self.read_json(f'cart/{self.username}.json')

            if pid in self.cart_data.keys():
                self.cart_data[pid]["product_quantity"] += self.item_data["product_quantity"]
                self.cart_data[pid]["total_price"] += int(self.item_data["product_quantity"] * self.item_data["product_price"])
            else: self.cart_data[pid] = self.item_data

            with open(f"Database/store/cart/{self.username}.json", 'w') as self.jfile:
                json.dump(self.cart_data, self.jfile, indent=4)

            return True

        except Exception: return False

    def remove_from_cart(self, pid: str):
        self.cart_data = self.read_json(f'cart/{self.username}.json')
        self.cart_data.pop(pid)

        with open(f"Database/store/cart/{self.username}.json", 'w') as self.jfile:
            json.dump(self.cart_data, self.jfile, indent=4)

        return True


class Wallet(User):
    def __init__(self, username: str):
        super().__init__(username)
        self.userIDs = []
        self.username = username
        self.purchase_data = dict()
        self.wallet_data = {'log': str(), 'amount': int()}
        self.userID = super().get_user_data('userID')[-1]

    def wallet_available(self):
        self.db = sqlite3.connect('Database/mydrugs_database.db')
        self.sql = self.db.cursor()
        
        try:
            self.sql.execute("SELECT userID FROM user_wallet")
            self.userIDs = self.sql.fetchall()
        except Exception: pass
        finally: self.sql.close(); self.db.close()

        try: self.userIDs = super().filter_data(self.userIDs)
        except Exception: self.userIDs = []

        if self.userID in self.userIDs: return True
        else: return False

    def login(self, wallet_password: str):
        self.db = sqlite3.connect('Database/mydrugs_database.db')
        self.sql = self.db.cursor()

        self.sql.execute(f"SELECT password_hash FROM user_wallet WHERE userID=?", (self.userID,))
        self.secure_password = self.sql.fetchone()[0]
        self.sql.close(); self.db.close()

        return check_password_hash(self.secure_password, wallet_password)

    def make_payment(self, amount: int):
        self.payment_status = list()

        if int(self.wallet_data['amount']) >= amount:
            self.db = sqlite3.connect('Database/mydrugs_database.db')
            self.sql = self.db.cursor()
            
            try:
                self.wallet_data['amount'] -= amount
                self.sql.execute(f"""UPDATE user_wallet 
                                     SET amount={self.wallet_data['amount']}, 
                                     WHERE userID={self.userID}; """)
                self.db.commit()

                self.orderNum = os.listdir(f'Database/store/Purchases/{self.username}').__len__()
                self.filePath = f'Database/store/Purchases/{self.username}/order#{self.orderNum+1}.json'
                open(self.filePath, 'x').close()

                self.purchase_data["order_no"] = self.orderNum
                self.purchase_data["trackID"] = hash(id(self.orderNum))
                self.purchase_data["order_amnt"] = amount
                self.purchase_data["order_status"] = "Order Placed"

                with open(self.filePath, 'w') as self.POFile:
                    json.dump(self.purchase_data, self.POFile, indent=4)

                self.payment_status = [True]

            except Exception as E: self.payment_status = [False, 'Unable to make payment']
            finally: self.sql.close(); self.db.close()

        else: self.payment_status = [False, 'Low ballance in wallet!']

        return self.payment_status

    def get_wallet_data(self):
        self.db = sqlite3.connect('Database/mydrugs_database.db')
        self.sql = self.db.cursor()

        self.sql.execute(f"SELECT amount FROM user_wallet WHERE userID=?", (self.userID,))
        self.wallet_data['amount'] = self.sql.fetchone()[0]
        self.sql.close(); self.db.close()

        with open(f'Database/store/wallet/wal{self.userID}let.log', 'r') as walletLog:
            self.wallet_data['log'] = walletLog.read()

    def create_wallet(self, wallet_password):
        self.wallet_setup_status = False

        self.db = sqlite3.connect('Database/mydrugs_database.db')
        self.sql = self.db.cursor()

        try:
            self.sql.execute("""INSERT INTO user_wallet(userID, password_hash, amount) 
                        VALUES(?, ?, ?)""", (self.userID, 
                                             generate_password_hash(wallet_password), 
                                             0,))
            self.db.commit()

            with open(f'Database/store/wallet/wal{self.userID}let.log', 'x') as _:\
            self.wallet_setup_status = True

        except Exception as E:
            print(f'\nError setting up wallet\nError: {E}\n')
            self.wallet_setup_status = False

        finally: self.sql.close(); self.db.close()
        return self.wallet_setup_status

    def delete_wallet(self):
        self.wallet_delete_status = False

        self.db = sqlite3.connect('Database/mydrugs_database.db')
        self.sql = self.db.cursor()

        try:
            self.sql.execute('DELETE FROM user_wallet WHERE userID=?', (self.userID,))
            self.db.commit()

            if f'wel{self.userID}let.log' in os.listdir('Database/store/wallet'):\
            os.remove(f'Database/store/wallet/{self.userID}.log')
            else: pass
            self.wallet_delete_status = True
            
        except Exception as E:
            print(f"\nError deleting wallet\nError: {E}\n")
            self.wallet_delete_status = False

        finally: self.sql.close(); self.db.close()
        return self.wallet_delete_status            
