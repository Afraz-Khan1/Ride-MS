from flask import Flask,render_template,request,session,redirect,url_for # i added this if user directly paste link of book_ride etc flask will open it without check if user is logged in so used it in every method
import mysql.connector


app=Flask(__name__) ## instance of flask class. (wsgi connecter of webserver to your app.)
app.secret_key="you_are_allowed"  # Login ensures only authorized users access the app, and combined with sessions, it securely tracks each user without exposing sensitive data.


conn=mysql.connector.connect(  #creating a connection of database and using cursor for querying   
   host="localhost",
   user="root",
   password="",
   database="myride"
)

cursor=conn.cursor()
@app.route("/",methods=["GET","POST"])
def home():
   if request.method=="POST":
      name=request.form["name"]
      email=request.form["email"]
      password=request.form["password"]
      phone=request.form["phone"]
      role=request.form["role"]  

      if role=="rider":
        cursor.execute("SELECT email FROM rider WHERE email=%s" ,(email,))
        Email=cursor.fetchone()
        if Email!=None:
           return render_template("home.html",message="Duplicate Data Detected!, Try Unique Rider Data")
        cursor.execute("INSERT INTO rider (name,email,password,phone)" \
        "values(%s,%s,%s,%s)" ,(name,email,password,phone))
        conn.commit()
      elif role=="driver":
        cursor.execute("SELECT email FROM driver WHERE email=%s" ,(email,))
        Email=cursor.fetchone()
        if Email!=None:
           return render_template("home.html",message="Duplicate Data Detected!, Try Unique Driver Data")
        cursor.execute("INSERT INTO driver (name,email,password,phone)" \
        "values(%s,%s,%s,%s)", (name,email,password,phone))
        conn.commit()
      elif role=="admin":
         cursor.execute("SELECT email FROM admin WHERE email=%s" ,(email,))
         Email=cursor.fetchone()
         if Email!=None:
           return render_template("home.html",message="Duplicate Data Detected!, Try Unique admin Data")
         cursor.execute("INSERT INTO admin (name,email,password,role)" \
         "values(%s,%s,%s,%s)", (name,email,password,role))
         conn.commit()
        

      return render_template('home.html',message="Registration Successful!")
      
   return render_template('home.html') # remember this is the get method here when page or forms open

@app.route("/adminlogin",methods=["GET","POST"])
def admin():
   if request.method=="POST":
      name=request.form["name"]
      email=request.form["email"]
      password=request.form["password"]
      cursor.execute("SELECT admin_id FROM admin where email=%s AND password=%s",(email,password,))
      admin_id=cursor.fetchone()
      if admin_id:
         
         session['admin_id']=admin_id[0]
         return render_template('admindash.html')
      else:
         return render_template('admin.html',message="Sorry, Wrong Credentials!")
         
   return render_template('admin.html',form='adminlogin')

@app.route("/admindash",methods=["GET"])
def admindash():
      return render_template('admindash.html')

@app.route("/userdash",methods=["GET"])
def userdash():
      return render_template('userdash.html')

@app.route("/driverdash",methods=["GET"])
def driverdash():
      return render_template('driverdash.html')



@app.route("/userlogin",methods=["GET","POST"])
def userlogin():
   
   if request.method=="POST":

      email=request.form["email"]
      password=request.form["password"]
      role=request.form["role"]
      session['role']=role  # storing role in session for safer access through out the routes using role=session.get('role'). and possible that user register as rider but login as driver so we must store role in session here in login
      if role=="rider":
        cursor.execute("SELECT * FROM rider WHERE email=%s AND password=%s " ,(email,password,))
        user_rider=cursor.fetchone() #returns the result of query
        
        if user_rider is not None:
          if user_rider[3]=="blocked":
           return render_template('user.html',user_rider=user_rider,message="You Are Blocked By Admin")
          session['rider_id']=user_rider[0]
          rider_id=session.get('rider_id')
          return render_template('userdash.html',user_rider=rider_id)
        else:
          return render_template('user.html',user_rider=user_rider,message="Wrong Credentials!") #wrong info
        
      elif role=="driver":
         cursor.execute("SELECT * FROM driver WHERE email=%s AND password=%s" ,(email,password))
         user_driver=cursor.fetchone() #returns the result of query

         if user_driver is not None:
          if user_driver[6]=="blocked":
           return render_template('user.html',user_rider=user_driver,message="You Are Blocked By Admin")
          session['driver_id']=user_driver[0]
          driver_id=session.get('driver_id')
          return render_template('driverdash.html',user_driver=driver_id)
         else:
          return render_template('user.html',user_rider=None,message="Wrong Credentials!") #wrong info

   return render_template('user.html',user_rider=None,form="login")

