#Python libraries used
from flask import Flask, request, render_template, redirect, url_for, flash, Response
import pyodbc
import os
from datetime import datetime
from dotenv import load_dotenv

# Set the required variables and file imports
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(12).hex()

not_skip_id_table = {"ADMIN", "HOST", "PARTICIPANT", "BUDGET_SHEET"}
double_id_table = {"BUDGET_SHEET"}
admin_table_access = {"Host Management": ["HOST", "REQUESTS"], 
                      "Org Management": ["ORGANIZATION", "REQUESTS"], 
                      "Item Management": ["ITEM", "REQUESTS"], 
                      "Venue Management": ["VENUE", "REQUESTS"], 
                      "Ticket Management": ["TICKETS", "REQUESTS"]}

def skip_id_check(table_name):
    if table_name in not_skip_id_table:
        return False
    return True

def double_id_check(table_name):
    if table_name in double_id_table:
        return True
    return False

db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")

connection = pyodbc.connect(
       'DRIVER={ODBC Driver 18 for SQL Server}' + 
       ';SERVER=' + 'localhost,1433' + ';UID=' + db_username + 
       ';PWD=' + db_password +
       ';database=project' + ';TrustServerCertificate=yes')

user_id = None
is_valid = None
user_fullname = None
admin_resp = None
org_id = None
user_type_flag = [0, 0, 0]

#Index/Landing page
@app.route('/')
def landing():
    return render_template('login.html')

#Login routing page
@app.route('/login_route', methods=['POST', 'GET'])
def login():
    global user_id, is_valid, user_fullname, user_type_flag
    try:
        if request.method == 'GET':
            print(user_id, user_fullname, user_type_flag)
            if user_id == None:
                flash('You have been logged out due to inactivity. Login again to continue.')
                return redirect(url_for('landing'))
            return render_template('index.html', user_id = user_id, user_fullname = user_fullname, user_type_flag = user_type_flag)
        elif request.method == 'POST':
            # Get email and password from the form
            email_username = str(request.form.get('email_username')).strip()
            password = str(request.form.get('password')).strip()

            # Initialize output parameters
            cursor = connection.cursor()

            # Call the stored procedure
            result = cursor.execute(
                """
                DECLARE @IsValid BIT,
                        @UserID INT,
                        @FirstName VARCHAR(50),
                        @LastName VARCHAR(50),
                        @UserType VARCHAR(3);
                EXEC validateUserCredentials 
                    @Email = ?, 
                    @Password = ?, 
                    @IsValid = @IsValid OUTPUT, 
                    @UserID = @UserID OUTPUT,
                    @FirstName = @FirstName OUTPUT,
                    @LastName = @LastName OUTPUT,
                    @UserType = @UserType OUTPUT;
                SELECT @IsValid AS IsValid, @UserID AS UserID, 
                    @FirstName AS FirstName, @LastName AS LastName, 
                    @UserType AS UserType;
                """,
                (email_username, password)
            )

            # Fetch the output parameters
            result = cursor.fetchone()
            is_valid = result[0]

            cursor.close()

            if not is_valid:
                # Flash an error message for invalid credentials
                flash('Invalid username or password.')
                return redirect(url_for('landing'))
            
            user_id = result[1]
            user_fullname = f"{result[2]} {result[3]}"
            user_type = result[4]
            print(user_id, user_fullname, user_type_flag)

            if "H" in user_type:
                user_type_flag[0] = 1
            
            if "P" in user_type:
                user_type_flag[1] = 1
            
            if "A" in user_type:
                user_type_flag[2] = 1
    except Exception as e:
        print(e)
        flash('An error occurred during login.')
        return redirect(url_for('landing'))
    return render_template('index.html', user_id = user_id, user_fullname = user_fullname, user_type_flag = user_type_flag)

@app.route('/logout')
def logout():
    global user_id, is_valid, user_fullname, user_type_flag, admin_resp, org_id
    user_id = None
    admin_resp = None
    is_valid = None
    user_fullname = None
    org_id = None
    user_type_flag[0] = 0
    user_type_flag[1] = 0
    user_type_flag[2] = 0
    # print(user_type_flag)
    return redirect(url_for('landing'))

