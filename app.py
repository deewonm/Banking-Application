# The following is your own personal bank account I have created for you
# User ID: dgb1
# Password: best_lecturer
# You don't have to use this account but i thought i would save you the time :)
# The admin account credentials are below
# User ID: cheeseburger
# Password: 3781

from flask import Flask, render_template, session, redirect, url_for, request
from database import get_db, close_db
from forms import RegistrationForm, LoginForm, DepositForm, WithdrawForm, TransferForm, AccountStatusForm, DeleteAccountForm, AdminDeleteAccountForm, AdminDepositForm, AdminWithdrawForm, FreezeAccountForm, NotifyUserForm
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import random, string
from datetime import datetime

app = Flask(__name__)

API_URL = "KEY"
app.teardown_appcontext(close_db)
app.config["SECRET_KEY"] = "key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Manually creating the Admin account, when the app is run
def master_account():
    db = get_db()
    master_user_id = "cheeseburger"
    master_password = "3781"
    exists = db.execute("""
                    SELECT user_id FROM accounts WHERE user_id = ?;""",
                    (master_user_id,) ).fetchone()
    
    if not exists:
        hashed_password = generate_password_hash(master_password)
        db.execute("""
                   INSERT INTO accounts (user_id, password, role, balance, status) 
                   VALUES (?, ?, ?, ?, ?)""",
                   (master_user_id, hashed_password, "administrator", 0, "active"))
        
        db.commit()

with app.app_context():  # the decorator before_first_request was removed from flask so i used app_context() as an alternative, link in next comment
    master_account()       # https://stackoverflow.com/questions/73570041/flask-deprecated-before-first-request-how-to-update





admin_user = "cheeseburger"


# generating random and UNIQUE ! ibans, bics, and acc numbers for each account that gets created
def generate_iban():
    characters = string.ascii_uppercase + string.digits
    rand_iban = "".join(random.choice(characters) for _ in range(20))
    return "IE" + rand_iban

def generate_bic():
    characters = string.ascii_uppercase + string.digits
    rand_bic = "".join(random.choice(characters) for _ in range(8))
    return "UCC" + rand_bic

def generate_account_number():
    number = "".join(random.choice(string.digits) for _ in range(15))
    return number

def generate_balance():
    balance = 0
    return balance
 
# Starting route / home route
@app.route("/")
def home():
    return render_template("home.html")


# This code was used from lecture 12
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        confirm_password = form.confirm_password.data
        db = get_db()
        conflict = db.execute("""SELECT * FROM accounts
                              WHERE user_id = ?;
                              """, (user_id,)).fetchone()
        
        if conflict is not None:
            form.user_id.errors.append("User id conflicts with another")
        else:
            iban = generate_iban()
            bic = generate_bic()
            account_number = generate_account_number()
            db.execute("""INSERT INTO accounts (user_id, password, iban, bic, account_number)
                            VALUES (?, ?, ?, ?, ?);
                       """, (user_id, generate_password_hash(password), iban, bic, account_number) )
            # this execute is not from lectures, it just adds transaction info to seperate db
            db.execute("""INSERT INTO transactions (user_id, amount, date, description)
                       VALUES (?, ?, ?, ?)""",
                       (user_id, "€10.99", "03-01-2026", "Welcome Bonus"))
            db.commit()
            return redirect(url_for("login"))
    return render_template("register.html", form=form, title="Register")

# Code from lecture 12
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        db = get_db()
        matching_user = db.execute("""SELECT * FROM accounts
                                   WHERE user_id = ?;
                                   """, (user_id,)).fetchone()
        if matching_user is None:
            form.user_id.errors.append("Unknown User ID")
        elif not check_password_hash(matching_user["password"], password):
            form.password.errors.append("Unknown Password")
        else:
            session.clear()
            session["user_id"] = user_id
            if user_id == "cheeseburger":
                return redirect(url_for("admin"))
            
            next_page = request.args.get("next")
            if not next_page:
                next_page = url_for("dashboard")
            return redirect(next_page)
    return render_template("login.html", form=form, title="Login")


