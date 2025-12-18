import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify
import io
import os
import pandas as pd
import yfinance as yf
from models.data_analysis import compute_moving_averages, compute_price_stats, prepare_candlestick_data
from models.forecast_model import arima_forecast, lstm_forecast

app = Flask(__name__)
app.secret_key = 'replace-with-a-secure-key'


# Home page
@app.route('/')
def index():
    return render_template('index.html')


# Analysis page (form posts here)
@app.route('/analyze', methods=['POST'])
def analyze():
    ticker = request.form.get('ticker', '').upper()
    period = request.form.get('period', '1y')
    analysis_type = request.form.get('analysis_type', 'moving_average')

    if not ticker:
        flash('Please enter a ticker symbol')
        return redirect(url_for('index'))

    try:
        # Fetch data
        data = yf.download(ticker, period=period, progress=False)
        if data is None or data.empty:
            flash('No data found for ticker: ' + ticker)
            return redirect(url_for('index'))

        # Compute analytics
        ma_df = compute_moving_averages(data)
        stats = compute_price_stats(data)
        candlestick = prepare_candlestick_data(data)

        # Save CSV to memory for download option
        csv_buffer = io.StringIO()
        data.to_csv(csv_buffer)
        csv_buffer.seek(0)

        # Prepare JSON-safe strings (reset index so dates are included)
        ma_json = ma_df.reset_index().to_json(orient='records', date_format='iso')
        candlestick_json = candlestick.reset_index().to_json(orient='records', date_format='iso')

        # Render analysis template
        return render_template('analysis.html',
                               ticker=ticker,
                               period=period,
                               analysis_type=analysis_type,
                               ma_json=ma_json,
                               stats=stats,
                               candlestick_json=candlestick_json,
                               raw_csv=csv_buffer.getvalue())

    except Exception as e:
        flash('Error fetching or processing data: ' + str(e))
        return redirect(url_for('index'))


# Forecast endpoint
@app.route('/forecast', methods=['POST'])
def forecast():
    ticker = request.form.get('ticker', '').upper()
    model_type = request.form.get('model_type', 'arima')
    try:
        periods = int(request.form.get('periods', 30))
    except Exception:
        periods = 30

    if not ticker:
        return jsonify({'error': 'Ticker required'}), 400

    try:
        data = yf.download(ticker, period='5y', progress=False)
        if data is None or data.empty:
            return jsonify({'error': 'No data found for ticker'}), 404

        if model_type == 'arima':
            forecast_df = arima_forecast(data['Close'], steps=periods)
        else:
            forecast_df = lstm_forecast(data['Close'], steps=periods)

        return jsonify({'forecast': forecast_df.reset_index().to_dict(orient='records')})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Download CSV
@app.route('/download_csv', methods=['POST'])
def download_csv():
    csv_data = request.form.get('csv_data')
    if not csv_data:
        flash('No CSV data to download')
        return redirect(url_for('index'))

    return send_file(io.BytesIO(csv_data.encode('utf-8')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='stock_data.csv')


if __name__ == '__main__':
    app.run(debug=True)