## Host Routes
@app.route('/host_get_org')
def host_check():
    global user_id, org_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    try:
        cursor = connection.cursor()

        table_query = f'SELECT [OrgID] FROM [HOST] WHERE [HUserID]={user_id}'

        cursor.execute(table_query)

        result = cursor.fetchall()

        org_id = result[0][0]

        print("org_id:", org_id)

        return redirect(url_for('host'))
    except Exception as e:
        print(e)
        flash('There was an error in showing host dashboard.')
        # flash(e)
    finally:
        cursor.close()

@app.route('/host_dashboard')
def host():
    global user_id, org_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    
    try:
        if org_id == None:
            # print("A")
            # print(org_id)
            flash('There was an issue in getting the host organization.')
            return redirect(url_for('host_check'))
        cursor = connection.cursor()

        host_events_query = f'SELECT * FROM [EVENT] WHERE [OrgID]={org_id}'

        cursor.execute(host_events_query)

        columns = cursor.description

        cols_list = []

        for i in range(len(columns)):
            cols_list.append(columns[i][0])

        data = cursor.fetchall()
        # print(data)
        cursor.close()
        return render_template('hevents.html', table = data, columns=cols_list, table_name="EVENT")
    except Exception as e:
        print(e)
        flash('There was an error in showing host events dashboard.')
        # flash(e)

@app.route('/org_req')
def org_req():
    global user_id, org_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    
    try:
        if org_id == None:
            # print("B")
            flash('There was an issue in getting the host organization.')
            return redirect(url_for('host_check'))
        cursor = connection.cursor()

        host_req_query = f'SELECT * FROM [REQUESTS] WHERE [HostID]={user_id}'

        cursor.execute(host_req_query)

        columns = cursor.description

        cols_list = []

        for i in range(len(columns)):
            cols_list.append(columns[i][0])

        data = cursor.fetchall()
        print(data)
        cursor.close()
        return render_template('hevents.html', table = data, columns=cols_list, table_name="REQUESTS")
    except Exception as e:
        print(e)
        flash('There was an error in showing host requests dashboard.')

@app.route('/org_budget_sheets')
def org_budget_sheets():
    global user_id, org_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    print("org_id:", org_id)
    try:
        if org_id == None:
            # print("C")
            flash('There was an issue in getting the host organization.')
            return redirect(url_for('host_check'))
        cursor = connection.cursor()
        
        host_budget_sheets_query = "EXEC getOrganizationBudgetSheets @OrgID = ?"
        cursor.execute(host_budget_sheets_query, org_id)

        columns = cursor.description

        cols_list = []

        for i in range(len(columns)):
            cols_list.append(columns[i][0])

        data = cursor.fetchall()
        print(data)
        cursor.close()
        return render_template('hevents.html', table = data, columns=cols_list, table_name="BUDGET_SHEET")
    except Exception as e:
        print(e)
        flash('There was an error in showing host budget sheets dashboard.')
        # flash(e)

@app.route('/show_reg/<eid>')
def show_reg(eid):
    global user_id, org_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    print("org_id:", org_id)
    try:
        if org_id == None:
            # print("C")
            flash('There was an issue in getting the host organization.')
            return redirect(url_for('host_check'))
        cursor = connection.cursor()
        
        host_event_reg_query = f'SELECT RegistrationID, S.Description, R.EventID, S.MaxQuantity, TicketQuantity, TransactionTime, RegistrationCheckinTime AS CheckIn, Remarks FROM REGISTRATION R INNER JOIN SEATS S ON R.SeatID=S.SeatID WHERE R.EventID={eid}'
        print(host_event_reg_query)

        cursor.execute(host_event_reg_query)

        columns = cursor.description

        cols_list = []

        for i in range(len(columns)):
            cols_list.append(columns[i][0])

        data = cursor.fetchall()
        print(data)
        cursor.close()
        return render_template('hregistrations.html', table = data, columns=cols_list)
    except Exception as e:
        print(e)
        flash('There was an error in showing event registrations dashboard.')
        # flash(e)

@app.route('/show_feedback/<eid>')
def show_feedback(eid):
    global user_id, org_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    print("org_id:", org_id)
    try:
        if org_id == None:
            # print("C")
            flash('There was an issue in getting the host organization.')
            return redirect(url_for('host_check'))
        cursor = connection.cursor()
        
        host_event_feedback_query = f'SELECT Message, Rating FROM [FEEDBACK] WHERE [EventID]={eid}'
        cursor.execute(host_event_feedback_query)

        print(host_event_feedback_query)

        columns = cursor.description

        cols_list = []

        for i in range(len(columns)):
            cols_list.append(columns[i][0])

        data = cursor.fetchall()
        print(data)
        cursor.close()
        return render_template('hfeedback.html', table = data, columns=cols_list)
    except Exception as e:
        print(e)
        flash('There was an error in showing event feedback dashboard.')
        # flash(e)

