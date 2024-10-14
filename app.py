# Import the dependencies.
import numpy as np
import pandas as pd
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
import datetime as dt


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")


# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station  

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
# Homepage route
@app.route("/")
def welcome():
    return (
        f"Welcome to the Hawaii Climate API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/2017-01-01<br/>"
        f"/api/v1.0/2017-01-01/2017-12-31<br/>"
    )

# Route for precipitation data (last 12 months)
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create session
    session = Session(engine)

    # Get the most recent date
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]

    # Calculate the date one year ago from the most recent date
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)

    # Query precipitation data for the last 12 months
    precipitation_data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_ago).all()

    session.close()

    # Convert query results into a dictionary {date: prcp}
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}

    return jsonify(precipitation_dict)

# Route for stations
@app.route("/api/v1.0/stations")
def stations():
    # Create session
    session = Session(engine)

    # Query all stations
    stations_data = session.query(Station.station).all()

    session.close()

    # Convert the list of tuples into a normal list
    stations_list = list(np.ravel(stations_data))

    return jsonify(stations_list)

# Route for temperature observations of the most active station (last 12 months)
@app.route("/api/v1.0/tobs")
def tobs():
    # Create session
    session = Session(engine)

    # Get the most recent date and the most active station
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)

    # Find the most active station
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()[0]

    # Query the temperature observations of the most active station for the last 12 months
    temperature_data = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == most_active_station).filter(Measurement.date >= one_year_ago).all()

    session.close()

    # Convert query results into a list
    tobs_list = list(np.ravel(temperature_data))

    return jsonify(tobs_list)

# Route for temperature statistics from a start date
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temp_stats(start=None, end=None):
    # Create session
    session = Session(engine)

    # Define the query for temperature statistics
    if not end:
        # Query when only start date is provided
        temp_data = session.query(func.min(Measurement.tobs), 
                                  func.avg(Measurement.tobs), 
                                  func.max(Measurement.tobs)).\
                                  filter(Measurement.date >= start).all()
    else:
        # Query when both start and end date are provided
        temp_data = session.query(func.min(Measurement.tobs), 
                                  func.avg(Measurement.tobs), 
                                  func.max(Measurement.tobs)).\
                                  filter(Measurement.date >= start).\
                                  filter(Measurement.date <= end).all()

    session.close()

    # Convert query results into a list [TMIN, TAVG, TMAX]
    temp_stats_list = list(np.ravel(temp_data))

    # Check if data exists for the provided date range
    if not temp_data or temp_stats_list == [None, None, None]:
        return jsonify({"error": "No temperature data available for the provided date range."}), 404


    # Return the results as a JSON response
    return jsonify({
        "start_date": start,
        "end_date": end if end else "latest",
        "TMIN": temp_stats_list[0],
        "TAVG": temp_stats_list[1],
        "TMAX": temp_stats_list[2]
    })

#################################################
# Run the app
#################################################
if __name__ == '__main__':
    app.run(debug=True)
