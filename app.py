from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "finance_secret_key"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

USERNAME = "admin"
PASSWORD = "1234"


class Customer(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))
    mobile = db.Column(db.String(20))
    address = db.Column(db.String(200))

    loan_amount = db.Column(db.Float)
    interest = db.Column(db.Float)

    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))

    emi = db.Column(db.Float)

    emi_status = db.Column(db.String(20), default="Pending")


@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == USERNAME and password == PASSWORD:

            session["user"] = username
            return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("login"))

    total_customers = Customer.query.count()

    pending_emi = Customer.query.filter_by(emi_status="Pending").count()

    total_loans = db.session.query(db.func.sum(Customer.loan_amount)).scalar() or 0

    return render_template(
        "dashboard.html",
        total_customers=total_customers,
        pending_emi=pending_emi,
        total_loans=total_loans
    )


@app.route("/add_customer", methods=["GET","POST"])
def add_customer():

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        name = request.form["name"]
        mobile = request.form["mobile"]
        address = request.form["address"]

        loan_amount = float(request.form["loan"])
        interest = float(request.form["interest"])

        start_date = request.form["start"]
        end_date = request.form["end"]

        months = 12
        total = loan_amount + (loan_amount * interest / 100)
        emi = total / months

        new_customer = Customer(
            name=name,
            mobile=mobile,
            address=address,
            loan_amount=loan_amount,
            interest=interest,
            start_date=start_date,
            end_date=end_date,
            emi=emi
        )

        db.session.add(new_customer)
        db.session.commit()

        return redirect(url_for("customers"))

    return render_template("add_customer.html")


@app.route("/customers")
def customers():

    if "user" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search")

    if search:
        all_customers = Customer.query.filter(
            (Customer.name.contains(search)) |
            (Customer.mobile.contains(search))
        ).all()
    else:
        all_customers = Customer.query.all()

    return render_template("customers.html", customers=all_customers)


@app.route("/customer/<int:id>")
def customer_profile(id):

    if "user" not in session:
        return redirect(url_for("login"))

    customer = Customer.query.get_or_404(id)

    return render_template(
        "customer_profile.html",
        customer=customer
    )


@app.route("/delete_customer/<int:id>")
def delete_customer(id):

    if "user" not in session:
        return redirect(url_for("login"))

    customer = Customer.query.get(id)

    if customer:
        db.session.delete(customer)
        db.session.commit()

    return redirect(url_for("customers"))


@app.route("/edit_customer/<int:id>", methods=["GET","POST"])
def edit_customer(id):

    if "user" not in session:
        return redirect(url_for("login"))

    customer = Customer.query.get(id)

    if request.method == "POST":

        customer.name = request.form["name"]
        customer.mobile = request.form["mobile"]
        customer.address = request.form["address"]

        db.session.commit()

        return redirect(url_for("customers"))

    return render_template("edit_customer.html", customer=customer)


@app.route("/pay_emi/<int:id>")
def pay_emi(id):

    if "user" not in session:
        return redirect(url_for("login"))

    customer = Customer.query.get(id)

    if customer:
        customer.emi_status = "Paid"
        db.session.commit()

    return redirect(url_for("customers"))


@app.route("/unpay_emi/<int:id>")
def unpay_emi(id):

    if "user" not in session:
        return redirect(url_for("login"))

    customer = Customer.query.get(id)

    if customer:
        customer.emi_status = "Pending"
        db.session.commit()

    return redirect(url_for("customers"))


@app.route("/emi_reminders")
def emi():

    if "user" not in session:
        return redirect(url_for("login"))

    customers = Customer.query.filter_by(emi_status="Pending").all()

    return render_template("emi.html", customers=customers)


@app.route("/logout")
def logout():

    session.pop("user",None)

    return redirect(url_for("login"))


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)