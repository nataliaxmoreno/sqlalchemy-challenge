import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta

# Database Setup
engine = create_engine("sqlite:///hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)

#  reference to the tables
measurement= Base.classes.measurement
station= Base.classes.station
# Flask Setup
#################################################
app = Flask(__name__)
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (f"Welcome to the Climate app for Hawaii!<br/>"
        f"These are your available Routes:<br/>"
        f"Precipitation for the past year of study: /api/v1.0/precipitation<br/>"
        f"List of Stations: /api/v1.0/stations<br/>"
        f"Temperature for one year for the most active station: /api/v1.0/tobs<br/>"
        f"Temperature stat from the start date(yyyy-mm-dd) until the last day of study: /api/v1.0/yyyy-mm-dd<br/>"
        f"Temperature stat from start to end dates(yyyy-mm-dd)(keep in mind the study goes till 2017-06-23): /api/v1.0/yyyy-mm-dd/yyyy-mm-dd")

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)

    mostrecentdate=dt.datetime.strptime((session.query(measurement.date).order_by(measurement.date.desc()).\
                                     first())[0],'%Y-%m-%d').date()
    oneyearago=session.query(measurement.date,measurement.prcp).\
filter(measurement.date >=(mostrecentdate-dt.timedelta(days=365))).all()
   
    session.close()

    precip= []
    for date,prcp  in oneyearago:
        prcp_dict = {}
        prcp_dict["date"] = date
        prcp_dict["prcp"] = prcp    
        precip.append(prcp_dict)
    return jsonify(precip)

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    all_stations = session.query(measurement.station).\
        group_by(measurement.station).all()
    session.close()
    list_of_stations = list(np.ravel(all_stations)) 
    return jsonify(list_of_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    mostrecentdate=dt.datetime.strptime((session.query(measurement.date).order_by(measurement.date.desc()).\
                                     first())[0],'%Y-%m-%d').date()
    oneyearago=session.query(measurement.date,measurement.prcp).\
filter(measurement.date >=(mostrecentdate-dt.timedelta(days=365))).all()    
    active_station=session.query(measurement.station,func.count(measurement.id)).\
group_by(measurement.station).order_by(func.count(measurement.id).desc()).all()
    mostactive_lastyear=session.query(measurement.date,measurement.tobs).\
filter(measurement.date >=(mostrecentdate-dt.timedelta(days=365))).\
filter(measurement.station==active_station[0][0]).all()
    session.close()

    all_tobs = []
    for date,tobs in mostactive_lastyear:
        tobs_dict = {}
        tobs_dict["date"] = date
        tobs_dict["tobs"] = tobs
        all_tobs.append(tobs_dict)

    return jsonify(all_tobs)

@app.route("/api/v1.0/<start_date>")
def Start_date(start_date):
    session = Session(engine)

    vacay_list= pd.date_range(start_date,'2017-08-23').strftime("%Y-%m-%d").tolist()

    start_date_tobs = []
    for date in vacay_list:
        mostactive= session.query(measurement.date,func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
            filter(measurement.date == date).all()
         
        for date, min, avg, max  in mostactive:
            start_date_tobs_dict = {}
            start_date_tobs_dict["date"] = date
            start_date_tobs_dict["min_temp"] = min
            start_date_tobs_dict["temp_avg"] = avg
            start_date_tobs_dict["max_temp"] = max
            start_date_tobs.append(start_date_tobs_dict)

    session.close()

    if start_date_tobs_dict["min_temp"]: 
        return jsonify(start_date_tobs)
    else:
        return jsonify({"error": f"Date(s) not found, invalid date range or dates not formatted correctly."}), 404

@app.route("/api/v1.0/<start_date>/<end_date>")
def Start_end_date(start_date, end_date):
    session = Session(engine)

    vacay_list= pd.date_range(start_date, end_date).strftime("%Y-%m-%d").tolist()

    start_end_tobs = []
    for date in vacay_list:
        mostactive= session.query(measurement.date,func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
            filter(measurement.date == date).all()
         
        for date, min, avg, max  in mostactive:
            start_end_tobs_dict = {}
            start_end_tobs_dict["date"] = date
            start_end_tobs_dict["min_temp"] = min
            start_end_tobs_dict["temp_avg"] = avg
            start_end_tobs_dict["max_temp"] = max
            start_end_tobs.append(start_end_tobs_dict)

    session.close()
    
    if start_end_tobs_dict["min_temp"]: 
        return jsonify(start_end_tobs)
    else:
        return jsonify({"error": f"Date(s) not found, invalid date range or dates not formatted correctly."}), 404

    

if __name__ == "__main__":
    app.run(debug=True)
