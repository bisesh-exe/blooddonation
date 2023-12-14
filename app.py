from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime
import sqlite3 as sql
import os

# Create Database if it doesn't exist
if not os.path.isfile('database.db'):
    conn = sql.connect('database.db')
    conn.execute('CREATE TABLE IF NOT EXISTS Donors (Name TEXT NOT NULL, Amount INTEGER NOT NULL, Email TEXT NOT NULL, [timestamp] TIMESTAMP)')
    conn.execute('CREATE TABLE IF NOT EXISTS Users (Name TEXT NOT NULL, Email TEXT NOT NULL, Password TEXT NOT NULL, Contact INTEGER NOT NULL, isAdmin BOOLEAN DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS PendingDonationRequests (AdTitle TEXT, AdDescription TEXT, ContactInfo TEXT, DonationAmount INTEGER)')
    
    try:
        # Insert Admin user with isAdmin set to True
        conn.execute("INSERT INTO Users (Name, Email, Password, Contact, isAdmin) VALUES (?, ?, ?, ?, ?)",
                     ('Admin', 'admin@admin.com', 'admin', '1234567890', 1))
        conn.commit()
        print("Admin user created successfully.")
        
        # Create DonationRequests table
        conn.execute('CREATE TABLE IF NOT EXISTS DonationRequests (AdTitle TEXT, AdDescription TEXT, ContactInfo TEXT, DonationAmount INTEGER)')
        conn.commit()
        print("DonationRequests table created successfully.")
        
        # Create PendingDonationRequests table
        conn.execute('CREATE TABLE IF NOT EXISTS PendingDonationRequests (AdTitle TEXT, AdDescription TEXT, ContactInfo TEXT, DonationAmount INTEGER)')
        conn.commit()
        print("PendingDonationRequests table created successfully.")
        
        # Insert dummy data into PendingDonationRequests table
        conn.execute("INSERT INTO PendingDonationRequests (AdTitle, AdDescription, ContactInfo, DonationAmount) VALUES (?, ?, ?, ?)",
                     ('Request 1', 'Description 1', 'Contact Info 1', 100))
        conn.execute("INSERT INTO PendingDonationRequests (AdTitle, AdDescription, ContactInfo, DonationAmount) VALUES (?, ?, ?, ?)",
                     ('Request 2', 'Description 2', 'Contact Info 2', 200))
        conn.commit()
        print("Dummy data inserted into PendingDonationRequests table.")

    except Exception as e:
        print("Error creating tables:", e)
        conn.rollback()

    conn.close()


app = Flask(__name__, static_url_path='/assets', static_folder='assets', template_folder='./')

app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = "your_secret_key_here"  

@app.route('/')
def root():
   session['logged_out']= 1
   return render_template('index.html')

@app.route('/index.html')
def index():
   return render_template('index.html')

@app.route('/header_page.html')
def header_page():
   return render_template('header_page.html')

@app.route('/menu-bar-charity.html')
def menu_bar_charity():
   return render_template('menu-bar-charity.html')

@app.route('/footer.html')
def footer():
   return render_template('footer.html')

@app.route('/sidebar.html')
def sidebar():
   return render_template('sidebar.html')   

@app.route('/contact.html')
def contact():
   return render_template('contact.html')

@app.route('/our-causes.html')
def our_causes():
   return render_template('our-causes.html')