@app.route("/rider-bookrides",methods=["GET","POST"])
def bookrides():

   if not session.get('rider_id'):
    return redirect("/userlogin")
   
   if request.method=="POST":
      
      pickup=request.form["pickupaddress"] # gulshan karachi
      drop=request.form["dropaddress"]
      parts1=pickup.split() # ['gulshan','karachi']
      parts2=drop.split()

      if len(parts1)!=2 or len(parts2)!=2:
        return render_template('userdash.html',message="Locations Should Be Filled In Correct Format!")

      vehicle=request.form["vehicle"]
      distance=request.form['distance']
      rider_id=session.get('rider_id') # retriving rider_id from session.
      fare=request.form['fare'] # form input is always string you can convert to int if you want for conditions
      if fare=='0':
         return render_template('userdash.html',message="Fare Can't Be zero")
      driver=None
      cursor.execute("SELECT driver_id FROM driver WHERE status='ok' limit 1") #cursor.execute() only runs the query.It does NOT return the result.
      driver=cursor.fetchone() #fetchone() gets the row returned by the query.
      if driver!=None:
        cursor.execute("SELECT vehicle_type FROM vehical WHERE driver_id=%s ",(driver[0],))
        vehi=cursor.fetchone()
      else:
         return render_template('userdash.html',message="Sorry, No drivers available right now!")
      
      if vehi[0]!=vehicle:
         return render_template('userdash.html',message="No Driver Available Of Your Vehicle Type")

      
      driver_id=driver[0] # here i didn't used session driver_id as here only that id need whos status is available
      cursor.execute("INSERT INTO ride (rider_id,driver_id,vehicle_type,pickup_location,drop_location,fare)" \
      "values(%s,%s,%s,%s,%s,%s)", (rider_id,driver_id,vehicle,pickup,drop,fare))
      conn.commit()
      # so lastrowid is a property only used after insert to get latest insert item no need for select
      ride_id=cursor.lastrowid #last inserted ride_id retrive . fetchone() can give old ride_id not latest

      #inserting in payments without fare. so that if users clicks on payment he can see ride_id which is not paid.
      cursor.execute("INSERT INTO payment (ride_id) values(%s)",(ride_id,))
      conn.commit()
      # before inserting into route we have to insert in location 1 id for start loc 1 id for end loc.
      cursor.execute("INSERT INTO location (address,city) values(%s,%s)",(parts1[0],parts1[1])) #pickup
      conn.commit()
      pick_loc=cursor.lastrowid #pick id from location
      cursor.execute("INSERT INTO location (address,city) values(%s,%s)",(parts2[0],parts2[1])) #drop
      conn.commit()
      drop_loc=cursor.lastrowid #drop id from location
      cursor.execute("INSERT INTO route (ride_id,start_location,end_location,distance)" \
      "values(%s,%s,%s,%s)",(ride_id,pick_loc,drop_loc,distance))
      conn.commit()

      return render_template("userdash.html",message="Congratulations! Ride Booked")
      
         
   return render_template('user-rider.html',form='bookride',user_rider=session.get('rider_id'))