@app.route('/org')
def org_details():
    global user_id, org_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    print("org_id:", org_id)
    try:
        if org_id == None:
            # print("C")
            flash('There was an issue in getting the host organization.')
            return redirect(url_for('host_check'))
        cursor = connection.cursor()
        
        org_query = f'SELECT * FROM [ORGANIZATION] WHERE [OrgID]={org_id}'
        cursor.execute(org_query)

        print(org_query)

        columns = cursor.description

        cols_list = []

        for i in range(len(columns)):
            cols_list.append(columns[i][0])

        org_data = cursor.fetchall()
        print(org_data)
        cursor.close()
        return render_template('horg.html', org = org_data[0])
    except Exception as e:
        print(e)
        flash('There was an error in showing event feedback dashboard.')

@app.route('/insert_host/<table_name>', methods = ['POST', 'GET'])
def insert_host(table_name):
    global user_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    try:
        if org_id == None:
            # print("D")
            flash('There was an issue in getting the host organization.')
            return redirect(url_for('host_check'))
        
        cursor = connection.cursor()

        cols_query = f'SELECT TOP 0 * FROM [{table_name}]'

        cursor.execute(cols_query)

        columns = cursor.description
        cursor.close()

        cols_list = []

        for i in range(len(columns)):
            cols_list.append(columns[i][0])
        
        return render_template('create_host.html', columns = cols_list, org_id=org_id, table_name=table_name, user_id=user_id)
    except Exception as e:
        print(e)
        flash('There was an error in inserting the row. Please check the values carefully.')
        # flash(e)

@app.route('/create_host/<table_name>', methods = ['POST'])
def create_host(table_name):
    global user_id, org_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))

    try:
        if request.method == 'POST':
            if org_id == None:
                # print("E")
                flash('There was an issue in getting the host organization.')
                return redirect(url_for('host_check'))
               
            cursor = connection.cursor()
            form_elements = request.form.to_dict()

            cols_list = []
            vals_list = []
            for i in form_elements:
                cols_list.append(f'[{i}]')
                vals_list.append(f"'{form_elements[i]}'")
            
            sep = ", "
            
            create_query = f"INSERT INTO [{table_name}] ({sep.join(cols_list)}) VALUES ({sep.join(vals_list)});"
            print(create_query)

            cursor.execute(create_query)
            connection.commit()

            cursor.close()

            flash('Row inserted successfully.')
            return redirect(url_for('host'))
    except Exception as e:
        print(e)
        flash('There was an error in creating the row. Please check the values carefully.')

@app.route('/edit_host/<table_name>/<column_name>/<uid>', methods = ['GET'])
def edit_host(table_name, column_name, uid):
    global user_id, org_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))

    try:
        if org_id == None:
            # print("F")
            flash('There was an issue in getting the host organization.')
            return redirect(url_for('host_check'))
        
        cursor = connection.cursor()

        cols_query = f'SELECT TOP 0 * FROM [{table_name}]'

        cursor.execute(cols_query)

        columns = cursor.description

        cols_list = []

        for i in range(len(columns)):
            cols_list.append(columns[i][0])

        update_query = f'SELECT * FROM [{table_name}] WHERE [{column_name}]={uid}'
            
        cursor.execute(update_query)

        data = cursor.fetchall()

        cursor.close()

        return render_template('edit_host.html', columns = cols_list, table_name=table_name, data=data[0])
    except Exception as e:
        print(e)
        flash('There was an error in editing the row. Please check the values carefully.')
        # flash(e)
    return redirect(url_for('host'))

