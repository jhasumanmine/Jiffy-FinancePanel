from flask import Flask, jsonify, request, send_file
import mysql.connector
import pandas as pd
import io

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

# Endpoint 1: Fetch Profit & Loss Data
@app.route('/api/profit_loss', methods=['GET'])
def get_profit_loss():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM profit_loss')
    profit_loss_data = cursor.fetchall()
    cursor.close()
    conn.close()

    result = []
    for row in profit_loss_data:
        result.append({
            'date': row['date'],
            'income': row['income'],
            'expenses': row['expenses'],
            'net_profit': row['net_profit']
        })
    return jsonify(result)

# Endpoint 2: Fetch Cash Flow Data
@app.route('/api/cash_flow', methods=['GET'])
def get_cash_flow():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM cash_flow')
    cash_flow_data = cursor.fetchall()
    cursor.close()
    conn.close()

    result = []
    for row in cash_flow_data:
        result.append({
            'date': row['date'],
            'inflows': row['inflows'],
            'outflows': row['outflows'],
            'net_cash_flow': row['net_cash_flow']
        })
    return jsonify(result)

# Endpoint 3: Fetch Balance Sheet Data
@app.route('/api/balance_sheet', methods=['GET'])
def get_balance_sheet():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM balance_sheet')
    balance_sheet_data = cursor.fetchall()
    cursor.close()
    conn.close()

    result = []
    for row in balance_sheet_data:
        result.append({
            'date': row['date'],
            'assets': row['assets'],
            'liabilities': row['liabilities'],
            'equity': row['equity']
        })
    return jsonify(result)

# Endpoint 4: Download report as CSV or PDF
@app.route('/api/download', methods=['GET'])
def download_report():
    report_type = request.args.get('report')  # report can be profit_loss, cash_flow, balance_sheet
    format_type = request.args.get('format')  # format can be csv or pdf

    conn = get_db_connection()
    cursor = conn.cursor()

    if report_type == 'profit_loss':
        query = 'SELECT * FROM profit_loss'
    elif report_type == 'cash_flow':
        query = 'SELECT * FROM cash_flow'
    elif report_type == 'balance_sheet':
        query = 'SELECT * FROM balance_sheet'
    else:
        return jsonify({'error': 'Invalid report type'}), 400

    cursor.execute(query)
    data = cursor.fetchall()

    column_names = [i[0] for i in cursor.description]  # Get column names
    df = pd.DataFrame(data, columns=column_names)
    cursor.close()
    conn.close()

    if format_type == 'csv':
        # Return CSV
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name=f"{report_type}.csv")

    elif format_type == 'pdf':
        # Return PDF (placeholder, can use PDF generation libraries like FPDF or ReportLab)
        return jsonify({'message': 'PDF generation is not implemented in this example'})

    return jsonify({'error': 'Invalid format type'}), 400

if __name__ == '__main__':
    app.run(debug=True)