# code from lecture 12
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# Route to dashboard or main home page
@app.route("/dashboard")
def dashboard():
    db = get_db()
    if "user_id" not in session:
        return redirect(url_for("home"))
    card = db.execute(
        """SELECT user_id, iban, bic, account_number, balance FROM accounts
            WHERE user_id = ?;""",
            (session["user_id"],) ).fetchone()
    transactions = db.execute("""
                              SELECT id, amount, date, description
                              FROM transactions
                              WHERE user_id = ?
                              ORDER BY date DESC
                              LIMIT 4;""", (session["user_id"],) ).fetchall()
    return render_template("dashboard.html", transactions=transactions, 
                           card_name=card["user_id"], title="Dashboard",
                           iban=card["iban"], bic=card["bic"], account_number=card["account_number"],
                           balance=card["balance"])


# Route for user depositing
@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    form = DepositForm()
    if form.cancel.data:
            return redirect(url_for("dashboard"))
    db = get_db()
    account = db.execute("""SELECT status FROM accounts
                              WHERE user_id = ?;""", (session["user_id"],)).fetchone()
    
    if form.validate_on_submit():
        if account["status"] == "Freeze":
            return render_template("deposit.html", form=form, title="Deposit",
                                   message="Deposit Failed: Account is frozen")
        
        deposit_amount = form.deposit.data
        user_id = session["user_id"]
        db.execute("""UPDATE accounts 
                   SET balance = balance + ? 
                   WHERE user_id = ?;""",(deposit_amount, user_id))
        db.execute("""INSERT INTO transactions (user_id, amount, date, description)
                   VALUES (?, ?, ?, ?)""",(user_id, deposit_amount, datetime.now(), "Deposit"))
        db.commit()
        return redirect(url_for("dashboard"))
    return render_template("deposit.html", form=form, title="Deposit")

# Route for user withdrawing
@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    form = WithdrawForm()
    if form.cancel.data:
            return redirect(url_for("dashboard"))
    
    db = get_db()
    account = db.execute("""SELECT status FROM accounts
                              WHERE user_id = ?;""", (session["user_id"],)).fetchone()
    
    if form.validate_on_submit():
        if account["status"] == "Freeze":
            return render_template("withdraw.html", form=form, title="Withdraw Funds",
                                   message="Withdraw Failed: Account is frozen")
        
        withdraw_amount = form.withdraw.data
        user_id = session["user_id"]
        account = db.execute("""SELECT balance
                             FROM accounts
                             WHERE user_id = ?;""",(user_id,)).fetchone()
        balance = account["balance"]
        if withdraw_amount > balance:
            return render_template("withdraw.html", form=form, error="Transaction is unable to process due to Incufficent funds")
        
        db.execute("""UPDATE accounts
                       SET balance = balance - ?
                       WHERE user_id = ?;""", (withdraw_amount, user_id))
        db.execute("""INSERT INTO transactions (user_id, amount, date, description)
                       VALUES (?, ?, ?, ?)""",
                       (user_id, -withdraw_amount, datetime.now(), "Withdraw"))
        db.commit()

        return redirect(url_for("dashboard"))
    return render_template("withdraw.html", form=form, title="Withdraw")

