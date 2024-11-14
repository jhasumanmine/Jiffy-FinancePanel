from flask import Flask, jsonify, request
import mysql.connector
from mysql.connector import Error
from decimal import Decimal

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

# API to get income vs expenses data for bar chart, with company_id filter
@app.route('/api/financials', methods=['GET'])
def get_financials():
    try:
        # Get the company_id from query parameters
        company_id = request.args.get('company_id')
        
        if not company_id:
            return jsonify({'error': 'company_id is required'}), 400
        
        connection = db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Query to get total income per project for a specific company
        query_income = """
            SELECT source AS project_name, SUM(amount) AS total_income
            FROM income
            WHERE company_id = %s
            GROUP BY source
        """
        
        # Query to get total expenses per project for a specific company
        query_expenses = """
            SELECT category AS project_name, SUM(amount) AS total_expenses
            FROM expenses
            WHERE company_id = %s
            GROUP BY category
        """
        
        # Fetch income data
        cursor.execute(query_income, (company_id,))
        income_data = cursor.fetchall()

        # Fetch expenses data
        cursor.execute(query_expenses, (company_id,))
        expense_data = cursor.fetchall()

        # Merge income and expenses data by project_name
        project_financials = {}
        
        # Combine income data
        for income in income_data:
            project_name = income['project_name']
            project_financials[project_name] = {
                'total_income': float(income['total_income']),
                'total_expenses': 0.00,  # Default value until expenses are added
                'profit': 0.00  # Default value
            }

        # Add or merge expenses data
        for expense in expense_data:
            project_name = expense['project_name']
            if project_name in project_financials:
                project_financials[project_name]['total_expenses'] = float(expense['total_expenses'])
            else:
                project_financials[project_name] = {
                    'total_income': 0.00,
                    'total_expenses': float(expense['total_expenses']),
                    'profit': 0.00
                }

        # Calculate profit for each project
        for project_name, financials in project_financials.items():
            financials['profit'] = financials['total_income'] - financials['total_expenses']

        return jsonify(project_financials)

    except Error as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if connection:
            cursor.close()
            connection.close()

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
