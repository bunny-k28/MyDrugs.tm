import flask
import dotenv

from __init__ import *
from datetime import timedelta
from flask import render_template, redirect, url_for, session, request


# mydrugs settings
mydrugs = flask.Flask(__name__)
mydrugs.secret_key = '3d9efc4wa651728'
mydrugs.permanent_session_lifetime = timedelta(days=1.0)

mydrugs.config['UPLOAD_FOLDER'] = "static/images/User_profileImages"
mydrugs.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# mydrugs server variabels
PORT = int(dotenv.get_key("Database/secrets.env", "PORT"))
DEBUG = bool(dotenv.get_key("Database/secrets.env", "DEBUG"))


# database connection
try:
    db = sqlite3.connect("Database/mydrugs_database.db")
    sql = db.cursor()

    sql.execute("""CREATE TABLE IF NOT EXISTS 
                login_dets(username TEXT PRIMARY KEY, password_hash HASH)""")
    sql.execute("""CREATE TABLE IF NOT EXISTS 
                user_dets(username TEXT PRIMARY KEY, userID UID, 
                fullname TEXT, email TEXT, address TEXT, PINcode INT)""")
    sql.execute("""CREATE TABLE IF NOT EXISTS 
                user_wallet(userID UID PRIMARY KEY, password_hash HASH, 
                amount INT)""")
    db.commit()

except Exception: pass
finally: sql.close(); db.close()


# index route
@mydrugs.route('/')
def indexRoute():
    return redirect(url_for('renderLogin'))


# login route
@mydrugs.route('/login')
def renderLogin():
    session["user"] = None
    session.pop("authQRcodePath", None)

    if 'authStatus' in session:
        if session["authStatus"]:
            if (("signupStatus" in session) and (session["signupStatus"] is True)):
                return render_template('login.html', 
                    form_title='Now Login to SHOP!')
            else: return render_template('login.html')
        else: return redirect(url_for('renderGoogleAuthentication'))
    else: return render_template('login.html')

@mydrugs.route('/login', methods=['POST'])
def login():
    session["user"] = request.form.get('username')

    user = User(session["user"])
    if user.login(request.form.get('pswd')):
        session['wallet_status'] = False
        del user; return redirect(url_for('shop'))
    else:
        session['user'] = None
        return render_template('login.html', 
            form_title='Incorrect Username/Password')


# email login route
@mydrugs.route('/login-through-email')
def renderEmailLogin():
    session["user"] = None
    return render_template('emailLogin.html')

@mydrugs.route('/login-through-email', methods=['POST'])
def emailLogin():
    user = User()

    if user.login_with_email(request.form.get('email')):
        verifyer = UserAuthentication()
        if verifyer.verify_user_auth(request.form.get('auth-key')):
            session['user'] = user.username
            del user, verifyer; return redirect(url_for('shop'))

        else: return render_template('emailLogin.html', 
                    form_title='Invalid Email/Auth-Key')

    else: 
        session['user'] = None
        return render_template('login.html', 
        form_title='Email/Auth-Key is incorrect!')


# logout route
@mydrugs.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('indexRoute'))


# signup route
@mydrugs.route('/signup')
def renderSignup():
    session['signupStatus'] = None
    session['tempUserName'] = None
    session["authQRcodePath"] = None
    return render_template('signup.html')

@mydrugs.route('/signup', methods=['POST'])
def signup():
    new_user = User(request.form.get('username'))

    new_user.get_available_users()
    if new_user.username in new_user.usernames: 
        return render_template('signup.html', 
        form_title='Username already taken')

    else:
        session['tempUserName'] = new_user.username

        new_user.user_data["email"] = request.form.get('email')
        new_user.user_data["fullname"] = "Not provided"
        new_user.user_data["address"] = "Address not registered"
        new_user.user_data["PINcode"] = 000000
        if request.form.get('pswd').__len__() < 8:
            return render_template('signup.html', form_title="Password too short")
        else:
            new_user.user_data["password"] = str(request.form.get('pswd'))

        if new_user.register_user():
            session['signupStatus'] = True
            user_auth = UserAuthentication(session['tempUserName'])
            if user_auth.create_auth_qr():
                session["authQRcodePath"] = f"../static/images/archives/{new_user.username}.png"
                if new_user.send_mail('register'): pass
                else: print('\n->Unable to send mail<-\n')
                del new_user, user_auth; return redirect(url_for('renderGoogleAuthentication'))
            else: return render_template('singup.html', form_title='Unable to register you.')
        else: return render_template('signup.html', 
                form_title='Unable to register you.')


