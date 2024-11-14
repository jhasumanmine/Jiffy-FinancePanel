from binascii import Error
from flask import Flask, jsonify, request, send_file
import mysql.connector
import pandas as pd
import io
from fpdf import FPDF 

app = Flask(__name__)

# Database connection function
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Add your password if needed
        database="income_panel"  # Change to your actual database name
    )
    return conn

# Endpoint 1: Fetch Profit & Loss Data with company_id filter
@app.route('/api/profit_loss', methods=['GET'])
def get_profit_loss():
    try:
        # Get the company_id from query parameters
        company_id = request.args.get('company_id')
        
        if not company_id:
            return jsonify({'error': 'company_id is required'}), 400
        
        # Database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to fetch profit and loss data for a specific company
        cursor.execute('SELECT * FROM profit_loss WHERE company_id = %s', (company_id,))
        profit_loss_data = cursor.fetchall()

        if not profit_loss_data:
            return jsonify({'error': 'No profit/loss data found for this company'}), 404

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Prepare the result data
        result = []
        for row in profit_loss_data:
            result.append({
                'date': row['date'],
                'income': row['income'],
                'expenses': row['expenses'],
                'net_profit': row['net_profit']
            })
        
        return jsonify(result)

    except Exception as e:
        # Log the error for debugging
        print(f"Error: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500



# Endpoint 2: Fetch Cash Flow Data with company_id filter
@app.route('/api/cash_flow', methods=['GET'])
def get_cash_flow():
    try:
        # Get the company_id from query parameters
        company_id = request.args.get('company_id')
        
        if not company_id:
            return jsonify({'error': 'company_id is required'}), 400
        
        # Database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to fetch cash flow data for a specific company
        cursor.execute('SELECT * FROM cash_flow WHERE company_id = %s', (company_id,))
        cash_flow_data = cursor.fetchall()

        if not cash_flow_data:
            return jsonify({'error': 'No cash flow data found for this company'}), 404

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Prepare the result data
        result = []
        for row in cash_flow_data:
            result.append({
                'date': row['date'],
                'inflows': row['inflows'],
                'outflows': row['outflows'],
                'net_cash_flow': row['net_cash_flow']
            })
        
        return jsonify(result)

    except Exception as e:
        # Log the error for debugging
        print(f"Error: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500


# Endpoint 3: Fetch Balance Sheet Data with company_id filter
@app.route('/api/balance_sheet', methods=['GET'])
def get_balance_sheet():
    try:
        # Get the company_id from query parameters
        company_id = request.args.get('company_id')
        
        if not company_id:
            return jsonify({'error': 'company_id is required'}), 400
        
        # Database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to fetch balance sheet data for a specific company
        cursor.execute('SELECT * FROM balance_sheet WHERE company_id = %s', (company_id,))
        balance_sheet_data = cursor.fetchall()

        if not balance_sheet_data:
            return jsonify({'error': 'No balance sheet data found for this company'}), 404

        # Close the cursor and connection
        cursor.close()
        conn.close()

        # Prepare the result data
        result = []
        for row in balance_sheet_data:
            result.append({
                'date': row['date'],
                'assets': row['assets'],
                'liabilities': row['liabilities'],
                'equity': row['equity']
            })
        
        return jsonify(result)

    except Exception as e:
        # Log the error for debugging
        print(f"Error: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500


@app.route('/api/download', methods=['GET'])
def download_report():
    report_type = request.args.get('report')  # report can be profit_loss, cash_flow, balance_sheet
    format_type = request.args.get('format')  # format can be csv or pdf

    if not report_type or not format_type:
        return jsonify({'error': 'Missing report or format type'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Determine the query based on the report type
    if report_type == 'profit_loss':
        query = 'SELECT * FROM profit_loss'
    elif report_type == 'cash_flow':
        query = 'SELECT * FROM cash_flow'
    elif report_type == 'balance_sheet':
        query = 'SELECT * FROM balance_sheet'
    else:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Invalid report type'}), 400

    cursor.execute(query)
    data = cursor.fetchall()

    if not data:
        cursor.close()
        conn.close()
        return jsonify({'error': f'No data found for report type: {report_type}'}), 404

    column_names = [i[0] for i in cursor.description]  # Get column names
    df = pd.DataFrame(data, columns=column_names)
    cursor.close()
    conn.close()

    # Handle CSV export
    if format_type == 'csv':
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()), 
                         mimetype='text/csv', 
                         as_attachment=True, 
                         download_name=f"{report_type}.csv")

    # Handle PDF export
    elif format_type == 'pdf':
        pdf = generate_pdf(df, report_type)
        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        return send_file(pdf_output, mimetype='application/pdf', as_attachment=True, download_name=f"{report_type}.pdf")

    return jsonify({'error': 'Invalid format type'}), 400


def generate_pdf(df, report_type):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, f"{report_type.capitalize()} Report", ln=True, align='C')

    # Column headers
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    for col in df.columns:
        pdf.cell(40, 10, col, border=1, align='C')
    pdf.ln()

    # Data rows
    for index, row in df.iterrows():
        for value in row:
            pdf.cell(40, 10, str(value), border=1, align='C')
        pdf.ln()

    return pdf
if __name__ == '__main__':
    app.run(debug=True)