@app.route('/about-us.html')
def about_us():
   return render_template('about-us.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    nm = request.form['nm']
    contact = request.form['contact']
    email = request.form['email']
    password = request.form['password']
         
    with sql.connect("database.db") as con:
      cur = con.cursor()
      #check if User already present
      cur.execute("SELECT Email FROM Users WHERE Email=(?)",[(email)])
      data = cur.fetchall()
      if len(data)>0:
        print('User already exists')
        user_exists=1
      else:
        print("User not found, register new user")
        user_exists=0
        cur.execute("INSERT INTO Users (Name,Email,Password,Contact) VALUES (?,?,?,?)",(nm,email,password,contact) )
        
  return render_template('login.html',user_exists=user_exists, invalid = None, logged_out=None)

@app.route('/login.html', methods=['GET', 'POST'])
def login():
    invalid = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with sql.connect("database.db") as con:
            cur = con.cursor()
            # Validate user credentials from the database
            cur.execute("SELECT Email FROM Users WHERE Email=(?) AND Password=(?)", [(email), (password)])
            data = cur.fetchall()
            if len(data) > 0:
                print('Login Success')
                # Fetch name of user
                cur.execute("SELECT Name FROM Users WHERE Email=(?) AND Password=(?)", [(email), (password)])
                nm = cur.fetchall()
                nm = nm[0][0]
                # Store User details in Session and log in user
                session['nm'] = nm
                session['email'] = email
                session['logged_out'] = None

                # Check if the user is an admin and set session variables accordingly
                if email == 'admin@admin.com':  # Change this condition based on admin identification
                    session['isAdmin'] = 1  # Assuming the user is an admin
                    print("User identified as admin")
                else:
                    session['isAdmin'] = 0  # User is not an admin

                # Print the session variables for debugging
                print("isAdmin:", session.get('isAdmin'))
                print("Email:", session.get('email'))
                return redirect(url_for('donate'))
            else:
                print("Invalid Login")
                invalid = 1
    return render_template('login.html', user_exists=None, invalid=invalid, logged_out=None)

@app.route('/logout')
def logout():
  session.clear()
  session['logged_out']=1
  print('Session Cleared and Logged Out')
  return render_template('index.html')  

@app.route('/donate')
def donate():
   # If Logged Out, Redirect to Log In page
   if session['logged_out']:
    return render_template('login.html',logged_out=1,user_exists=None, invalid = None)
   nm = session['nm']
   email = session['email']
   return render_template('donate.html',nm=nm,email=email)         

#insert values into table
@app.route('/donation',methods = ['POST', 'GET'])
def donation():
   # If Logged Out, Redirect to Log In page
   if session['logged_out']:
    return render_template('login.html',logged_out=1,user_exists=None, invalid = None)
   if request.method == 'POST':
         nm = session['nm']
         email = session['email']
         amt = request.form['amt']
         today = datetime.now()
         today = today.strftime("%d-%m-%Y"+","+"%H:%M")
         
         with sql.connect("database.db") as con:
            cur = con.cursor()
            #check if already donated. If already donated, add donation. Else create new donation
            cur.execute("SELECT Email FROM Donors WHERE Email=(?)",[(email)])
            data = cur.fetchall()
            if len(data)>0:
              cur.execute("UPDATE Donors SET Amount=Amount+(?) WHERE Email=(?)",[(amt),(email)])
            else:
              cur.execute("INSERT INTO Donors (Name,Amount,Email,timestamp) VALUES (?,?,?,?)",(nm,amt,email,today) )                
            con.commit()
            
            # Greeting
            msg = "Thank You for Donating"
            for row in cur.execute("SELECT Amount FROM Donors WHERE Email=(?)",[(email)]):
                Amount=row
         return render_template("greeting.html",msg = msg,nm=nm,Amount=Amount,today=today, email=email)
         con.close()

#Display List of Donations
@app.route('/list1')
def list1():
   # If Logged Out, Redirect to Log In page
   if session['logged_out']:
    return render_template('login.html',logged_out=1,user_exists=None, invalid = None)
   con = sql.connect("database.db")
   con.row_factory = sql.Row
   
   cur = con.cursor()
   cur.execute("SELECT * FROM Donors")
   
   rows = cur.fetchall();
   return render_template("list1.html",rows = rows)

#Donation request form
@app.route('/submit_donation_request', methods=['POST'])
def submit_donation_request():
    if request.method == 'POST':
        ad_title = request.form['ad_title']
        ad_description = request.form['ad_description']
        contact_info = request.form['contact_info']
        donation_amount = request.form['donation_amount']
        # Add the data to your database (similar to the 'donation' route)
        # Assuming the donation requests are stored in a table named 'DonationRequests'
        with sql.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO DonationRequests (AdTitle, AdDescription, ContactInfo, DonationAmount) VALUES (?,?,?,?)",
                        (ad_title, ad_description, contact_info, donation_amount))
            con.commit()
        return redirect(url_for('confirmation_page'))
    return "Bad request"