# Google Auth route
@mydrugs.route('/account-authentication')
def renderGoogleAuthentication():
    session['authStatus'] = False

    if (("signupStatus" in session) and (session["signupStatus"] is True)):
        return render_template('googleAuthQR.html', 
            QRcode_path=session["authQRcodePath"])

    else: return flask.render_template_string("Page not found")

@mydrugs.route('/account-authentication', methods=['POST'])
def googleAuthentication():
    verifyer = UserAuthentication()
    if verifyer.verify_user_auth(str(request.form.get('auth-key'))):
        try: os.remove(f'static/images/archives/{session["tempUserName"]}.png')
        except OSError: pass

        try: session.pop('tempUserName', None)
        except KeyError: pass

        session['authStatus'] = True
        del verifyer; return redirect(url_for('renderLogin', registration=True))

    else: return render_template('googleAuthQR.html', 
            form_title="Incorrect Auth Key", 
            QRcode_path=session["authQRcodePath"])


# shop route
@mydrugs.route("/shop")
def shop():
    session['cartActionStatus'] = None
    session["products"] = None
    session["count"] = 0

    if "user" in session:
        shop = Shop(session["user"])
        try:
            session["products"] = shop.read_json("products.json")
            shop.user_cart = shop.read_json(f'cart/{session["user"]}.json')
            if shop.user_cart:
                session["count"] = shop.user_cart.__len__()

            del shop; return render_template("shop.html", 
                            username=session["user"], 
                            item_count=session["count"], 
                            products=session["products"])

        except Exception as E:
            return flask.render_template_string(f'Unable to load shop\nError: {E}')

    else: return redirect(url_for("logout"))


# wallet route
@mydrugs.route("/wallet")
def renderUserWallet():
    session['wallet_data'] = None
    session['userID'] = None

    if 'user' in session:
        user_wallet = Wallet(session['user'])

        if user_wallet.wallet_available():
            if session['wallet_status']:
                user_wallet.get_wallet_data()
                session['wallet_data'] = user_wallet.wallet_data
                session['userID'] = user_wallet.userID
                del user_wallet; return render_template('wallet.html', 
                                        wallet_status=True, 
                                        userID=session['userID'], 
                                        walletData=session['wallet_data'])

            else: return redirect(url_for('renderWalletLogin'))
        else: return redirect(url_for('renderSetWallet'))
    else: return redirect(url_for('logout'))


# wallet login route
@mydrugs.route("/wallet/login")
def renderWalletLogin():
    session['walletLoginStatus'] = False

    if 'user' in session:
        return render_template('walletLogin.html', 
                login_status=session['walletLoginStatus'])
    else: return redirect(url_for('logout'))

@mydrugs.route("/wallet/login", methods=['POST'])
def walletLogin():
    user_wallet = Wallet(session['user'])
    if user_wallet.login(request.form.get('walletPSWD')):
        del user_wallet; session['wallet_status'] = True
        return redirect(url_for('renderUserWallet'))
    else: return render_template('walletLogin.html', form_title='Incorrect Password!')


# wallet logout route
@mydrugs.route('/wallet/logout')
def logoutWallet():
    session['wallet_status'] = False
    return redirect(url_for('profilePageRedirect'))


# set wallet route
@mydrugs.route("/wallet/set")
def renderSetWallet():
    if 'user' in session:
        return render_template('walletSetup.html')
    else: return redirect(url_for('logout'))

@mydrugs.route("/wallet/set", methods=['POST'])
def setWallet():
    new_wallet = Wallet(session['user'])
    
    if request.form.get('walletPSWD') == request.form.get('walletCPSWD'):
        if new_wallet.create_wallet(request.form.get('walletPSWD')):
            del new_wallet; session['wallet_status'] = True
            return redirect(url_for('renderUserWallet'))

        else: return render_template('walletSetup.html', 
                    form_title='Unable to set wallet!')
    else: return render_template('walletSetup.html', 
                    form_title="Password doesn't match")


# delete wallet route
@mydrugs.route("/wallet/delete")
def deleteWallet():
    if 'user' in session:
        user_wallet = Wallet(session['user'])
        if user_wallet.delete_wallet():
            del user_wallet; return redirect(url_for('profilePageRedirect'))
        else: return render_template('wallet.html', delete_wallet=False)

    else: return redirect(url_for('logout'))


