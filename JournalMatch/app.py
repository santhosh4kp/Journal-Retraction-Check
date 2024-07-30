import pandas as pd
from flask import Flask, request, render_template, send_file, make_response
import os

app = Flask(__name__)

# Function to read CSV file from URL
def read_csv_from_url(url):
    try:
        return pd.read_csv(url, sep=',', low_memory=False, encoding='latin1')
    except Exception as e:
        print(f"Error reading CSV from URL: {e}")
        return None

url = 'https://api.labs.crossref.org/data/retractionwatch?name@email.org'
large_df = read_csv_from_url(url)

if large_df is not None:
    default_value = 'null'
    large_df.fillna(value=default_value, inplace=True)
else:
    print("Failed to load the large CSV file from the URL.")

@app.route('/', methods=['GET'])
def upload_file():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file"

    if file and file.filename.endswith('.csv'):
        user_df = pd.read_csv(file)

        # Check which columns are present in the user uploaded CSV
        has_title = 'Title' in user_df.columns
        has_doi = 'DOI' in user_df.columns

        if not has_title and not has_doi:
            return "CSV must contain at least 'Title' or 'DOI' column"

        matched_records = []

        # Compare and find matching records
        if large_df is not None:
            for _, user_row in user_df.iterrows():
                matched = None
                if has_doi and pd.notna(user_row['DOI']):
                    matched = large_df[large_df['RetractionDOI'] == user_row['DOI']]
                elif has_title and pd.notna(user_row['Title']):
                    matched = large_df[large_df['Title'] == user_row['Title']]
                
                if matched is not None and not matched.empty:
                    matched_records.append(matched.iloc[0].to_dict())

            matched_df = pd.DataFrame(matched_records)

            # Save the matched records to a CSV file
            output_csv_path = 'matched_records.csv'
            matched_df.to_csv(output_csv_path, index=False)

            response = make_response(send_file(output_csv_path, as_attachment=True, mimetype='text/csv'))
            response.headers["Content-Disposition"] = "attachment; filename=matched_records.csv"
            return response
        else:
            return "Failed to load the large CSV file from the URL."

if __name__ == '__main__':
    app.run(debug=True)
