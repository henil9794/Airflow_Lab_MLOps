# Import necessary libraries and modules
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
import os
import shutil
from src.main import load_data, data_preprocessing, train_model

# Default arguments
default_args = {
    'owner': 'Henil Patel',
    'start_date': datetime(2026, 1, 15),
    'retries': 2,  # Number of retries in case of task failure
    'retry_delay': timedelta(minutes=5),  # Delay before retries
}

def check_churn_model_quality(**kwargs):
    """Decision gate based on accuracy from the training task."""
    accuracy = kwargs['ti'].xcom_pull(task_ids='train_churn_model_task')
    # For churn prediction, set threshold to 78%, if accuracy of model is greater than threshold then it will be saved
    if accuracy >= 0.78:
        return 'save_model_task'
    return 'low_accuracy_alert_task'

def save_model():
    """Moves the verified churn model to the save file path."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    src = os.path.join(base_dir, "model/temp_model.sav")
    dst = os.path.join(base_dir, "model/model.sav")
    if os.path.exists(src):
        shutil.move(src, dst)

# DAG
with DAG(
    'Customer_Churn_Prediction_Pipeline',
    default_args=default_args,
    description='Pipeline to predict customer churn using Telco dataset',
    catchup=False,
    schedule_interval=None,
) as dag:

    # Task to load data
    load_data_task = PythonOperator(
        task_id='load_data_task',
        python_callable=load_data,
    )

    # Task to perform data preprocessing
    data_preprocessing_task = PythonOperator(
        task_id='data_preprocessing_task',
        python_callable=data_preprocessing,
        op_args=[load_data_task.output],
    )

    # Task to train model
    train_churn_model_task = PythonOperator(
        task_id='train_churn_model_task',
        python_callable=train_model,
        op_args=[data_preprocessing_task.output],
    )

    # Task to evaluate model performance
    evaluate_model_performance_task = BranchPythonOperator(
        task_id='evaluate_model_performance_task',
        python_callable=check_churn_model_quality,
        provide_context=True,
    )

    # Task to save model if accuracy is sufficient
    save_model_task = PythonOperator(
        task_id='save_model_task',
        python_callable=save_model,
    )

    # Task if accuracy is too low
    low_accuracy_alert_task = EmptyOperator(
        task_id='low_accuracy_alert_task',
    )

    # Set task dependencies
    load_data_task >> data_preprocessing_task >> train_churn_model_task >> evaluate_model_performance_task >> [save_model_task, low_accuracy_alert_task]

# If this script is run directly, allow command-line interaction with the DAG
if __name__ == "__main__":
    dag.test()