# cart route
@mydrugs.route("/cart")
def renderCart():
    session['checkout-go'] = None
    session['checkoutActive?'] = False

    if "user" in session:
        cart = Shop(session["user"])
        session["cart_data"] = cart.read_json(f'cart/{cart.username}.json')
        session["checkout_amnt"] = cart.get_checkout_amount(); del cart

        try:
            return render_template('cart.html', 
                    username=session["user"], 
                    status=session["cartActionStatus"],
                    checkout_amnt=session["checkout_amnt"], 
                    cart_items=session["cart_data"])

        except Exception as E:
            print(E)
            return render_template('cart.html', 
                    username=session["user"], 
                    status=session["cartActionStatus"],
                    checkout_amnt=session["checkout_amnt"], 
                    error="Unable to load cart items")

    else: return redirect(url_for("logout"))


# add to cart route
@mydrugs.route("/cart/add-item", methods=["POST"])
def addToCart():
    session["cart_data"] = None

    if "user" in session:
        cart = Shop(session["user"])
        try:
            cart.item_data["product_name"] = request.form["pname"]
            cart.item_data["product_img"] = request.form["pimg"]
            cart.item_data["product_quantity"] = int(request.form["quantity"])
            cart.item_data["product_price"] = int(request.form["pprice"])
            cart.item_data["total_price"] = int(cart.item_data["product_quantity"]) * int(cart.item_data["product_price"])
            cart.item_data["product_status"] = request.form["pstatus"]

            session['products'] = cart.read_json('products.json')

            if (request.form["pid"], cart.item_data["product_name"], 
                cart.item_data["product_img"], cart.item_data["product_quantity"], 
                cart.item_data["product_status"]) and (request.method == "POST"):
                if cart.add_item_to_cart(request.form["pid"]):
                    session["cart_data"] = cart.read_json(f'cart/{session["user"]}.json')
                    if session["cart_data"]:
                        session["count"] = session["cart_data"].__len__()
                        del cart; return render_template('shop.html', 
                                        products=session['products'], status=True, 
                                        item_count=session["count"])

                else: return render_template('shop.html', 
                            products=session['products'], status=False, 
                            item_count=session["count"])
            else: pass

        except Exception as E: return render_template('shop.html', 
                                    products=session['products'], status=False, 
                                    item_count=session["count"])

    else: return redirect(url_for("logout"))


# pop from cart route
@mydrugs.route('/cart/remove-item', methods=['POST'])
def removeFromCart():
    if "user" in session:
        cart = Shop(session["user"])

        try: 
            if request.form['pid'] and (request.method == "POST"):
                if cart.remove_from_cart(request.form['pid']):
                    session["cart_data"] = cart.read_json(f'cart/{session["user"]}.json')
                    session['cartActionStatus'] = True; del cart; 
                    if session['checkoutActive?']: return redirect(url_for('checkout'))
                    else: return redirect(url_for('renderCart'))

                else:
                    session['cartActionStatus'] = False
                    if session['checkoutActive?']: return redirect(url_for('checkout'))
                    else: return redirect(url_for('renderCart'))

            else: pass

        except:
            if session['checkoutActive?']: return redirect(url_for('checkout'))
            else: return redirect(url_for('renderCart'))

    else: return redirect(url_for('logout'))


# checkout route
@mydrugs.route('/cart/checkout')
def checkout():
    if 'user' in session:
        session['payment_status'] = None
        session['checkoutActive?'] = True
        session['user_data'] = dict()

        user = User(session['user'])
        user_cart = Shop(session['user'])
        session['user_data'] = user.get_user_data()[-1]
        session['checkout_amount'] = user_cart.get_checkout_amount()
        session['cart_data'] = user_cart.read_json(f"cart/{session['user']}.json")

        del user, user_cart; return render_template('checkout.html',
                                    status=session['checkout-go'], 
                                    user_data=session['user_data'],
                                    cartItems=session['cart_data'], 
                                    checkout_amount=session['checkout_amount'])

    else: return redirect(url_for('logout'))


# wallet payment route
@mydrugs.route('/cart/checkout/payment/wallet')
def renderWalletCheckout():
    if session['checkoutActive?']:
        
        if (session['user_data']['address'] == "Address not registered") and\
        (int(session['user_data']['PINcode']) == 0):
            session['checkout-go'] = False
            return redirect(url_for('checkout'))

        else: return render_template('walletPaymentAuth.html')
    else: return redirect(url_for('shop'))

@mydrugs.route('/cart/checkout/payment/wallet', methods=['POST'])
def payUsingWallet():
    user_wallet = Wallet(session['user'])
    user_wallet.get_wallet_data()
    session['payment_status'] = user_wallet.make_payment(int(session['checkout_amount']))
    if session['payment_status'][0]:
        del user_wallet; return render_template('thanks.html', 
                                order_no="order_no", 
                                trackID="trackID")

    else: return render_template('walletPaymentAuth.html', 
                payment_status=session['payment_status'][-1])


