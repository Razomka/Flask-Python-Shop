from flask import Flask, render_template, session, redirect, url_for, g, request
from database import get_db, close_db
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from forms import *
from functools import wraps
from datetime import datetime

"""
There is an admin login. The username is 'admin' and the password 'bakerylife'.
This will allow you modify stock, users and email users when searched.
Enjoy looking around.
"""



app = Flask(__name__)
app.teardown_appcontext(close_db)
app.config["SECRET_KEY"] = "THIS-IS-MY-SECRET-KEY"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.before_request
def load_logged_in_user():
    g.admin = session.get("admin", None)
    g.user = session.get("username", None)

def admin_login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.admin is None:
            return redirect(url_for("login", next=request.url))
        return view(**kwargs)
    return wrapped_view

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login", next=request.url))
        return view(**kwargs)
    return wrapped_view

@app.route("/")
def index():
    success = request.args.get("success")
    if success == "True":
        success = "Thank you for your purchase and we have saved your address for next time!"
        success2 = ""
        length = len(success)
    elif success == "False":
        success = "Thank you for your purchase! Hope you see you soon!"
        success2 = ""
        length = len(success)
    else:
        success = "Welcome to Shopping With James G."
        success2 = "Your only stop for bakery goods."
        length = len(success)
    return render_template("index.html",success=success, success2=success2, length=length)

@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        db = get_db()
        matching_user = db.execute("""SELECT * FROM users
                                        WHERE user_id = ?;""", (username,)).fetchone()
        if matching_user is None:
            form.username.errors.append("Wrong username. Please try again")
        elif matching_user["type"] == "admin" or matching_user["type"] == "Admin":
            session["admin"]  = None
            session["username"] = username
            session["admin"] = username
            return render_template("admin.html")
        elif not check_password_hash(matching_user["password"], password):
            form.password.errors.append("Wrong password, please try again")
        else:
            session["username"] = None
            session["username"] = username
            next_page = request.args.get("next")
            if not next_page:
                next_page = url_for("index")
            return redirect(next_page)
    return render_template ("login.html", form=form)

@app.route("/logout")
def logout():
    session["admin"] = None
    session["username"] = None
    return redirect(url_for("index"))

