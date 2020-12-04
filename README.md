# Reconciliation APIs

This holds Reconciliation API implementations (compliant to
https://reconciliation-api.github.io/specs/0.1/) for use with OpenRefine and
other software supporting the reconciliation API standard.

## How to Install Reconciliation Server

You will only need to set this up once before you can use the Reconciliatio nserver

1. Make sure you have an [OpenRefine](https://openrefine.org/) server running
2. Make sure you have Python 3 (at least version 3.6) installed
3. Set up virtual environment and install dependencies for the reconciliation server:
    1. Navigate to the `reconciliation-apis` directory in your terminal
    2. Run `python3 -m venv venv` (creates virtual environment) (only need to do this once)
    3. Run `source venv/bin/activate` (activates virtual environment)
    4. Run `pip install -r requirements.txt` (installs dependencies) (only need to do this once)
4. Run the server: `python3 app.py`:
    - If you need to stop/restart the server, remember to activate the virtual environment before running this command
5. From the OpenRefine web interface ([link here](http://localhost:3333)), open up a CSV file as you would normally, and use the drop down menu for any column to select "Reconcile" and then "Start Reconciling"
    ![Selecting the "Start Reconciling" button](../img/reconcile1.png)
6. This should have opened a new modal window. Select "Add Standard Service" in the lower left corner of this window and enter `http://localhost:5000/reconcile` into the text box. This address is produced by the default address of the reconciliation server (open `app.py` to change the port) followed by the `/reconcile` path, which is the endpoint that supports the reconciliation API. This should now appear as the "Brick Reconciliation Service" in the modal.
7. Use the "Brick Reconciliation Service" as suggested in the [YouTube tutorial](https://www.youtube.com/watch?v=LKcXMvrxXzE)