#Display Profile
@app.route('/profile')
def profile():
   # If Logged Out, Redirect to Log In page
   if session['logged_out']:
    return render_template('login.html',logged_out=1,user_exists=None, invalid = None)
   nm = session['nm']
   email = session['email']
   with sql.connect("database.db") as con:
    cur = con.cursor()
    # Fetch details of user
    cur.execute("SELECT Contact FROM Users WHERE Email=(?)",[(email)])
    contact = cur.fetchall()
    contact=contact[0][0]

    cur.execute("SELECT Password FROM Users WHERE Email=(?)",[(email)])
    password = cur.fetchall()
    password=password[0][0]
   return render_template("profile.html",nm=nm,email=email,contact=contact,password=password)

@app.route('/create_donation_request', methods=['GET', 'POST'])
def create_donation_request():
    if 'email' not in session or session['logged_out']:
        # If the user is not logged in, redirect to the login page
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            ad_title = request.form.get('ad_title')
            ad_description = request.form.get('ad_description')
            contact_info = request.form.get('contact_info')
            donation_amount = request.form.get('donation_amount')

            with sql.connect("database.db") as con:
                cur = con.cursor()
                cur.execute("INSERT INTO DonationRequests (AdTitle, AdDescription, ContactInfo, DonationAmount) VALUES (?,?,?,?)",
                            (ad_title, ad_description, contact_info, donation_amount))
                con.commit()

            # Redirect to the 'donation' route upon successful submission
            return redirect(url_for('donation'))

        except sql.Error as e:
            # Log the exception for debugging
            print("SQL error occurred in create_donation_request:", e)
            # Return an error page or a message to indicate the failure
            return "SQL error occurred while processing the request"

        except Exception as ex:
            # Log other exceptions for debugging
            print("Error occurred in create_donation_request:", ex)
            # Return an error page or a message to indicate the failure
            return "Error occurred while processing the request"

    # For GET requests or when the form is not submitted
    return render_template('donation_request_form.html')

@app.route('/confirmation_page')
def confirmation_page():
    # Logic for the confirmation page
    return render_template('donation_request_confirmation.html')

@app.route('/donation_appel_request', methods=['POST'])
def donation_appel_request():
    if request.method == 'POST':
        # Extract form data
        ad_title = request.form.get('ad_title')
        ad_description = request.form.get('ad_description')
        contact_info = request.form.get('contact_info')
        donation_amount = request.form.get('donation_amount')

        # Save the donation request to the database (pending admin approval)
        # Here, you would insert the request into a table named 'PendingDonationRequests'
        # indicating that it is pending approval
        # Replace the following with your database insertion logic

        # Assuming your table structure for pending requests is PendingDonationRequests
        # Insert the donation request into the PendingDonationRequests table
        with sql.connect("database.db") as con:
            try:
                cur = con.cursor()
                cur.execute("""
                    INSERT INTO PendingDonationRequests (AdTitle, AdDescription, ContactInfo, DonationAmount)
                    VALUES (?, ?, ?, ?)
                """, (ad_title, ad_description, contact_info, donation_amount))
                con.commit()
                return render_template('donation_request_confirmation.html')
            except sql.Error as e:
                con.rollback()  # Rollback the changes if an error occurs
                print("SQL error occurred:", e)
                return "Error occurred while saving data to the database"
            except Exception as ex:
                print("Error occurred:", ex)
                return "Error occurred while processing the request"

@app.route('/donation_appeal_requests')
def donation_appeal_requests():
    try:
        with sql.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM PendingDonationRequests")
            donation_requests = cur.fetchall()
        return render_template('donation_appeal_requests_admin.html', donation_requests=donation_requests)
    except sql.Error as e:
        print("SQL error occurred:", e)
        # Handle the error gracefully or log the error message
        return "Error occurred while fetching data from the database"
    except Exception as ex:
        print("Error occurred:", ex)
        # Handle the exception or log the error message
        return "Error occurred while processing the request"
    
if __name__ == '__main__':
   app.secret_key = ".."
   app.run(debug=True)