@app.route("/rider-viewrides")
def viewrides():

   if not session.get('rider_id'): # logged in check for user
    return redirect("/userlogin")
   
   cursor.execute("SELECT * FROM ride WHERE rider_id=%s",(session.get('rider_id'),)) 
   rides=cursor.fetchall()
   if rides: # i didn't write rides!=None cuz fetchall return [] when no rides.
      return render_template('user-rider.html',form='viewrides',rides=rides,message=None)
   else:
      return render_template('userdash.html',message="Sorry no rides available right now!")
   

@app.route("/rider-payment",methods=["GET","POST"])
def riderpay():
   
   if not session.get('rider_id'):
    return redirect("/userlogin")

   cursor.execute( # so we added left join because if no rides booked yet still user click pay than it would open the error message 
   "SELECT r.ride_id, r.fare, p.payment_status \
   FROM ride r " \
   "LEFT JOIN payment p " \
   "ON r.ride_id=p.ride_id \
   WHERE r.rider_id=%s AND p.payment_status='pending'",
   (session.get('rider_id'),)
   )
   ride_ids=cursor.fetchall()
   if not ride_ids: # as fetchall never return None but an empty list[] so we have to write not but we can't write !=None
      return render_template('userdash.html',message="No Pending Payments left!")
   
   if request.method=="POST":
     ride_id=request.form["rideid"]
     fare=int(request.form["fare"]) # any thing from form is in string we should convert integer values from string to int
     cursor.execute("SELECT fare FROM ride WHERE ride_id=%s",(ride_id,))
     fare_check=cursor.fetchone() #fare_check is tuple we should compare fare_check[0]
     if fare_check is None or fare_check[0]!=fare:
        return render_template('userdash.html',message="Please Enter Required Amount Payable!")
     cursor.execute("UPDATE ride SET fare=%s WHERE ride_id=%s",(fare,ride_id,))
     conn.commit()
     cursor.execute("UPDATE payment SET payment_status='paid',amount=%s where ride_id=%s",(fare,ride_id))
     conn.commit()
     
     return render_template('userdash.html',user_rider=session.get('rider_id'),message="Payment Successfull!")
     
   return render_template('user-rider.html',form='payment',ride_ids=ride_ids) # we wrote here user-rider for get method 
   
      

@app.route("/rider-feedback",methods=["GET","POST"])
def riderfeedback():

   if not session.get('rider_id'):
    return redirect("/userlogin")

   rider_id=session.get('rider_id')
   cursor.execute("SELECT ride_id FROM ride WHERE rider_id=%s",(rider_id,))
   ride_ids=cursor.fetchall()
   if not ride_ids:
       return render_template('userdash.html',message="Sorry, There Are No Completed Rides!")

   cursor.execute("SELECT ride_id FROM ride WHERE rider_id=%s and fare IS NOT NULL",(rider_id,))
   ride_ids_with_done_payment=cursor.fetchall()
   if not ride_ids_with_done_payment:
       return render_template('userdash.html',message="You Have Completed Rides That Are Not Paid Yet!")

   

   if request.method=="POST":

      rideid=request.form["rideid"]
      cursor.execute("SELECT feedback_id FROM feedback WHERE ride_id=%s AND rider_id=%s",(rider_id,rideid,))
      feedback_check=cursor.fetchone()
      if feedback_check:
        return render_template('userdash.html',message="Feedback already recorded!")
      rating=request.form["rating"]
      comment=request.form["feedback"]
      cursor.execute("INSERT INTO feedback (ride_id,rider_id,ratings,comments)" \
      "values(%s,%s,%s,%s)",(rideid,rider_id,rating,comment))
      conn.commit()
      return render_template('userdash.html',message="Thankyou for your feedback!")
   
   return render_template('user-rider.html',form='feedback',ride_ids=ride_ids_with_done_payment)


