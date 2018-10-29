from flask import Flask, render_template, request
from wtforms import Form, TextAreaField, validators
import sqlite3
from flask import g
import pandas as pd
import pickle
import os
import numpy as np
from sklearn.ensemble import RandomForestRegressor

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/prediction', methods=['POST'])

def prediction():
	if request.method == 'POST':
		issue = request.form['issuenumber']
		conn = sqlite3.connect('issues.sqlite')
		def predictSingleIssue_fromDB(key):
			regressor_unpickled = pickle.load(open(os.path.join('issueclassifier','pkl_objects','final_model.pkl'),'rb'))
			row = pd.read_sql("select * from issues_db where key = '{0}'".format(key), conn)
			df = pd.read_sql("select * from issues_db where key = '{0}'".format(key), conn)
			X = row.drop(['days_existing','created+existing','resolutiondate','key','days_in_from_status_Log','just_date'], axis=1)
			prediction = regressor_unpickled.predict(X)
    			# convert to real value
			real_value = np.expm1(prediction)
			real_pred = real_value[0]
			days = pd.Timedelta(real_pred, unit='D')
			# Convert just_date to datetime
			df['created+existing'] = pd.to_datetime(df['created+existing'])
			predicted_resolutiondate = df[df['key'] == key]['created+existing'] + days
    
   	 		# Convert datetime64 to string and print only year-month-day
			return predicted_resolutiondate.values[0]	
		
		result = predictSingleIssue_fromDB(issue)
		return render_template('prediction.html', result = result)
	return render_template('index.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)