# Route for user transferring funds
@app.route("/transfer_funds", methods=["GET", "POST"])
def transfer_funds():
    if "user_id" not in session:
        return redirect(url_for("dashboard"))
    db = get_db()
    form = TransferForm()

    if form.cancel.data:
        return redirect(url_for("dashboard"))
    
    sender_account = db.execute("""SELECT status FROM accounts
                              WHERE user_id = ?;""", (session["user_id"],)).fetchone()
    
    if form.validate_on_submit():
        if sender_account["status"] == "Freeze":
            return render_template("transfer.html", title="Transfer Funds", form=form, 
                                   message="Transaction failed: Account frozen")
        sender = session["user_id"]
        receiver_user = form.receiver_user.data
        receiver_iban = form.receiver_iban.data
        amount = form.transfer.data
        confirm = form.confirm_transfer.data
        message = form.message.data

        # A few error checks
        if amount != confirm:
            return render_template("transfer.html", form=form, error="The transfer amounts do not match")
        receiver = db.execute("""SELECT user_id FROM accounts
                              WHERE user_id = ?
                              AND iban = ?;""",(receiver_user, receiver_iban)).fetchone()
        if receiver is None:
            return render_template("transfer.html", form=form, error="Username and IBAN do not match a registered account")
        
        if receiver_user == sender:
            return render_template("transfer.html", form=form, error="Cannot transfer to your own account!")
        
        sender_account = db.execute("""SELECT balance
                                    FROM accounts
                                    WHERE user_id = ?;""",(sender,)).fetchone()
        balance = sender_account["balance"]

        if amount > balance:
            return render_template("transfer.html", form=form, error="Insufficent Funds")
        
        account = db.execute("""SELECT status FROM accounts
                              WHERE user_id = ?;""", (session["user_id"],)).fetchone()
        
        if account["status"] == "frozen":
            return render_template("transfer.html", form=form, title="Deposit",
                                   message="Transaction Failed: Account is frozen")
        
        # Updating both sender and receiver accounts
        db.execute("""UPDATE accounts 
                   SET balance = balance - ? 
                   WHERE user_id = ?""",(amount, sender))
        
        db.execute("""UPDATE accounts 
                   SET balance = balance + ? 
                   WHERE user_id = ?""",(amount, receiver_user))
        
        db.execute("""INSERT INTO transactions (user_id, amount, date, description)
                   VALUES (?, ?, datetime("now"), ?)""",
                   (receiver_user, amount, f"Transferring from {sender}: {message}"))

        # notification system for when funds are sent between accounts
        db.execute("""INSERT INTO notifications (user_id, message, date)
                   VALUES (?, ?, datetime("now"));""",(receiver_user, f"You received €{amount} from {sender}"))
        
        db.execute("""INSERT INTO notifications (user_id, message, date)
                   VALUES (?, ?, datetime("now"));""",(sender, f"You sent €{amount} from {receiver_user}"))
        
        db.commit()

        return redirect(url_for("dashboard"))
    return render_template("transfer.html", form=form, title="Transfer Funds")
        
        
# route for transaction history of user
@app.route("/transaction_history")
def transaction_history():
    if "user_id" not in session:
        return redirect(url_for("home"))
    db = get_db()
    transactions = db.execute("""SELECT id, amount, date, description
                              FROM transactions
                              WHERE user_id = ?;""",(session["user_id"],)).fetchall()
    return render_template("transactions.html", transactions=transactions, title="Transaction History")

# all notifications for user
@app.route("/notifications")
def notifications():
    if "user_id" not in session:
        return redirect(url_for("home"))
    db = get_db()
    notifications = db.execute("""SELECT message, date, read
                               FROM notifications
                               WHERE user_id = ?
                               ORDER BY date DESC;""",(session["user_id"],)).fetchall()
    db.execute("""UPDATE notifications
               SET read = 1
               WHERE user_id = ?;""", (session["user_id"],)).fetchall()
    db.commit()
    
    return render_template("notifications.html", notifications=notifications, title="Notifications")

# user settings, freeze account and delete account
@app.route("/user_settings", methods=["GET", "POST"])
def user_settings():
    if "user_id" not in session:
        return redirect(url_for("home"))
    
    db = get_db()
    account = db.execute("""SELECT status, balance FROM accounts
                      WHERE user_id = ?;""", (session["user_id"],)).fetchone()
    status_form = AccountStatusForm(status=account["status"])
    delete_form = DeleteAccountForm()
    status_message = ""
    delete_message = ""

    if status_form.validate_on_submit():
        new_status = status_form.status.data
        if new_status == account["status"]:
            status_message = f"Account is already been {new_status}d"
        else:

            db.execute("""UPDATE accounts
                    SET status = ?
                    WHERE user_id = ?;""", (status_form.status.data, session["user_id"]))
            db.commit()
            status_message = f"New account status: {new_status}d"
            account = db.execute("""SELECT status FROM accounts
                                 WHERE user_id = ?;""", (session["user_id"],)).fetchone()
    if delete_form.validate_on_submit():
        # error checking
        if account["balance"] > 0:
            delete_message = "Account cannot be deleted. Balance must be €0.00"
        else:
            db.execute("""DELETE FROM accounts
                       WHERE user_id = ?;""", (session["user_id"],))
            db.commit()
            session.clear() # clears up when account is deleted
            return redirect(url_for("home"))
        
    return render_template("user_settings.html", title="User Settings", 
                           form=status_form, delete_form=delete_form ,account=account, 
                           status_message=status_message, delete_message=delete_message)