@app.route("/driver-license",methods=["GET","POST"])
def driverlicence():

   if not session.get('driver_id'):
    return redirect("/userlogin")
   driver_id=session.get('driver_id')

   cursor.execute("SELECT license_number FROM driver where driver_id=%s",(driver_id,))
   license_check=cursor.fetchone()
   if license_check[0] and license_check:
      return render_template('driverdash.html',message="Sorry, Your Licence Is Already Registered!")


   if request.method=="POST":
     
     license=request.form['license']
     cursor.execute("SELECT driver_id FROM driver WHERE license_number = %s", (license,))
     duplicate_lic_check = cursor.fetchall()
     if duplicate_lic_check:
        return render_template('driverdash.html',message="License Duplicate Detected!")
        
     status=request.form['status']
     cursor.execute("UPDATE driver SET license_number=%s , status=%s WHERE driver_id=%s",(license,status,session.get('driver_id')))
     conn.commit()
     return render_template('driverdash.html',message="Congratulations!, licence registered")
   
   return render_template('user-driver.html',form='license')


@app.route("/driver-avail",methods=["GET","POST"])
def driveravail():

   if not session.get('driver_id'):
    return redirect("/userlogin")
   
   cursor.execute("SELECT schedule_id FROM schedule WHERE driver_id=%s",(session.get('driver_id'),))
   schedule_check=cursor.fetchone()
   if schedule_check!=None:
      return render_template('driverdash.html',message="Your Availability Is Already Set!")

   
   if request.method=="POST":
     driver_id=session.get('driver_id')
     ontime=request.form['ontime']
     offtime=request.form['offtime']
     vehicletype=request.form['vehicletype']
     # first inserting into vehicle vehicle type
     cursor.execute("INSERT INTO vehical (driver_id,vehicle_type)" \
     "values(%s,%s)",(driver_id,vehicletype))
     conn.commit()
     # second inserting relevent data into schedule
     cursor.execute("INSERT INTO schedule (driver_id,available_from,available_to) "
     "values(%s,%s,%s)",(driver_id,ontime,offtime))
     conn.commit()
     return render_template('driverdash.html',message="Your Availability And Rates Are Now Set!")
   
   return render_template('user-driver.html',form='setavail')


@app.route("/driver-checkpay")
def drivercheckpay():

   if not session.get('driver_id'):
    return redirect("/userlogin")

   cursor.execute("SELECT * FROM payment")
   pay=cursor.fetchall()
   if pay:
      return render_template('user-driver.html',form='payreceived',payments=pay)
   else:
      return render_template('driverdash.html',message="Sorry, No payments yet!")
   

@app.route("/driver-checkfeed")
def drivercheckfeed():

   if not session.get('driver_id'):
    return redirect("/userlogin")

   cursor.execute("SELECT * FROM feedback")
   feed=cursor.fetchall()
   if feed:
      return render_template('user-driver.html',form='checkfeed',feeds=feed)
   else:
      return render_template('driverdash.html',message="Sorry, Complete Rides First")

@app.route("/userrole",methods=["GET","POST"])
def role():
   if request.method=="POST":
      role=request.form["role"]
      return redirect(url_for('userstatus',role=role)) # this role is send to userstatus by admin. cuz on get we should have any role to show ids of in userstatus by admin.instead of doing 
   # that using javascript
   
   return render_template('admincontrols.html',form='userrole')

