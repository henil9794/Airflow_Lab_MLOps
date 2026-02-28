# 📊 Customer Churn Prediction Pipeline (Airflow & MLOps)

---

## 📌 Project Overview

This project implements a containerized end-to-end Machine Learning pipeline using **Apache Airflow**. The goal is to predict customer churn using the **Telco Customer Churn** dataset. Unlike a standard script, this pipeline includes a **Quality Gate**: it only saves model if accuracy meets a specific threshold (**≥ 78%**).

---

## 🏗️ System Architecture

The project is decoupled into three main layers:

| Layer | Technology | Responsibility |
|---|---|---|
| **Orchestration** | Apache Airflow | Task sequencing, branching logic, and retries |
| **Logic** | Python / Scikit-Learn | Data loading, preprocessing, and model training |
| **Infrastructure** | Docker | Reproducible environment across any machine |

---

## 🚀 Pipeline Tasks

The DAG (`Customer_Churn_Prediction_Pipeline`) consists of the following steps:

1. **`load_data_task`**
   - Reads the raw CSV and passes it downstream via XCom.

2. **`data_preprocessing_task`**
   - Cleans `TotalCharges` column.
   - Encodes categorical variables.
   - Scales features using `StandardScaler`.

3. **`train_churn_model_task`**
   - Trains a **Random Forest Classifier** and calculates accuracy on a 20% test set.

4. **`evaluate_model_performance_task`** *(BranchPythonOperator)*
   - Acts as the **Quality Gate**:
     - ✅ Accuracy **≥ 78%** → proceeds to `save_model_task`
     - ❌ Accuracy **< 78%** → proceeds to `low_accuracy_alert_task`

5. **`save_model_task`**
   - Overwrites the production `model.sav` with the newly trained version.

6. **`low_accuracy_alert_task`** *(EmptyOperator)*
   - Safely stops the pipeline if the quality threshold is not met.

---

## 📁 File Structure

```
Airflow_Lab/
├── dags/
│   └── airflow.py           # DAG definition & branching logic
├── src/
│   └── lab.py               # ML Logic (Preprocessing & Training)
├── data/
│   └── telco_customer_churn_dataset.csv
├── model/
│   ├── temp_model.sav       # Intermediate model storage
│   └── model.sav            # Final production model
└── docker-compose.yaml      # Docker configuration
```

---

## 🛠️ Setup and Execution

### Prerequisites

- **Docker Desktop** installed and running.
- The **Telco dataset** placed in the `data/` folder.

### Running the Pipeline

**1. Start the containers:**
```bash
docker-compose up -d
```

**2. Access the Airflow UI:**

Open [http://localhost:8080](http://localhost:8080) in your browser.
> Default credentials — Login: `airflow` / Password: `airflow`

**3. Trigger the DAG:**

Locate `Customer_Churn_Prediction_Pipeline`, unpause it, and click **Trigger DAG**.

**4. Check Results:**

- ✅ If the model passes the quality gate, `model/model.sav` will be updated.
- 📋 Check the **`train_churn_model_task` → XCom tab** to inspect the exact accuracy score.