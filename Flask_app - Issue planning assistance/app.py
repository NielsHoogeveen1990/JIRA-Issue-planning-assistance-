from flask import Flask, render_template, request, send_from_directory
from flask import jsonify
import json
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
		timespan = request.form['timespan']
		nowdate = request.form['nowdate']
		conn = sqlite3.connect('issues.sqlite')
		def planningAssistance(datenow, days_timespan):
			regressor_unpickled = pickle.load(open(os.path.join('issueclassifier','pkl_objects','final_model.pkl'),'rb'))
			# convert strin to int
			days_timespan = int(days_timespan)
			
			now = pd.to_datetime(datenow)
			days = pd.Timedelta(days_timespan, unit='D')
			deadline = now + days
			
			# read dataframe from db	
			df = pd.read_sql("select * from issues_db", conn)
			# convert created+existing to date time
			df['created+existing'] = pd.to_datetime(df['created+existing'])
			df['just_date'] = pd.to_datetime(df['just_date'])

			X = df.drop(['days_existing','created+existing','resolutiondate','key','days_in_from_status_Log','just_date'], axis=1)
			
			# create new column with predicted resolution date
			predictions = regressor_unpickled.predict(X)
    			# convert to real value
			real_pred = np.expm1(predictions)
			
			# make dataframe of predictions Series
			real_pred = pd.DataFrame(real_pred)
			real_pred = pd.to_timedelta(pd.Series(real_pred[0].values),unit='D')
			real_pred = pd.DataFrame(real_pred,columns=['days_predicted'])
			
			# merge with df
			df = pd.merge(df, real_pred, left_index=True, right_index=True)
			df['predicted_resolutiondate'] = df['created+existing'] + df['days_predicted']
			df['predicted_resolutiondate'] = pd.to_datetime(df['predicted_resolutiondate'])
			
			# filter df where predicted resolution date is equal or greater than now but less than deadline
			mask = (df['predicted_resolutiondate'] >= now) & (df['predicted_resolutiondate'] < deadline)
			df = df.loc[mask]
						
			df = df[['key','predicted_resolutiondate']]
			df.rename(columns={'predicted_resolutiondate':'resolution date'}, inplace=True)
			
			df = df.sort_values(by=['resolution date'])	
							
			#json_df = json.dumps(json.loads(df.to_json(orient='index')), indent=2)
			
			return df
		
		result = planningAssistance(nowdate,timespan)
		return render_template('prediction.html', result = result.to_html())
	return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True,port=80)