@app.route("/register", methods=["GET","POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        password2 = form.password2.data
        realname = form.realname.data
        email = form.email.data
        address = form.address.data
        data_dict={"user_id":username,"name":realname,"email":email,"address":address}

        db = get_db()
        clashing_user = db.execute("""SELECT * FROM users
                                        WHERE user_id = ?;""", (username,)).fetchone()
        if clashing_user is not None:
            form.username.errors.append("User ID has already been taken. Please enter a different one")
        else:
            db.execute("""INSERT INTO users (user_id, password) VALUES (?,?);""",(username,generate_password_hash(password)))
            db.commit()
            for key,value in data_dict.items():
                if value != "":
                    db.execute("""UPDATE users SET %s = ? WHERE user_id = ? ;""" % key,(value,username))
                    db.commit()
            return redirect( url_for("login"))
    return render_template("register.html", form=form)

@app.route("/admin")
@admin_login_required
def admin():
    return render_template("admin.html")

@app.route("/stock", methods=["GET","POST"])
@admin_login_required
def stock():
    form = StockForm()
    db = get_db()
    stock_items = db.execute("""SELECT * FROM shop;""").fetchall()
    success = ""
    if form.validate_on_submit():
        newstock = form.newstock.data
        itemremoval = form.itemremoval.data
        stockID = form.stockID.data
        stockname = form.stockname.data
        stocklevel = form.stocklevel.data
        imagename = form.imagename.data
        price= form.price.data
        description = form.description.data
        data_dict = {"id":stockID,"item":stockname,"stock":stocklevel,"imagename":imagename,"price":price,"title":description}
        spare_dict = {}
        try:
            if newstock == True and itemremoval == True:
                success = "Cannot remove and add an item"
                return render_template("stock.html", form=form, stock_items = stock_items, success=success)
            elif itemremoval == True and stockname != "":
                for key,value in data_dict.items():
                    if value != "":
                        db.execute("""DELETE FROM shop WHERE %s = ?;""" % key, (value,))
                        db.commit()
                stock_items = db.execute("""SELECT * FROM shop;""").fetchall()
                success = "Item has been removed"
                return render_template("stock.html", form=form, stock_items = stock_items, success=success)
            elif newstock == True and stockname != "":                 
                    db.execute("""INSERT INTO shop (item,stock,imagename,price,title) VALUES (?,?,?,?,?);""",(stockname,stocklevel,imagename,price,description))
                    db.commit()
                    success = "Added new item"
                    stock_items = db.execute("""SELECT * FROM shop;""").fetchall()
            else:
                for key,value in data_dict.items():
                    if value != "":
                        spare_dict[key] = value
                if len(spare_dict) == 1:
                    for key,value in data_dict.items():
                        if value != "":
                            stock_items = db.execute("""SELECT * FROM shop WHERE %s = ?;""" % key, (value,)).fetchall()
                else:
                    if len(spare_dict) > 1:
                        for key,value in data_dict.items():
                            if value != "" and stockname != "":
                                db.execute("""UPDATE shop SET %s = ? WHERE item = ?;""" %key,(value,stockname))
                                db.commit()
                                success = "Stock data has been modified"
                                stock_items = db.execute("""SELECT * FROM shop;""").fetchall()
                            elif value != "" and stockname == "" :
                                success = "Item name needed to update stock levels"
        except:
            return render_template("stock.html",stock_items = stock_items,form=form, success="Cannot insert duplicate items as a new item")
    return render_template("stock.html", form=form, stock_items = stock_items, success=success)

@app.route("/users", methods=["GET","POST"])
@admin_login_required
def users():
    form = UserForm()
    db = get_db()
    users = db.execute("""SELECT * FROM users;""").fetchall()
    success = ""
    itemname = ""
    orders_itemname = ""
    orders = ""
    if form.validate_on_submit():
        modification = form.modification.data
        removal = form.removal.data
        username = form.username.data
        password = form.password.data
        changetype = form.changetype.data
        changename = form.changename.data
        changeaddress = form.changeaddress.data
        changemail = form.changemail.data
        data_dict = {"user_id":username,"type":changetype,"name":changename,"address":changeaddress,"email":changemail}
        if removal == True and modification == True:
            success = "You cannot remove and modify an account. Please select either one or no option"
        elif removal == True and username != "":
            db.execute("""DELETE FROM users where user_id = ?;""",(username,))
            db.commit()
            users = db.execute("""SELECT * FROM users;""").fetchall()
            success = "User has been removed"
            if username == session["admin"]:
                return redirect(url_for("logout"))
        elif modification == True and username != "":
            if len(username) > 0:
                userCheck = db.execute("""SELECT * FROM users where user_id = ?;""",(username,)).fetchone()                 
                if userCheck == None:
                    db.execute("""INSERT INTO users (user_id, password) VALUES (?,?);""",(username,generate_password_hash(password)))
                    db.commit()
                    success = "Added User to Database"
                else:
                    db.execute("""UPDATE users SET user_id = ? WHERE user_id = ?;""",(username,username))
                    db.commit()
            for key,value in data_dict.items():
                if len(value) > 0:
                    db.execute("""UPDATE users SET '%s' = ? WHERE user_id = ?;""" %key,(value,username)) 
                    db.commit()
            users = db.execute("""SELECT * FROM users WHERE user_id = ?;""",(username,)).fetchall()
            if success == "":
                success = "The change has been made"
        else:
            for key,value in data_dict.items():
                if len(value) > 0:
                    if value == "None":
                        value = "NULL"
                        users = db.execute("""SELECT * FROM users WHERE %s IS %s;""" %(key,value)).fetchall()
                    else:
                        users = db.execute("""SELECT * FROM users WHERE %s = ?;""" %key,(value,)).fetchall()
            if users[0][7] != None:
                if len(users[0][7]) > 0:
                    print(users[0][7])
                    print(len(users[0][7]))
                    print(type(users[0][7]))
                    i= 0
                    orders = {}
                    orders_itemname = {}
                    while i < (len(users[0][7])-3):
                        if users[0][7][i] != " " and users[0][7][i+1] == " ":
                            if users[0][7][i+2] != " " and users[0][7][i+3] == " ":
                                orders[users[0][7][i]] = users[0][7][i+2]
                                i += 4
                            else:
                                orders[users[0][7][i]] = users[0][7][i+2]+users[0][7][i+3]
                                i += 5
                        else:
                            if orders[users[0][7][i+3]] != " " and orders[users[0][7][i+4]] == " ":                            
                                orders[users[0][7][i]] = users[0][7][i+3]
                                i += 5
                            else:
                                orders[users[0][7][i]] = users[0][7][i+3]+users[0][7][i+4]
                                i += 6
                    for key in orders:
                        print(key)
                        item = db.execute("""SELECT item FROM shop WHERE id =?;""",(key,)).fetchone()
                        orders_itemname[key] = item[0]         
            if users[0][6] != None:
                if len(users[0][6]) > 0:
                    i= 1
                    listwish = []
                    itemname = []
                    while i < (len(users[0][6])-1):
                        if users[0][6][i] != " " and users[0][6][i+1] == " ":
                            listwish.append(users[0][6][i])
                            i += 2
                        else:
                            listwish.apppend(users[0][6][i]+users[0][6][i+1])
                            i += 3
                    for value in listwish:
                        item = db.execute("""SELECT item FROM shop WHERE id =?;""",(value,)).fetchone()
                        itemname.append(item[0])
    return render_template("users.html", form=form, success=success, users=users, itemname=itemname,orders_itemname=orders_itemname, orders=orders)

@app.route("/email_user", methods=["GET","POST"])
@admin_login_required
def email_user():
    username = request.args.get("username")
    form = EmailForm()
    success = ""
    if form.validate_on_submit():
        success = "Email has been sent to " + username
    return render_template("email_user.html", form=form,username=username,success=success)

@app.route("/shop")
def shop():
    db = get_db()
    shop = db.execute("""SELECT * FROM shop;""").fetchall()
    success = request.args.get("success")
    error = request.args.get("error")
    if error == "True":
        success = "You have already added this item to your wish list, cannot re-add"
    elif success == "error":
        success = "I'm sorry, we do not have this item currently in stock."
    elif success == "True":
        success = "Item added to basket!"
    elif success == "False":
        success = "Item added to your wish list!"
    else:
        success = ""
    return render_template("shop.html",shop=shop, success=success)

@app.route("/basket")
@login_required
def basket():
    if "basket" not in session:
        session["basket"] = {}
    if session["basket"] == {}:
        return render_template("basket.html",empty=True)
    db = get_db()
    shop = db.execute("""SELECT * FROM shop;""").fetchall()
    items = {}
    total = 0
    item = {}
    success = request.args.get("success")
    if success == True:
        success = "Item has been removed by one"
    else:
        success = ""
    for id in session["basket"]:
        item = db.execute("""SELECT * FROM shop WHERE id = ?;""",(id,)).fetchone()
        items[id] = item[1]
        total = total + (item[4]*session["basket"][id])
    total = "%.2f" % total
    return render_template("basket.html",basket=session["basket"],items=items,total=total, success=success, shop=shop)

@app.route("/add_to_basket/<int:id>")
@login_required
def add_to_basket(id):
    db = get_db()
    if "basket" not in session:
        session["basket"] = {}
        session["wishlist"] = {}
    if id not in session["basket"]:
        session["basket"][id] = 0
    stockcheck = db.execute("""SELECT stock FROM shop WHERE id = ?;""",(id,)).fetchone()
    if stockcheck[0] < 0:
        success = "error"
        del session["basket"][id]
    elif stockcheck[0] > 0:
        session["basket"][id] = session["basket"][id] + 1
        success = True
    return redirect(url_for('shop',success=success))

@app.route("/remove_from_basket/<int:id>")
@login_required
def remove_from_basket(id):
    if "basket" not in session:
        success = "You do not have a basket"
        return redirect(url_for('shop',success=success))
    if session["basket"][id] <= 1:
        del session["basket"][id]
    else:    
        session["basket"][id] = session["basket"][id] - 1
    success = True
    return redirect(url_for('basket',success=success))

@app.route("/remove_from_wishlist/<int:id>")
@login_required
def remove_from_wishlist(id):
    if "wishlist" not in session:
        success = "You do not have a wish list"
        return redirect(url_for('shop',success=success))
    del session["wishlist"][id]
    success = True
    return redirect(url_for('wishlist',success=success))

@app.route("/add_to_wishlist/<int:id>")
@login_required
def add_to_wishlist(id):
    db = get_db()
    new_str = ""
    if "wishlist" not in session:
        session["wishlist"] = {}
    if id not in session["wishlist"]:
        session["wishlist"][id] = 0
    elif session["wishlist"][id] >= 1:
        error = True
        return redirect(url_for('shop',error=error))
    session["wishlist"][id] = session["wishlist"][id] + 1
    for key in session["wishlist"]:
        new_str = new_str + " " + str(key)
    db.execute("""UPDATE users SET wishlist = ? WHERE user_id = ?;""",(new_str,g.user))
    db.commit()
    success = False
    return redirect(url_for('shop',success=success))


@app.route("/wishlist", methods=["GET","POST"])
@login_required
def wishlist():
    if "wishlist" not in session:
        session["basket"] = {}
        session["wishlist"] = {}
    if session["wishlist"] == {}:
        return render_template("wishlist.html",empty=True)
    db = get_db()
    shop = db.execute("""SELECT * FROM shop;""").fetchall()
    items = {}
    success = request.args.get("success")
    if success == True:
        success = "Item has been removed from your wish list."
    else:
        success = ""
    for id in session["wishlist"]:
        item = db.execute("""SELECT * FROM shop WHERE id = ?;""",(id,)).fetchone()
        itemname = item[1]
        items[id] = itemname
    return render_template("wishlist.html",wishlist = session["wishlist"],items=items, success=success,shop=shop)

@app.route("/checkout", methods=["GET","POST"])
@login_required
def checkout():
    if "basket" not in session:
        session["basket"] = {}
        session["wishlist"] = {}
    form = CheckoutForm()
    if session["basket"] == {}:
        return render_template("checkout.html",form=form,empty=True)
    db = get_db()
    for key,value in session["basket"].items():
        stockcheck = db.execute("""SELECT stock, item FROM shop WHERE id = ?;""",(key,)).fetchone()
        if value > stockcheck[0]:
            return render_template("checkout.html",stockname=stockcheck,form=form,empty=False,error=True)
    promotion = 1
    success = ""
    if form.validate_on_submit():
        promotion = form.promotion.data
        if promotion == "Sale":
            promotion = 0.8
            success = "Voucher has been added! 20% discount applied"
        else:
            promotion = 1
            success = "This is not a valid voucher"
    items = {}
    imagenames = {}
    prices = {}
    total = 0
    minitotal = {}
    for id in session["basket"]:
        item = db.execute("""SELECT * FROM shop WHERE id =?;""",(id,)).fetchone()
        itemname = item[1]
        items[id] = itemname
        imagenames[id] = item[3]
        prices[id] = item[4]
        total = total + ((item[4]*session["basket"][id])*promotion)
        minitotal[id] = "%.2f" % ((item[4]*session["basket"][id])*promotion)
    total = "%.2f" % total
    return render_template("checkout.html",form=form,basket=session["basket"], items=items,imagenames=imagenames, prices=prices, total=total,empty=False,minitotal=minitotal,success=success)

@app.route("/purchase/<total>", methods=["GET","POST"])
@login_required
def purchase(total):
    form = PurchaseForm()
    db = get_db()
    success = ""
    shipaddress= ""
    addtodata = None
    addresscheck = db.execute("""SELECT * FROM users WHERE user_id = ?;""",(g.user,)).fetchone()
    if form.validate_on_submit():
        cardnumber = form.cardnumber.data
        datenumber = form.datenumber.data
        securitynum = form.securitynum.data
        shipaddress = form.shipaddress.data
        cardaddress = form.cardaddress.data
        addtodata = form.addtodata.data
        item_str = ""
        if datenumber < datetime.now().date():
            form.datenumber.errors.append("You card has expired. Not valid to use.")
            return render_template("purchase.html", form=form,total=total)
        for id,value in session["basket"].items():
            item_str = item_str + str(id) + " " + str(value) + " "
            db.execute("""UPDATE users SET orders = ? WHERE user_id = ?;""",(item_str,g.user))
            db.execute("""UPDATE shop SET stock = stock-? WHERE id = ?;""",(value,id))
            db.commit()
        if addtodata == True:
            db.execute("""UPDATE users SET address = ? WHERE user_id = ?;""",(shipaddress,g.user) )
            db.commit()
            success = True
            session["basket"].clear()
            return redirect(url_for("index",success=success))
        else:
            session["basket"].clear()
            success = False
        return redirect(url_for("index",success=success))
    elif addresscheck["address"] != None:
        form.shipaddress.default.append(addresscheck["address"])
    return render_template("purchase.html", form=form,success=success,shipaddress=shipaddress, addtodata=addtodata, total=total)