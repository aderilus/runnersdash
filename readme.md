!['Screenshot'](screenshots/2022-05-14_screenshot.gif)

# Runner's Dash

- [Goals](#project-goals)
- [Implemented visualizations](#implemented-visualizations)
- [Installation](#installation)
- [Usage](#usage)
    - [1. Extraction](#1-extract-store-and-clean-apple-health-data)
        - [More details](#in-detail-usage-of-exporthealthdatapy)
    - [2. Dashboard](#2-launch-dashboard)
- [A note on data privacy](#a-note-regarding-data-privacy)

## Project goals
- Create an interactive dashboard to visualize running data alongside other health metrics, and be able to do some exploratory data analysis with personal health data.
    - Extract health data from exported Apple Health (XML) file and store them on a local database.
    - Use Plotly Dash to generate a dashboard.

## Implemented visualizations
1. Time series plots across one year, binned weekly and monthly.
```
    - Total Distance (sum)
    - Total Duration (sum)
    - Total Energy Burned (mean)
    - Total Elevation Ascended (mean)
    - Avg. Pace
    - Avg. VO2Max (if available)
    - Avg. Weight (labeled as 'BodyMass')
    - Avg. METs
    - Avg. Resting Heart Rate
    - Avg. Heart Rate Variability SDNN
    - Avg. Respiratory Rate
    - Avg. Blood Pressure Diastolic
    - Avg. Blood Pressure Systolic
    - Avg. Menstrual Flow
```
2. Total distance run per day across one week.
3. Histograms (number of runs across a year/years) and a line plot of their associated avg. distance per run.
```
    - Day of the Week
    - Hour of run start time
    - Total run distance
    - Daily total distance, duration, avg METs
```
4. Various running/health metrics against temperature and humidity (for days with outdoor runs).


## Installation
1. Clone this repository under your chosen directory
```
git clone https://github.com/nadinetab/runnersdash.git
```

2. Navigate to the project directory and install dependencies
```
pip install -r requirements.txt
```

## Usage

### 1. Extract, store, and clean Apple Health data
Relevant file(s): `exporthealthdata.py`

1. Under the Health app settings (click on your profile picture), there will be a link to 'Export All Health Data'. This will download the file `export.zip` to your device. 
1. Move this file to the same directory you cloned this repository to and open it to extract. This will create a new folder called `apple_health_export` where all your health data reside.
1. To run `exporthealthdata.py`:

    - If you want to extract all entries within export.xml:
        ```
            $ python exporthealthdata.py
        ```

    - If you already have a database (.db) file of a previous export and just need to add new entries since the last export:
        ```
            $ python exporthealthdata.py --append
        ```
        assuming there is an existing db file within the `data/` subdirectory.


#### **In detail, usage of exporthealthdata.py**: 


    ```
    python exporthealthdata.py [-o --open-file </path/to/export.xml>]
                                 [-a --append] [-v --version]
                                 [-w --workouts] [-r --records]

    OPTIONAL ARGUMENTS:

    -o --open-export </path/to/export.xml> : 
        Determine export.xml file to read.

    -a --append (bool) : 
        If passed in, script will find the latest version of a db file within the 'data/' subdirectory and append to the database any data with 'startDate' >= latest export date of the .db file. For use if you have previous exports already stored in a database and just need to add new data entries since your last export.
        Default is --no-append.

    -v --version (bool) : 
        If true, the version number of extractapplehealth.py is appended to the name of the resulting database .db file.
        Default is --no-version.

    -w --workouts <list of Workout names> : 
        List (space-separated) of table names (as it appears) in the database file of type Workout to process.

        Default: Running

        Note: Tables that are not listed in the default list have not yet been implemented within the data processing routines.

        Example Workout tables:
            - Running
            - Barre
            - Flexibility
            - Walking
            - Other
            - Skiing

    -r --records <list of Record names> :
        List (space-separated) of table names of type Record to process.

        Default: 
            MenstrualFlow RestingHeartRate VO2Max BodyMass HeartRateVariabilitySDNN StepCount RespiratoryRate BloodPressureDiastolic BloodPressureSystolic

        Note: Tables that are not listed in the default list have not yet been implemented within the data processing routines.

        Example Record tables:
            - HeartRateVariabilitySDNN
            - VO2Max
            - StepCount
    ```
    
#### Outputs:
This step will produce the following things within `data/` subdirectory:
1. A database (.db file) containing data from export.xml organized and stored into tables.
2. A set of five CSV files, containing daily/weekly/monthly aggregates as well as resampled running data, *given default arguments for `--workouts` and `--records` parameters.*

### 2. Launch dashboard
Related file(s): `app.py`

Launch the Dash app with the following:
```
python app.py
```

## A note regarding data privacy

All health data is stored locally (and remains local).


<!--- 
TO-DO:
1. To be implemented/roadmap section
--->
