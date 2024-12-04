# Timothy Sims
import streamlit as st
import mysql.connector

def checkUser(email):
    cnx = mysql.connector.connect(user='root', password='password', host='localhost', database='HouseRentals')    # Connect to the database
    cursor = cnx.cursor()   # Create a cursor object
    
    cursor.execute("SELECT HostID FROM Host WHERE email = %s", (email,))    # first search for the email among hosts
    host_result = cursor.fetchone() # Fetch the result
    
    cursor.execute("SELECT GuestID FROM Guest WHERE email = %s", (email,))  # then search in guests
    guest_result = cursor.fetchone()

    cursor.close()
    cnx.close()

    if host_result: # if the email is found in hosts, return the user type and the ID
        return 'Host', host_result[0]
    elif guest_result:  # if the email is found in guests, return the user type and the ID
        return 'Guest', guest_result[0]
    else:   # if the email is not found, return None
        return None, None
    
def getHostBalance(hostID):
    try:
        cnx = mysql.connector.connect(user='root', password='password', host='localhost', database='HouseRentals')    # Connect to the database
        cursor = cnx.cursor()   # Create a cursor object
        query = "SELECT balance FROM Host WHERE HostID = %s"    # Query to get the balance of the host
        cursor.execute(query, (hostID,))    # Execute the query
        balance = cursor.fetchone()[0]  # Fetch the result

        cursor.close()
        cnx.close()

        return balance

    except mysql.connector.Error as err:    # If there is an error, return None and print the error
        print(f"Error: {err}")
        return None

    
def getPropertyByMaxPrice(max_price):
    cnx = mysql.connector.connect(user='root', password='password', host='localhost', database='HouseRentals')    # Connect to the database
    cursor = cnx.cursor()
    query = "SELECT * FROM property WHERE price < %s"   # Query to get the properties with price less than the max price
    cursor.execute(query, (max_price,)) # Execute the query
    rows = cursor.fetchall()    # Fetch the result

    cursor.close()
    cnx.close()

    return rows # Return the result
    
def showProperties(hostID):
    cnx = mysql.connector.connect(user='root', password='password', host='localhost', database='HouseRentals')    # Connect to the database
    cursor = cnx.cursor()   # Create a cursor object

    cursor.execute("SELECT * FROM Property WHERE HostID = %s", (hostID,))   # Query to get the properties of the host
    properties = cursor.fetchall()  # Fetch the result

    cursor.close()
    cnx.close()

    return properties   # Return the result

def removeProperty(propertyID):
    try:
        cnx = mysql.connector.connect(user='root', password='password', host='localhost', database='HouseRentals')    # Connect to the database
        cursor = cnx.cursor()
        cursor.execute("SELECT isBooked FROM Property WHERE propertyID = %s", (propertyID,))    # Query to check if the property is booked
        is_booked = cursor.fetchone()[0]    # Fetch the result

        if not is_booked:   # If the property is not booked, delete it
            cursor.execute("DELETE FROM Property WHERE propertyID = %s", (propertyID,))   # Query to delete the property
            cnx.commit()
            return "Property removed successfully."
        else:   # If the property is booked, return an error message
            return "Cannot remove a booked property."

    except mysql.connector.Error as err:
        cnx.rollback()
        return f"Error: {err}"

    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()


