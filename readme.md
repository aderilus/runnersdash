# Runner's Dash

!['Screenshot'](screenshots/2022-03-20_screenshot.gif)

## Implemented visualizations
1. Time series graphs across a year, binned weekly and monthly.
    - Total Distance
    - Total Duration
    - Avg. Pace
    - Avg. Resting Heart Rate
    - Avg. VO2Max (if available)
    - Avg. Weight (labeled as 'BodyMass')
1. Total distance run per day across one week.
1. Calendar heatmap of running across all available years, where x = Months, y = Days, and z = ['Total Distance', 'Avg. Pace'].
1. Histograms (number of runs across a year/years) and a line plot of their associated avg. distance per run.
    - Day of the Week
    - Hour of day of run start time
    - Total run distance

## What it does
1. Extracts health data from exported Apple Health (XML) raw data and stores them on a local database.
2. Uses Dash framework to create a web-based dashboard visualizing running metrics.

## Installation
Clone this repository under your chosen directory
```
git clone https://github.com/nadinetab/runnersdash.git
```

## How to use

### 1. Extracting Apple Health data
Related file(s): `extractapplehealth.py`
1. Under the Health app settings (click on your profile picture), there will be a link to 'Export All Health Data'. This will download the file `export.zip` to your device. 
1. Move this file to the same directory you cloned this repository to and open it to extract. This will create a new folder called `apple_health_export` where all your health data resides.
1. To run `extractapplehealth.py`:

    a. If `export.zip` has been extracted within the `runnersdash/` directory: in the terminal, run
    ```
    python extractapplehealth.py
    ```

    b. Or if `export.zip` has been extracted somewhere else, run
    ```
    python extractapplehealth.py -o /path/to/export.xml
    ```

### 2. Prepare datasets for dashboard
Related file(s): `preparedatasets.py`, which reads relevant running metrics from the database file (the output from step 1) and outputs daily, weekly, and monthly aggregates of those metrics, stored as CSV files.

```
python preparedatasets.py data/{export_date}_applehealth.db
```

where `export_date` is the ExportDate of the export.xml file formatted as "YYYYmmdd".

Note: `extractapplehealth.py` stores output database file in the `data/` subdirectory of `runnersdash/`.

### 3. Launch dashboard
Related file(s): `app.py`

```
python app.py
```

<!--- 
TO-DO: 
- Add list of available visualizations?
--->