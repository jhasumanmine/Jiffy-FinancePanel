from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
import uuid
from datetime import datetime

app = Flask(__name__)

# Database connection function
def db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='income_panel',  # Your database name
            user='root',  # Your MySQL username
            password=''  # Your MySQL password
        )
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None

# Endpoint to create a new invoice
@app.route('/api/invoices', methods=['POST'])
def create_invoice():
    try:
        connection = db_connection()
        cursor = connection.cursor()

        # Get form data from the request body
        data = request.json
        client_name = data.get('client_name')
        services_provided = data.get('services_provided')
        amount = data.get('amount')
        due_date = data.get('due_date')
        company_id = data.get('company_id')
        payment_status = data.get('payment_status', 'Pending')  # Default to 'Pending' if not provided

        # Auto-generate a unique invoice number
        invoice_number = str(uuid.uuid4())[:8]

        # Insert new invoice data into the database
        insert_invoice_query = """
            INSERT INTO invoices (invoice_number, client_name, services_provided, amount, due_date, payment_status, company_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_invoice_query, (
            invoice_number, client_name, services_provided, amount, due_date, payment_status, company_id
        ))
        connection.commit()

        return jsonify({
            'message': 'Invoice created successfully',
            'invoice_number': invoice_number
        }), 201

    except Error as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if connection:
            cursor.close()
            connection.close()


# Endpoint to list all invoices
@app.route('/api/invoices', methods=['GET'])
def list_invoices():
    try:
        connection = db_connection()
        cursor = connection.cursor(dictionary=True)

        # Base query to fetch all invoices
        fetch_invoices_query = """
            SELECT invoice_number, client_name, services_provided, amount, due_date, payment_status, company_id, created_at
            FROM invoices
            WHERE 1 = 1
        """

        # Filtering by company_id if provided
        company_id = request.args.get('company_id')
        if company_id:
            fetch_invoices_query += " AND company_id = %s"
            cursor.execute(fetch_invoices_query, (company_id,))
        else:
            cursor.execute(fetch_invoices_query)

        invoices = cursor.fetchall()

        return jsonify(invoices), 200

    except Error as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if connection:
            cursor.close()
            connection.close()


# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