# product details route
@mydrugs.route("/shop/product-details/redirector", methods=["POST"])
def productDetails():
    session['product_det'] = None

    user_store = Shop(session["user"])
    session['product_det'] = user_store.read_json('product_det.json', request.form["pid"])
    
    del user_store; return redirect(url_for("renderProductDetails", 
                            pid=request.form["pid"], pref=request.form["pref"], 
                            product=session["product_det"][0]))

@mydrugs.route("/shop/product-details/<product>?pid=<pid>&pref=<pref>")
def renderProductDetails(product, pid, pref):
    if (("product_det" in session) and (session["product_det"] != None)):
        user_store = Shop(session["user"])
        session['products'] = user_store.read_json('products.json', pref)
        return render_template("productDetails.html", 
                pid=pid, user=session["user"], pname=product, 
                pdata=session['products'], pdet=session["product_det"][-1]) 

    else: return render_template('productDetails.html', 
                error="Unable to load product details")


# profile route
@mydrugs.route("/profile")
def profilePageRedirect():
    session["profile_img_name"] = None
    if os.listdir('static/images/User_profileImages').__len__() > 0:
        for filename in os.listdir('static/images/User_profileImages'):
            if session['user'] in filename:
                session["profile_img_name"] = filename
                break
            else: continue
    else: pass

    if "user" in session:
        return redirect(url_for("renderUserProfile", 
                username=session["user"]))
    else: return redirect(url_for("logout"))

@mydrugs.route("/profile/user:<username>")
def renderUserProfile(username):
    if "user" in session:
        user = User(session["user"])
        session["user_data"] = user.get_user_data()[-1]
        del user; return render_template('profile.html', 
                            username=username, 
                            filename = session["profile_img_name"], 
                            user_data=session["user_data"]) 

    else: return redirect(url_for("logout"))


# edit account route
@mydrugs.route("/profile/user:<username>", methods=["POST"])
def editAccountDetails(username):
    user = User(session['user'])

    user.user_data["fullname"] = str(request.form['fullname'])
    user.user_data["address"] = str(request.form['address'])
    user.user_data["PINcode"] = int(request.form['areaPIN'])
    user.user_data["email"] = str(request.form['email'])

    try:
        if request.files['file'] and user.allowed_file(request.files['file'].filename):
            session["profile_img_name"] = f"{username}." + '.png' # request.files['file'].filename.split(".")[-1]

            if session["profile_img_name"] in os.listdir("static/images/User_profileImages"):
                os.remove(os.path.join(mydrugs.config['UPLOAD_FOLDER'], session["profile_img_name"]))
                request.files['file'].save(os.path.join(mydrugs.config['UPLOAD_FOLDER'], session["profile_img_name"]))

            else: request.files['file'].save(os.path.join(mydrugs.config['UPLOAD_FOLDER'], session["profile_img_name"]))

    except Exception as E:
        print(E)
        print("Error uploading profile image")

    try:
        session['user_data'] = user.user_data
        if user.update_user_data() is True:
            del user; return render_template('profile.html', 
                        username=session['user'], user_data=session['user_data'], 
                        proFile=os.listdir("static/images/User_profileImages"), 
                        filename = session["profile_img_name"], update_status="✅")
        
        else:
            print("Error updating user info")
            return render_template('profile.html', 
                username=username, user_data=session['user_data'], 
                proFile=os.listdir("static/images/User_profileImages"), 
                filename = session["profile_img_name"], update_status="❌")

    except Exception as E:
        print("Error updating user info: ", E)
        return render_template('profile.html', 
            username=username, user_data=session['user_data'], 
            proFile=os.listdir("static/images/User_profileImages"), 
            filename = session["profile_img_name"], update_status="❌")


# delete account route
@mydrugs.route("/profile/delete")
def deleteUserAccount():
    if "user" in session:
        user = User(session["user"])
        if user.send_mail("delete-account"): pass
        else: print("\n->Unable to send mail<-\n")

        if user.delete_user_account():
            del user; return redirect(url_for("logout"))
        else: 
            session['user_data'] = user.get_user_data()[-1]
            del user; return render_template("profile.html", 
                    username=session["user"], delete_profile=False, 
                    user_data=session['user_data'])



###########################################################################
if __name__ == '__main__':

    mydrugs.run(debug=DEBUG, port=PORT)