# Customer Churn Prediction Pipeline (Airflow)

---

## Project Overview

This project implements a containerized end-to-end Machine Learning pipeline using **Apache Airflow**. The goal is to predict customer churn using the **Telco Customer Churn** dataset. This pipeline includes a **Quality Gate**: it only saves model if accuracy meets a specific threshold (**≥ 78%**).

ML Model:

This script is designed for Supervised Learning to predict customer churn. It utilizes a Random Forest Classifier to determine the likelihood of a customer leaving based on the Telco Customer Churn dataset. It provides functionality to load data, perform preprocessing, train a model, and evaluate performance.

---

## System Architecture

The project is decoupled into three main layers:

| Layer | Technology | Responsibility |
|---|---|---|
| **Orchestration** | Apache Airflow | Task sequencing, branching logic, and retries |
| **Logic** | Python / Scikit-Learn | Data loading, preprocessing, and model training |
| **Infrastructure** | Docker | Reproducible environment across any machine |

---

## Functions

load_data(): Loads the Telco dataset from the data/ folder, serializes it using pickle, and encodes it to base64 for safe transfer through Airflow XComs.

data_preprocessing(): Decodes the data, handles missing values in TotalCharges, encodes text categories into numbers using LabelEncoder, and scales features using StandardScaler.

train_model(): Splits data into training (80%) and testing (20%) sets. Trains a RandomForestClassifier. Saves a temp_model.sav file and returns the accuracy score as a float.

---

## Airflow Setup

Airflow Setup
Use Airflow to author workflows as directed acyclic graphs (DAGs). The Airflow scheduler executes your tasks on an array of workers while following the specified dependencies and branching logic.

References

-   Product - https://airflow.apache.org/
-   Documentation - https://airflow.apache.org/docs/
-   Github - https://github.com/apache/airflow

#### Installation

Prerequisites: You should allocate at least 4GB memory for the Docker Engine (ideally 8GB).

Local

-   Docker Desktop Running

Cloud