@app.route("/user_status_byadmin",methods=["GET","POST"])
def userstatus():
   
   if not session.get('admin_id'):
      return redirect("/adminlogin") 
   
   user = (request.args.get('role') or request.form.get('role') or '').strip().lower()
   
   riderid_check=[]
   driverid_check=[]
   if user=="rider":
     cursor.execute("SELECT rider_id FROM rider") # we kept these both outside cuz on get rideid_check was getting none
     riderid_check=cursor.fetchall()
     if not riderid_check:
         return render_template('admindash.html',message="Sorry No Riders Yet!")
     
   elif user=="driver":
      cursor.execute("SELECT driver_id FROM driver")
      driverid_check=cursor.fetchall()
      if not driverid_check:
         return render_template('admindash.html',message="Sorry No Drivers Yet!")

   if request.method=="POST":
      newstatus=request.form["newstatus"]
      
      if user=="rider":
         
         rider_id=request.form["userid"]
         cursor.execute("UPDATE rider SET status=%s where rider_id=%s",(newstatus,rider_id))
         conn.commit()
         return render_template('admindash.html',message="User Status Changed By Admin!")
         
      elif user=="driver":
          
         driver_id=request.form["userid"]
         cursor.execute("UPDATE driver SET status=%s where driver_id=%s",(newstatus,driver_id))
         conn.commit()
         return render_template('admindash.html',message="User Status Changed By Admin!")
         
   return render_template('admincontrols.html',form='userstatus',rider_ids=riderid_check,driver_ids=driverid_check,role=user)


@app.route("/cancel_ride_byadmin",methods=["GET","POST"])
def cancelride():

   if not session.get('admin_id'):
      return redirect("/adminlogin") 
   
   cursor.execute(
    "SELECT r.ride_id FROM ride r "
    "INNER JOIN payment p "
    "ON r.ride_id = p.ride_id "
    "WHERE p.payment_status = 'unpaid'"
)
   rideid_check=cursor.fetchall()
   if not rideid_check:
      return render_template("admindash.html",message="Sorry, No Rides Yet!")

   if request.method=="POST":
      
      rideid=request.form["rideid"]
      cursor.execute("UPDATE ride SET fare=%s WHERE ride_id=%s",("NULL",rideid,))
      conn.commit()
      cursor.execute("UPDATE payment SET payment_status=%s where ride_id=%s",("cancelled",rideid,))
      conn.commit()
      return render_template("admindash.html",message="Ride Cancelled By Admin!")
      
   return render_template('admincontrols.html',form='cancelride',ride_ids=rideid_check)


@app.route("/delete_feedback_byadmin",methods=["GET","POST"])
def deletefeed():
   if not session.get('admin_id'):
      return redirect("/adminlogin")

   
   cursor.execute("SELECT feedback_id FROM feedback")
   feed_ids=cursor.fetchall()
   if not feed_ids:
      return render_template('admindash.html',message="No Feedbacks Yet!")
   
   if request.method=="POST":

      feed_id=request.form["feedback_id"]
      cursor.execute("DELETE FROM feedback where feedback_id=%s",(feed_id,))
      conn.commit()
      return render_template("admindash.html",message="Feedback Deleted Successfully!")
         
   return render_template('admincontrols.html',form='userfeed',feed_ids=feed_ids)


@app.route("/viewrides_byadmin")
def rideview():
   if not session.get('admin_id'):
      return redirect("/adminlogin") 
   
   cursor.execute("SELECT * FROM ride") 
   rides=cursor.fetchall()
   if rides: # i didn't write rides!=None cuz fetchall return [] when no rides.
      return render_template('admincontrols.html',form='viewrides',rides=rides)
   else:
      return render_template('admindash.html',message="Sorry No Rides To Show")
   


@app.route("/viewpayments_byadmin")
def payview():
   if not session.get('admin_id'):
      return redirect("/adminlogin") 
   
   cursor.execute("SELECT * FROM payment")
   pay=cursor.fetchall()
   if pay:
      return render_template('admincontrols.html',form='viewpay',payments=pay)
   else:
      return render_template('admindash.html',message="Sorry, No payments yet!")


@app.route("/viewfeedback_byadmin")
def feedview():
   if not session.get('admin_id'):
      return redirect("/adminlogin") 
   
   cursor.execute("SELECT * FROM feedback")
   feed=cursor.fetchall()
   if feed:
      return render_template('admincontrols.html',form='checkfeed',feeds=feed)
   else:
      return render_template('admindash.html',message="Sorry, No feedbacks yet")
         




if __name__=="__main__":  ## initial condition of any app to work.
   app.run(debug=True) ## let the developer to not run the server again and again to see changes just reload.