@app.route('/update_host/<table_name>/<uid>', methods = ['POST', 'GET'])
def update_host(table_name, uid):
    global user_id, org_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))

    try:
        if request.method == 'POST':
            if org_id == None:
                # print("G")
                flash('There was an issue in getting the host organization.')
                return redirect(url_for('host_check'))
            
            cursor = connection.cursor()
            form_elements = request.form.to_dict()
            uid_split = uid.split("_")

            update_key_vals = []

            for key, value in form_elements.items():
                if value == 'None' or value.strip() == '':
                    update_key_vals.append(f"[{key}] = NULL")
                else:
                    update_key_vals.append(f"[{key}] = '{value}'")
                
            sep = ", "

            update_query = f'UPDATE [{table_name}] SET {sep.join(update_key_vals)} WHERE {uid_split[0]} = {uid_split[1]};'
            
            print(update_query)

            cursor.execute(update_query)
            connection.commit()

            cursor.close()

            flash('Row updated successfully.')
            return redirect(url_for('host'))
    except Exception as e:
        print(e)
        flash('There was an error in updating the row. Please check the values carefully.')

@app.route('/delete_host/<table_name>/<column_name>/<uid>', methods = ['GET'])
def delete_host(table_name, column_name, uid):
    global user_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))

    try:
        if org_id == None:
            # print("G")
            flash('There was an issue in getting the host organization.')
            return redirect(url_for('host_check'))
        
        cursor = connection.cursor()

        delete_query = f'DELETE FROM [{table_name}] WHERE {column_name} = {uid};'
        
        print(delete_query)

        cursor.execute(delete_query)
        connection.commit()

        cursor.close()

        flash('Row deleted successfully.')
        return redirect(url_for('host'))
    except Exception as e:
        print(e)
        flash('There was an error in deleting the row. Please check the values carefully.')
        # flash(e)

## Admin Routes
@app.route('/admin_resp_check')
def admin_check():
    global user_id, admin_resp
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    try:
        cursor = connection.cursor()

        table_query = f'SELECT [Responsibility] FROM [ADMIN] WHERE [AUserID]={user_id}'

        cursor.execute(table_query)

        result = cursor.fetchall()

        admin_resp = result[0][0]

        print(admin_resp)

        return redirect(url_for('admin'))
    except Exception as e:
        print(e)
        flash('There was an error in showing admin dashboard.')
        # flash(e)
    finally:
        cursor.close()

@app.route('/admin_dashboard')
def admin():
    global user_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    table_names = [[]]
    try:
        if admin_resp != "Super Admin":
            table_names = [admin_table_access[admin_resp]]
            # print(table_names)
        else:
            cursor = connection.cursor()

            table_query = 'SELECT [name] FROM sys.tables'

            cursor.execute(table_query)

            result = cursor.fetchall()
            for table_name in result:
                table_names[0].append(table_name[0])
            cursor.close()
        admin_table_access['Super Admin'] = table_names[0]
        print(table_names)
        return render_template('select.html', tables = table_names)
    except Exception as e:
        print(e)
        flash('There was an error in showing admin dashboard.')
        # flash(e)

@app.route('/read', methods = ['POST', 'GET'])
def read():
    global user_id, admin_resp
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    try:
        if request.method == 'POST':
            table_name = str(request.form.get('table'))
            # print("A")
            # print(table_name)
            if table_name == "None" or table_name == None:
                # print("C")
                table_name = str(request.form.get('nav_table'))
                # print("B")
                # print(table_name)
            
            print("admin_resp:", admin_resp)
            print("table_name:", table_name)

            if admin_resp!= "Super Admin":
                if table_name not in admin_table_access[admin_resp]:
                    flash('You do not have permission to this table.')
                    return redirect(url_for('admin_check'))
            
            cursor = connection.cursor()

            cols_query = f'SELECT * FROM [{table_name}]'

            print(cols_query)

            cursor.execute(cols_query)

            columns = cursor.description

            cols_list = []

            for i in range(len(columns)):
                cols_list.append(columns[i][0])

            data = cursor.fetchall()
            print(data)
            cursor.close()
            
            return render_template('read.html', table = data, columns = cols_list, table_name=table_name, tables=[admin_table_access[admin_resp]])
    except Exception as e:
        print(e)
        flash('There was an error in the table data.')
        # flash(e)
    return redirect(url_for('admin_check'))

@app.route('/insert/<table_name>', methods = ['POST', 'GET'])
def insert(table_name):
    global user_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    try:
        cursor = connection.cursor()
        if admin_resp!= "Super Admin":
                if table_name not in admin_table_access[admin_resp]:
                    flash('You do not have permission to this table.')
                    return redirect(url_for('admin_check'))

        cols_query = f'SELECT TOP 0 * FROM [{table_name}]'

        cursor.execute(cols_query)

        columns = cursor.description
        cursor.close()

        cols_list = []

        for i in range(len(columns)):
            cols_list.append(columns[i][0])
        return render_template('create.html', columns = cols_list, table_name=table_name, skip_id=skip_id_check(table_name), tables=[admin_table_access[admin_resp]])
    except Exception as e:
        print(e)
        flash('There was an error in inserting the row. Please check the values carefully.')
        # flash(e)