# ADMIN ROUTES
# Main route to the main page for admin
@app.route("/admin")
def admin():
    if session["user_id"] != admin_user:
        return redirect(url_for("home"))
    db = get_db()
    accounts = db.execute("""SELECT user_id, iban, account_number, balance, status
                          FROM accounts""").fetchall()

    deposit_form = AdminDepositForm()
    withdraw_form = AdminWithdrawForm()
    freeze_form = FreezeAccountForm()
    delete_form = AdminDeleteAccountForm()
    notify_form = NotifyUserForm()
    message = session.pop("admin_message", None)

    return render_template("admin.html", accounts=accounts, deposit_form=deposit_form, withdraw_form=withdraw_form,
                           freeze_form=freeze_form, delete_form=delete_form, notify_form=notify_form, message=message)


# Admin depositing into users accounts
@app.route("/admin_deposit/<user_id>", methods=["GET", "POST"])
def admin_deposit(user_id):
    if session["user_id"] != admin_user:
         return redirect(url_for("home"))

    form = AdminDepositForm()
    db = get_db()

    if form.validate_on_submit():
        amount = form.amount.data
        db.execute("""UPDATE accounts
                SET balance = balance + ?
                WHERE user_id = ?;""",(amount, user_id))
        db.execute("""INSERT INTO transactions (user_id, amount, date, description)
                   VALUES (?, ?, ?, ?)""",(user_id, amount, datetime.now(), "Admin - Deposit"))
        db.commit()
        session["admin_message"] = f"Deposited €{amount} into {user_id}'s account"
    return redirect(url_for("admin"))

# Admin withdrawing from a users account
@app.route("/admin_withdraw/<user_id>", methods=["GET", "POST"])
def admin_withdraw(user_id):
    if session["user_id"] != admin_user:
         return redirect(url_for("home"))
    
    form = AdminWithdrawForm()
    db = get_db()
    if form.validate_on_submit():
    
        amount = form.amount.data
        account = db.execute("""SELECT balance FROM accounts
                            WHERE user_id = ?;""", (user_id,)).fetchone()
        if account["balance"] < amount: # error checking
            session["admin_message"] = "Incuffient Funds in user's account!"
        else:
            db.execute("""UPDATE accounts
                    SET balance = balance - ?
                    WHERE user_id = ?;""", (amount, user_id))
            db.execute("""INSERT INTO transactions (user_id, amount, date, description)
                    VALUES (?, ?, ?, ?)""",
                    (user_id, -amount, datetime.now(), "Admin - Withdraw"))
            db.commit()
            session["admin_message"] = f"Withdrew €{amount} from {user_id}'s account"
    return redirect(url_for("admin"))

# Admin freeze route to freeze users accounts
@app.route("/admin_freeze/<user_id>", methods=["GET", "POST"])
def admin_freeze(user_id):
    if session["user_id"] != admin_user:
        return redirect(url_for("home"))
    
    form = FreezeAccountForm()
    db = get_db()
    if form.validate_on_submit():
        db.execute("""UPDATE accounts
                SET status = "Freeze"
                WHERE user_id = ?;""", (user_id,))
        db.commit()
        session["admin_message"] = f"Account {user_id}: Frozen"
    return redirect(url_for("admin"))

# Admin delete route to delete users accounts
@app.route("/admin_delete/<user_id>", methods=["GET", "POST"])
def admin_delete(user_id):
    if session["user_id"] != admin_user:
         return redirect(url_for("home"))
    
    form = AdminDeleteAccountForm()
    db = get_db()

    if form.validate_on_submit():
        db.execute("""DELETE FROM accounts
                WHERE user_id = ?;""", (user_id,))
        db.commit()
        session["admin_message"] = f"Account {user_id}: Successfully deleted!"
    return redirect(url_for("admin"))


# admin notify route to send a message to any user 
@app.route("/admin_notifications/<user_id>", methods=["GET", "POST"])
def admin_notification(user_id):
    if session["user_id"] != admin_user:
         return redirect(url_for("home"))
    
    form = NotifyUserForm()
    db = get_db()
    if form.validate_on_submit():
        message_string = form.message.data
        db.execute("""INSERT INTO notifications (user_id, message, date)
                VALUES (?, ?, ?)""", (user_id, "Admin: " + message_string, datetime.now()))
        db.commit()
        session["admin_message"] = f"Notification sent to {user_id}"
    return redirect(url_for("admin"))





    

 










    