def listProperty(hostID, propertyName, address, price, description):
    try:
        cnx = mysql.connector.connect(user='root', password='password', host='localhost', database='HouseRentals')    # Connect to the database
        cursor = cnx.cursor()   # Create a cursor object

        cursor.execute("SELECT MAX(propertyID) FROM Property")  # Query to get the max property ID
        max_id_result = cursor.fetchone()
        next_propertyID = (max_id_result[0] or 0) + 1   # Get the next property ID, since I did not use autoincrement I add one to the current highest ID

        cursor.execute("SELECT COUNT(*) FROM Property WHERE HostID = %s", (hostID,))    # Query to check if the host already has a property listed
        count = cursor.fetchone()[0]

        if count == 0:
            query = """
            INSERT INTO Property (propertyID, HostID, propertyName, address, price, description, averageReview, isBooked)
            VALUES (%s, %s, %s, %s, %s, %s, NULL, 0)
            """
            cursor.execute(query, (next_propertyID, hostID, propertyName, address, price, description)) # Query to insert the new property
            
            cnx.commit()
            print("Property listed successfully.")
        else:   # If the host already has a property listed, return an error message
            print("This host already has a property listed.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        cnx.rollback()

    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()

def bookProperty(guestID, propertyID):
    try:
        cnx = mysql.connector.connect(user='root', password='password', host='localhost', database='HouseRentals')    # Connect to the database
        cursor = cnx.cursor()
        cursor.execute("SELECT MAX(BookingID) FROM Booking")    # Query to get the max booking ID
        max_id_result = cursor.fetchone()
        next_bookingID = (max_id_result[0] or 0) + 1    # Get the next booking ID, since I did not use autoincrement I add one to the current highest ID
        cursor.execute("START TRANSACTION;")
        cursor.execute("SELECT EXISTS (SELECT 1 FROM Property WHERE PropertyID = %s AND IsBooked = 0), EXISTS (SELECT 1 FROM Guest WHERE GuestID = %s AND BookingID IS NULL)", (propertyID, guestID))
        propertyAvailable, guestFree = cursor.fetchone()    # Check if the property is available and the guest does not have a booking

        if propertyAvailable and guestFree: # If the property is available and the guest does not have a booking, book the property
            cursor.execute("INSERT INTO Booking (BookingID, GuestID, PropertyID, TotalPrice) SELECT %s, %s, %s, (SELECT Price FROM Property WHERE PropertyID = %s)", (next_bookingID, guestID, propertyID, propertyID))
            cursor.execute("UPDATE Property SET IsBooked = 1 WHERE PropertyID = %s", (propertyID,)) # Query to update the property to booked
            cursor.execute("UPDATE Guest SET BookingID = %s WHERE GuestID = %s", (next_bookingID, guestID)) # Query to update the guest to have a booking

            cnx.commit()
            return "Booking successful!"    # Return a success message

        else:
            return None, "Booking failed: Property not available or guest already has a booking."   # Return an error message

    except mysql.connector.Error as err:
        cnx.rollback()
        return None, f"Booking failed: {err}"

    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()

def getGuestBookings(guestID):
    try:
        cnx = mysql.connector.connect(user='root', password='password', host='localhost', database='HouseRentals')    # Connect to the database
        cursor = cnx.cursor()   # Create a cursor object
        query = """
        SELECT B.BookingID, P.PropertyName, P.Address, P.Price, P.Description
        FROM Booking B
        JOIN Property P ON B.PropertyID = P.PropertyID
        WHERE B.GuestID = %s
        """
        cursor.execute(query, (guestID,))   # Query to get the guest's bookings
        bookings = cursor.fetchall()    # Fetch the result

        cursor.close()  # Close the cursor and the connection
        cnx.close()

        return bookings # Return the result

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []
    
def cancelBooking(guestID, bookingID):
    try:
        cnx = mysql.connector.connect(user='root', password='password', host='localhost', database='HouseRentals')    # Connect to the database
        cursor = cnx.cursor()   # Create a cursor object
        cursor.execute("SELECT PropertyID FROM Booking WHERE BookingID = %s", (bookingID,))   # Query to get the property ID of the booking
        propertyID = cursor.fetchone()[0]
        cursor.execute("START TRANSACTION;")    # Start a transaction
        cursor.execute("UPDATE Guest SET BookingID = NULL WHERE GuestID = %s", (guestID,))  # Query to update the guest to not have a booking
        cursor.execute("UPDATE Property SET IsBooked = 0 WHERE PropertyID = %s", (propertyID,)) # Query to update the property to not be booked
        cursor.execute("DELETE FROM Booking WHERE BookingID = %s", (bookingID,))    # Query to delete the booking

        cnx.commit()    # Commit the transaction
        return "Booking cancelled successfully."    # Return a success message

    except mysql.connector.Error as err:
        cnx.rollback()
        return f"Error: {err}"

    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()


if 'user_type' not in st.session_state:   # If the user type is not initialized, initialize it
    st.session_state['user_type'] = None    # Initialize the user type
    st.session_state['user_id'] = None  # Initialize the user ID

# Streamlit GUI starts here
st.title('Short Term Rentals')  # Title of the app

if st.session_state['user_type'] is None:   # If the user type is not set, show the login form
    email = st.text_input("Enter your email:")  # Input field for the email
    if st.button('Login'):  # Login button
        user_type, user_id = checkUser(email)   # Check if the email exists in the database
        st.session_state['user_type'] = user_type
        st.session_state['user_id'] = user_id
        if user_type:
            st.success(f"Logged in as {user_type} with ID {user_id}")   # Show a success message if the email exists
        else:
            st.error("Email not found. Please try again.")  # Show an error message if the email does not exist

if st.session_state['user_type'] == 'Host':
    host_balance = getHostBalance(st.session_state['user_id'])  # Get the balance of the host
    if host_balance is not None:    # If the balance is not None, show the balance
        st.write(f"Your current balance: ${host_balance}")  # Show the balance
    properties = showProperties(st.session_state['user_id'])    # Get the properties of the host
    if properties:
        st.write("Your Properties (cannot remove booked properties):")  # Show the properties
        for prop in properties:
            with st.container():    # Container to show the property and the remove button
                st.write(f"ID: {prop[0]}, Name: {prop[2]}, Address: {prop[3]}, Price: {prop[4]}, Booked: {'Yes' if prop[7] else 'No'}")
                remove_button = st.button("Remove", key=f"remove_{prop[0]}")    # Remove button
                if remove_button:   # If the remove button is clicked, remove the property
                    remove_message = removeProperty(prop[0])
                    st.write(remove_message)
                    properties = showProperties(st.session_state['user_id'])    # Refresh the properties
    else:
        st.write("You currently have no properties listed.")    # Show a message if the host has no properties listed
        with st.form(key='add_property_form'):  # Form to add a new property
            st.write("List a New Property") # Title of the form
            new_propertyName = st.text_input("Property Name")   # Input field for the property name
            new_address = st.text_input("Address")  # Input field for the address
            new_price = st.number_input("Price", min_value=0.0, format='%f')    # Input field for the price
            new_description = st.text_area("Description")   # Input field for the description
            submit_button = st.form_submit_button(label='List Property')    # Submit button

            if submit_button:   # If the submit button is clicked, list the property
                listProperty(st.session_state['user_id'], new_propertyName, new_address, new_price, new_description)
                st.success("Property listed successfully!")

elif st.session_state['user_type'] == 'Guest':
    guest_bookings = getGuestBookings(st.session_state['user_id'])  # Get the guest's bookings
    if guest_bookings:  # If the guest has bookings, show the bookings
        st.write("Your Current Bookings:")  # Title of the section
        for booking in guest_bookings:  # Show the bookings
            with st.container():    # Container to show the booking and the cancel button
                st.write(f'''
                    Booking ID: {booking[0]}
                    Property Name: {booking[1]}
                    Address: {booking[2]}
                    Price: {booking[3]}
                    Description: {booking[4]}
                ''')
                cancel_button = st.button("Cancel Booking", key=f"cancel_{booking[0]}")   # Cancel button
                if cancel_button:   # If the cancel button is clicked, cancel the booking
                    cancel_message = cancelBooking(st.session_state['user_id'], booking[0])
                    st.write(cancel_message)
                    guest_bookings = getGuestBookings(st.session_state['user_id'])  # Refresh the bookings
    elif 'successful_booking' not in st.session_state or not st.session_state['successful_booking']:
        st.write("No current bookings. Available Properties:")  # Show a message if the guest has no bookings
        min_price = st.number_input("Enter a maximum price:", min_value=0.0, value=0.0, step=10.0)
        properties = getPropertyByMaxPrice(min_price)   # Get the properties with price less than the max price
        for prop in properties: # Show the properties
            with st.container():
                st.write(f'''Property ID: {prop[0]}
                            Host ID: {prop[1]}
                            Property Name: {prop[2]}
                            Address: {prop[3]}
                            Price: {prop[4]}
                            Average rating: {prop[5]}
                            Description: {prop[6]}
                            Booked: {"Yes" if prop[7] == 1 else "No"}''')
                if not prop[7]: # If the property is not booked, show the book button
                    book_button = st.button("Book Now", key=f"book_{prop[0]}")
                    if book_button: # If the book button is clicked, proceed to confirm the booking
                        st.session_state['selected_property'] = prop[0]
        if 'selected_property' in st.session_state: # If the property is selected, show the confirmation button
            st.write(f"You have selected Property ID: {st.session_state['selected_property']}")
            confirm_booking = st.button("Confirm Booking")  # Confirm button
            if confirm_booking: # If the confirm button is clicked, book the property
                booking_message = bookProperty(st.session_state['user_id'], st.session_state['selected_property'])  # Book the property
                st.write(booking_message)   # Show the result of the booking
refresh_button = st.button("Refresh")   # Refresh button

if refresh_button:  # If the refresh button is clicked, refresh the page
    st.rerun()  # Refresh the page