# Runner's Dash

## What it does
1. Extracts health data from exported Apple Health (XML) raw data and stores them on a local database.
2. Uses Dash framework to create a web-based dashboard visualizing running and other health metrics.

## How to use

### Installation
Clone this repository under your chosen directory
> git clone https://github.com/nadinetab/runnersdash.git

### Extracting Apple Health data
1. Under the Health app settings (click on your profile picture), there will be a link to 'Export All Health Data'. This will download the file `export.zip` to your device. 
2. Move this file to the same directory you cloned this repository to and open it to extract. This will create a new folder called `apple_health_export` where all your health data resides.
3. To run `extractapplehealth.py`:

    a. This assumes that `export.zip` has been extracted in the same directory. In the terminal, change to the local runnersdash directory and run
    > $ python extractapplehealth.py

    b. Assuming the contents of `export.zip` have been extracted somewhere else, in the local directory, run
    > $ python extractapplehealth.py /path/to/export.xml

<!--- TO-DO: Add a list of dependencies --->