@app.route('/create/<table_name>', methods = ['POST'])
def create(table_name):
    global user_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))

    try:
        if request.method == 'POST':
            if admin_resp!= "Super Admin" and table_name not in admin_table_access[admin_resp]:
                flash('You do not have permission to this table.')
                return redirect(url_for('admin_check'))
               
            cursor = connection.cursor()
            form_elements = request.form.to_dict()

            cols_list = []
            vals_list = []
            for i in form_elements:
                cols_list.append(f'[{i}]')
                vals_list.append(f"'{form_elements[i]}'")
            
            sep = ", "
            
            create_query = f"INSERT INTO [{table_name}] ({sep.join(cols_list)}) VALUES ({sep.join(vals_list)});"
            print(create_query)

            cursor.execute(create_query)
            connection.commit()

            cursor.close()

            flash('Row inserted successfully.')
            return redirect(url_for('admin_check'))
    except Exception as e:
        print(e)
        flash('There was an error in creating the row. Please check the values carefully.')
        # flash(e)

@app.route('/edit/<table_name>/<uid>', methods = ['GET'])
def edit(table_name, uid):
    global user_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))

    try:
        if admin_resp!= "Super Admin":
                if table_name not in admin_table_access[admin_resp]:
                    flash('You do not have permission to this table.')
                    return redirect(url_for('admin_check'))
        
        cursor = connection.cursor()

        cols_query = f'SELECT TOP 0 * FROM [{table_name}]'

        cursor.execute(cols_query)

        columns = cursor.description

        cols_list = []

        for i in range(len(columns)):
            cols_list.append(columns[i][0])
        
        uid_split = uid.split("_")

        if double_id_check(table_name):
            update_query = f'SELECT * FROM [{table_name}] WHERE {uid_split[0]}={uid_split[1]} AND {uid_split[2]}={uid_split[3]}'
        else:
            update_query = f'SELECT * FROM [{table_name}] WHERE {uid_split[0]}={uid_split[1]}'
            
        cursor.execute(update_query)

        data = cursor.fetchall()

        cursor.close()

        return render_template('edit.html', columns = cols_list, table_name=table_name, data=data[0], skip_id=double_id_check(table_name), tables=[admin_table_access[admin_resp]])
    except Exception as e:
        print(e)
        flash('There was an error in deleting the row. Please check the values carefully.')
        # flash(e)
    return redirect(url_for('admin_check'))

@app.route('/update/<table_name>/<uid>', methods = ['POST', 'GET'])
def update(table_name, uid):
    global user_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))

    try:
        if request.method == 'POST':
            if admin_resp!= "Super Admin" and table_name not in admin_table_access[admin_resp]:
                flash('You do not have permission to this table.')
                return redirect(url_for('admin_check'))
            
            cursor = connection.cursor()
            form_elements = request.form.to_dict()
            uid_split = uid.split("_")

            update_key_vals = []

            for key, value in form_elements.items():
                if value == 'None' or value.strip() == '':
                    update_key_vals.append(f"[{key}] = NULL")
                else:
                    update_key_vals.append(f"[{key}] = '{value}'")
                
            sep = ", "

            if double_id_check(table_name):
                update_query = f'UPDATE [{table_name}] SET {sep.join(update_key_vals)} WHERE {uid_split[0]} = {uid_split[1]} AND {uid_split[2]} = {uid_split[3]};'
            else:
                update_query = f'UPDATE [{table_name}] SET {sep.join(update_key_vals)} WHERE {uid_split[0]} = {uid_split[1]};'
            
            print(update_query)

            cursor.execute(update_query)
            connection.commit()

            cursor.close()

            flash('Row updated successfully.')
            return redirect(url_for('admin_check'))
    except Exception as e:
        print(e)
        flash('There was an error in updating the row. Please check the values carefully.')
        # flash(e)