-   Linux VM
-   SSH Connection
-   Installed Docker Engine - [Install using the convenience script](https://docs.docker.com/engine/install/ubuntu/#install-using-the-convenience-script)

#### Tutorial

1. Create a new directory

    ```bash
    mkdir -p ~/airflow_lab
    cd ~/airflow_lab
    ```

2. Running Airflow in Docker - [Refer](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#running-airflow-in-docker)

    a. You can check if you have enough memory by running this command

    ```bash
    docker run --rm "debian:bullseye-slim" bash -c 'numfmt --to iec $(echo $(($(getconf _PHYS_PAGES) * $(getconf PAGE_SIZE))))'
    ```

    b. Fetch [docker-compose.yaml](https://airflow.apache.org/docs/apache-airflow/2.5.1/docker-compose.yaml)

    ```bash
    curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.5.1/docker-compose.yaml'
    ```

    c. Update the following in docker-compose.yml

    ```bash
    # Donot load examples
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'

    # Additional python package
    _PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:- pandas scikit-learn}

    # Output dir
    - ${AIRFLOW_PROJ_DIR:-.}/working_data:/opt/airflow/working_data

    # Change default admin credentials
    _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-test1}
    _AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-test1}
    ```

    e. Initialize the database

    ```bash
    docker compose up airflow-init
    ```

    f. Running Airflow

    ```bash
    docker compose up
    ```

    Wait until terminal outputs

    `app-airflow-webserver-1  | 127.0.0.1 - - [17/Feb/2023:09:34:29 +0000] "GET /health HTTP/1.1" 200 141 "-" "curl/7.74.0"`

    g. Enable port forwarding

    h. Visit `localhost:8080` login with credentials set on step `2.d`

3. Explore UI and add user `Security > List Users`

4. You can check accuracy score in XCom tab. 

5. Stop docker containers

    ```bash
    docker compose down
    ```

## Pipeline Tasks

The DAG (`Customer_Churn_Prediction_Pipeline`) consists of the following steps:

1. **`load_data_task`**
   - Reads the raw CSV and passes it downstream via XCom.

2. **`data_preprocessing_task`**
   - Cleans `TotalCharges` column.
   - Encodes categorical variables.
   - Scales features using `StandardScaler`.

3. **`train_churn_model_task`**
   - Trains a **Random Forest Classifier** and calculates accuracy on a 20% test set.

4. **`evaluate_model_performance_task`**
   - Acts as the **Quality Gate**:
     - Accuracy **≥ 78%** → proceeds to `save_model_task`
     - Accuracy **< 78%** → proceeds to `low_accuracy_alert_task`

5. **`save_model_task`**
   - Overwrites the production `model.sav` with the newly trained version.

6. **`low_accuracy_alert_task`**
   - Safely stops the pipeline if the quality threshold is not met.

---

## File Structure

```
Airflow_Lab/
├── dags/
│   └── airflow.py           # DAG definition & branching logic
├── src/
│   └── main.py               # ML Logic (Preprocessing & Training)
├── data/
│   └── telco_customer_churn_dataset.csv
├── README.md
|── requirements.txt
```

---

# Airflow DAG Script

This section explains the logic in `dags/airflow.py`, which manages the **MLOps lifecycle**.

## Script Overview

The DAG defines a workflow that includes a **Quality Gate**. If the model does not reach a **78% accuracy threshold**, it will not be moved to the production file path.

## Logic Highlights

### Importing Logic

The DAG imports all ML functions directly from the logic layer:

```python
from src.main import load_data, data_preprocessing, train_model
```

### Branching Function

The `check_churn_model_quality` function pulls the accuracy score from **XCom**. If the score is **≥ 0.78**, it returns the ID for the save task; otherwise, it triggers an alert task.

### Task Dependencies

```python
load_data_task >> data_preprocessing_task >> train_churn_model_task >> evaluate_model_performance_task >> [save_model_task, low_accuracy_alert_task]
```

> Tasks run **sequentially** until `evaluate_model_performance_task`, where the pipeline **branches** based on model quality.

---

### Running the Pipeline in Docker

This section provides step-by-step instructions to run the `Customer_Churn_Prediction_Pipeline` DAG inside Docker using Docker Compose.

#### Prerequisites

- Docker Desktop installed and running on your system.
- The Telco dataset placed in the `data/` folder before starting.

#### Step 1: Directory Structure

Ensure your project has the following directory structure:

```plaintext
Airflow_Lab/
├── dags/
│   └── airflow.py                        # DAG definition & branching logic
├── src/
│   └── main.py                            # ML logic (preprocessing & training)
├── data/
│   └── telco_customer_churn_dataset.csv
├── model/
│   ├── temp_model.sav                    # Intermediate model storage
│   └── model.sav                         # Final production model
└── docker-compose.yaml                   # Docker configuration
└── README.md
└── requirements.txt
```

#### Step 2: Docker Compose Configuration

Create or verify your `docker-compose.yaml` file in the project root. Ensure the `data/` and `model/` directories are mounted as volumes so Airflow containers can read and write to them.

#### Step 3: Start the Docker Containers

```bash
docker compose up -d
```

Wait until you see the log message indicating the Airflow webserver is healthy:

`app-airflow-webserver-1 | 127.0.0.1 - - [17/Feb/2023:09:34:29 +0000] "GET /health HTTP/1.1" 200 141 "-" "curl/7.74.0"`

#### Step 4: Access the Airflow Web Interface

- Open a web browser and navigate to `http://localhost:8080`.
- Log in with the credentials defined in your `docker-compose.yaml`.
- Once logged in, you will land on the Airflow DAGs overview page.

#### Step 5: Trigger the DAG

- Locate `Customer_Churn_Prediction_Pipeline` in the DAGs list.
- Toggle the switch to **unpause** the DAG.
- Click the **▶ Trigger DAG** button to start a manual run.
- Monitor task progress in the **Graph View**. Each task will turn green upon successful completion as shown in figure below.

![Airflow Image](images\Airflow_DAG_Pipeline.png "Airflow")

#### Step 6: Verify Pipeline Outputs

Once the DAG run completes, verify the results as follows:

- If `save_model_task` is **green** — the model passed the quality gate and `model/model.sav` has been updated with the new version.
- If `low_accuracy_alert_task` is **green** — the model was rejected. The existing `model/model.sav` is preserved unchanged.
- Navigate to `train_churn_model_task > XCom tab` in the Airflow UI to inspect the exact accuracy score that was produced during training.