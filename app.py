import datetime as dt
import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify
"""LOGGING"""
#from logging import FileHandler, WARNING

# Default sqlalchemy does not allow same thread, set parameters
# https://docs.python.org/3/library/sqlite3.html#sqlite3.connect
engine = create_engine("sqlite:///Resources/hawaii.sqlite", connect_args={'check_same_thread': False}, echo=True)
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session
session = Session(engine)

# Flask 
app = Flask(__name__)

"""LOGGING"""
#file_handler = FileHandler('errorlog.txt')
#file_handler.setLevel(WARNING)
# add logger to app
#app.logger.addHandler(file_handler)

@app.route("/")
def welcome():
    return (
        f"Welcome to the Hawaii Climate Analysis API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/temp/start/end"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the precipitation data for the last year
        OR return precipitation data"""
    # Check for latest date in database
    max_date_str = session.query(func.max(Measurement.date)).all()[0][0]
    max_date = dt.datetime.strptime(max_date_str, '%Y-%m-%d').date() 

    # For databases with updated data
    if ((dt.date.today().month == max_date.month) & (dt.date.today().day > max_date.day)) | (dt.date.today().month > max_date.month):
        # Use data from one year ago
        one_year_ago = (max_date - dt.timedelta(days=365)).year
        prev_year = dt.date(one_year_ago, dt.date.today().month, dt.date.today().day)
    else:
        # Use current data
        prev_year = dt.date(max_date.year, dt.date.today().month, dt.date.today().day)

    # Query for the date and precipitation for the last year
    precipitation = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= prev_year).all()

    # Dict with date as the key and prcp as the value
    precip = {date: prcp for date, prcp in precipitation}
    return jsonify(precip)


@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations."""
    results = session.query(Station.station).all()

    # Unravel results into a 1D array and convert to a list
    stations = list(np.ravel(results))
    return jsonify(stations)


@app.route("/api/v1.0/tobs")
def temp_monthly():
    """Return the temperature observations (tobs) for previous year."""
    max_date_str = session.query(func.max(Measurement.date)).all()[0][0]
    max_date = dt.datetime.strptime(max_date_str, '%Y-%m-%d').date() 
    if ((dt.date.today().month == max_date.month) & (dt.date.today().day > max_date.day)) | (dt.date.today().month > max_date.month):
        one_year_ago = (max_date - dt.timedelta(days=365)).year
        prev_year = dt.date(one_year_ago, dt.date.today().month, dt.date.today().day)
    else:
        prev_year = dt.date(max_date.year, dt.date.today().month, dt.date.today().day)


    # Query the primary station for all tobs from the last year
    results = session.query(Measurement.tobs).\
        filter(Measurement.station == 'USC00519281').\
        filter(Measurement.date >= prev_year).all()

    # Unravel results into a 1D array and convert to a list
    temps = list(np.ravel(results))

    # Return the results
    return jsonify(temps)


@app.route("/api/v1.0/temp/<start>")
@app.route("/api/v1.0/temp/<start>/<end>")
def stats(start=None, end=None):
    """Return TMIN, TAVG, TMAX."""

    # Select statement
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

    if not end:
        # calculate TMIN, TAVG, TMAX for dates greater than start
        results = session.query(*sel).\
            filter(Measurement.date >= start).all()
        # Unravel results into a 1D array and convert to a list
        temps = list(np.ravel(results))
        return jsonify(temps)

    # calculate TMIN, TAVG, TMAX with start and stop
    results = session.query(*sel).\
        filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()
    # Unravel results into a 1D array and convert to a list
    temps = list(np.ravel(results))
    return jsonify(temps)


if __name__ == '__main__':
    app.run()
