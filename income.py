import datetime
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Database connection function
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='income_panel',
            user='root',
            password=''  # Leave password empty if no password set for MySQL
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Route for adding income entry
@app.route('/api/add_income', methods=['POST'])
def add_income():
    data = request.json
    
    # Validate required fields
    required_fields = ['date', 'source', 'amount', 'category', 'payment_method', 'company_id']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"{field} is required"}), 400
    
    try:
        connection = create_connection()
        if not connection:
            return jsonify({"error": "Failed to connect to the database"}), 500
        
        cursor = connection.cursor()

        # Insert income data into the database, including company_id
        query = """
            INSERT INTO income (date, source, amount, category, payment_method, transaction_id, notes, company_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['date'],
            data['source'],
            data['amount'],
            data['category'],
            data['payment_method'],
            data.get('transaction_id', None),  # Optional field
            data.get('notes', None),  # Optional field
            data['company_id']  # Newly added required field
        ))
        connection.commit()
        return jsonify({"message": "Income entry added successfully"}), 201
    
    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/income', methods=['GET'])
def get_income_records():
    try:
        connection = create_connection()
        if not connection:
            return jsonify({"error": "Failed to connect to the database"}), 500
        
        cursor = connection.cursor(dictionary=True)

        # Base query
        query = """
            SELECT id, date, source, amount, category, payment_method, transaction_id, notes, company_id 
            FROM income
            WHERE 1 = 1
        """

        # Filtering by date range, category, source, and company_id
        params = []
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        category = request.args.get('category')
        source = request.args.get('source')
        company_id = request.args.get('company_id')  # New filter for company_id

        if date_from:
            query += " AND date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND date <= %s"
            params.append(date_to)
        if category:
            query += " AND category = %s"
            params.append(category)
        if source:
            query += " AND source LIKE %s"
            params.append(f"%{source}%")
        if company_id:
            query += " AND company_id = %s"
            params.append(company_id)

        # Sorting (default to sorting by date)
        sort_by = request.args.get('sort_by', 'date')
        sort_order = request.args.get('sort_order', 'ASC')  # ASC or DESC
        query += f" ORDER BY {sort_by} {sort_order}"

        # Pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        # Execute the query
        cursor.execute(query, tuple(params))
        income_records = cursor.fetchall()

        # Format data for response
        for record in income_records:
            record['amount'] = f"${record['amount']:,}"  # Format amount as currency
            if record['notes'] and len(record['notes']) > 50:
                record['notes'] = record['notes'][:50] + "..."  # Truncate long notes

        # Return paginated results
        return jsonify({
            "data": income_records,
            "pagination": {
                "page": page,
                "per_page": per_page
            }
        })

    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/expenses', methods=['POST'])
def add_expense():
    data = request.json
    
    # Validate required fields
    required_fields = ['date', 'category', 'amount', 'payment_method', 'company_id']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"{field} is required"}), 400
    
    try:
        connection = create_connection()
        if not connection:
            return jsonify({"error": "Failed to connect to the database"}), 500
        
        cursor = connection.cursor()

        # Insert expense data into the database
        query = """
            INSERT INTO expenses (date, category, amount, notes, payment_method, company_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['date'],
            data['category'],
            data['amount'],
            data.get('notes', None),  # Optional field
            data['payment_method'],
            data['company_id']
        ))
        connection.commit()
        return jsonify({"message": "Expense entry added successfully"}), 201
    
    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()




@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    try:
        connection = create_connection()
        if not connection:
            return jsonify({"error": "Failed to connect to the database"}), 500
        
        cursor = connection.cursor(dictionary=True)

        # Base query
        query = """
            SELECT id, date, category, amount, notes, payment_method, company_id
            FROM expenses
            WHERE 1 = 1
        """

        # Filtering by category
        params = []
        category = request.args.get('category')
        if category:
            query += " AND category = %s"
            params.append(category)

        # Filter by company_id
        company_id = request.args.get('company_id')
        if company_id:
            query += " AND company_id = %s"
            params.append(company_id)

        # Searching by amount, date, or notes
        search = request.args.get('search')
        if search:
            search_query = "%" + search + "%"
            query += " AND (amount LIKE %s OR date LIKE %s OR notes LIKE %s)"
            params.extend([search_query, search_query, search_query])

        # Sorting (default to sorting by date)
        sort_by = request.args.get('sort_by', 'date')
        sort_order = request.args.get('sort_order', 'ASC')  # ASC or DESC
        query += f" ORDER BY {sort_by} {sort_order}"

        # Pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        # Execute the query
        cursor.execute(query, tuple(params))
        expense_records = cursor.fetchall()

        # Format data for response
        for record in expense_records:
            record['amount'] = f"${record['amount']:,}"  # Format amount as currency
            if record['notes'] and len(record['notes']) > 50:
                record['notes'] = record['notes'][:50] + "..."  # Truncate long notes

        # Return paginated results
        return jsonify({
            "data": expense_records,
            "pagination": {
                "page": page,
                "per_page": per_page
            }
        })

    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/expenses/<int:id>', methods=['DELETE'])
def delete_expense(id):
    try:
        connection = create_connection()
        if not connection:
            return jsonify({"error": "Failed to connect to the database"}), 500
        
        cursor = connection.cursor()

        # Check if the expense exists with the provided company_id
        company_id = request.args.get('company_id')
        if not company_id:
            return jsonify({"error": "company_id is required"}), 400

        # Verify that the expense belongs to the specified company_id
        select_query = "SELECT * FROM expenses WHERE id = %s AND company_id = %s"
        cursor.execute(select_query, (id, company_id))
        expense_record = cursor.fetchone()
        
        if not expense_record:
            return jsonify({"error": "Expense not found or does not belong to the specified company"}), 404

        # Delete query
        delete_query = "DELETE FROM expenses WHERE id = %s AND company_id = %s"
        cursor.execute(delete_query, (id, company_id))
        connection.commit()

        return jsonify({"message": "Expense entry deleted successfully"}), 200

    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/expenses/<int:id>', methods=['PUT'])
def edit_expense(id):
    data = request.json
    try:
        connection = create_connection()
        if not connection:
            return jsonify({"error": "Failed to connect to the database"}), 500
        
        cursor = connection.cursor()

        # Verify if the expense exists and belongs to the specified company_id
        company_id = request.args.get('company_id')
        if not company_id:
            return jsonify({"error": "company_id is required"}), 400

        # Check if the expense with the provided id and company_id exists
        select_query = "SELECT * FROM expenses WHERE id = %s AND company_id = %s"
        cursor.execute(select_query, (id, company_id))
        expense_record = cursor.fetchone()
        
        if not expense_record:
            return jsonify({"error": "Expense not found or does not belong to the specified company"}), 404

        # Update query
        update_query = """
            UPDATE expenses 
            SET date = %s, category = %s, amount = %s, notes = %s, payment_method = %s
            WHERE id = %s AND company_id = %s
        """
        cursor.execute(update_query, (
            data['date'],
            data['category'],
            data['amount'],
            data.get('notes', None),
            data.get('payment_method', None),
            id,
            company_id
        ))
        connection.commit()

        return jsonify({"message": "Expense entry updated successfully"}), 200

    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()



if __name__ == '__main__':
    app.run(debug=True)