@app.route('/delete/<table_name>/<uid>', methods = ['GET'])
def delete(table_name, uid):
    global user_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))

    try:
        if admin_resp!= "Super Admin":
                if table_name not in admin_table_access[admin_resp]:
                    flash('You do not have permission to this table.')
                    return redirect(url_for('admin_check'))
        
        cursor = connection.cursor()

        uid_split = uid.split("_")

        if double_id_check(table_name):
            delete_query = f'DELETE FROM [{table_name}] WHERE {uid_split[0]} = {uid_split[1]} AND {uid_split[2]} = {uid_split[3]};'
        else:
            delete_query = f'DELETE FROM [{table_name}] WHERE {uid_split[0]} = {uid_split[1]};'
        
        print(delete_query)

        cursor.execute(delete_query)
        connection.commit()

        cursor.close()

        flash('Row deleted successfully.')
        return redirect(url_for('admin_check'))
    except Exception as e:
        print(e)
        flash('There was an error in deleting the row. Please check the values carefully.')
        # flash(e)

## Participant routes
@app.route('/participant_dashboard', methods = ['POST', 'GET'])
def get_unregistered_events():
    """
    Call the getUnregisteredEvents stored procedure to fetch events a participant has not registered for.
    """
    global user_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    try:
        cursor = connection.cursor()

        # Call the stored procedure
        cursor.execute("EXEC getUnregisteredEventsWithDate @ParticipantUserID=?", user_id)
        
        # Fetch the results
        columns = [column[0] for column in cursor.description]
        events = cursor.fetchall()

        return render_template('pevents.html', events = events, columns = columns)
    except Exception as e:
        print(e)
        flash('There was an error in fetching all the events.')
    finally:
        cursor.close()

@app.route('/show', methods=['GET', 'POST'])
def get_event_details():
    """
    Call the getEventVenueAndTicketDetails stored procedure to fetch event, venue, and ticket details.
    """
    global user_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    try:
        cursor = connection.cursor()

        event_id = str(request.form.get('event_id'))

        # Call the stored procedure for event and venue details
        cursor.execute("EXEC getEventVenueAndTicketDetails @EventID=?", event_id)
        
        event_venue = cursor.fetchall()

        # Move to the second result set (seat and ticket details)
        cursor.nextset()
        seat_ticket = cursor.fetchall()

        return render_template('show_pevent.html', event_venue = event_venue[0], seat_ticket = seat_ticket, event_id = event_id)
    except Exception as e:
        print(e)
        flash('There was an error in fetching event details.')
    finally:
        cursor.close()

@app.route('/book_ticket', methods=['POST'])
def book_ticket():
    global user_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    try :
        # Retrieve event_id from the form
        event_id = request.form.get("event_id")
        # print(request.form.items())

        for ticket_id, quantity in request.form.items():
            print(ticket_id, quantity)

        # Retrieve ticket data
        seat_id = None
        quant = None
        transaction_time = datetime.now()

        for ticket_id, quantity in request.form.items():
            if ticket_id.startswith("ticket_") and int(quantity) > 0:
                seat_id = ticket_id.split("_")[1]
                quant = quantity
        
        cursor = connection.cursor()
        form_elements = request.form.to_dict()

        cols_list = ["PUserID", "EventID", "SeatID", "TicketQuantity", "TransactionTime"]
        vals_list = [str(user_id), str(event_id), str(seat_id), str(quant), "GETDATE()"]
        
        sep = ", "
        
        create_query = f"INSERT INTO [REGISTRATION] ({sep.join(cols_list)}) VALUES ({sep.join(vals_list)});"
        print(create_query)

        cursor.execute(create_query)
        connection.commit()

        cursor.close()

        flash('Booking Successfully.')
        return render_template("booking_success.html")
    except Exception as e:
        print(e)
        flash('Booking failed.')

@app.route('/event_registrations', methods=['POST', 'GET'])
def get_tickets():
    global user_id
    if user_id == None:
        flash('You have been logged out due to inactivity. Login again to continue.')
        return redirect(url_for('landing'))
    try:
        cursor = connection.cursor()
        # print(user_id)

        # Call the stored procedure for event and venue details
        cursor.execute("EXEC getUserEvents @UserID=?", user_id)
        
        event_reg_tickets = cursor.fetchall()

        columns = cursor.description

        cols_list = []

        for i in range(len(columns)):
            cols_list.append(columns[i][0])

        return render_template('registered_pevents.html', events = event_reg_tickets, columns = cols_list)
    except Exception as e:
        print(e)
        flash('There was an error in fetching user registrations.')
    finally:
        cursor.close()

if __name__ == '__main__':
    app.run(port=8000, debug=True)