import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle
import os
import base64

def load_data():
    print("Loading data")
    path = os.path.join(os.path.dirname(__file__), "../data/telco_customer_churn_dataset.csv")
    df = pd.read_csv(path)
    
    serialized_data = pickle.dumps(df)
    return base64.b64encode(serialized_data).decode("ascii")

def data_preprocessing(data_b64: str):
    """
    Deserializes base64-encoded pickled data, performs churn-specific preprocessing,
    and returns base64-encoded pickled preprocessed features.
    """
    print("Performing data preprocessing")
    # decode -> bytes -> DataFrame
    data_bytes = base64.b64decode(data_b64)
    df = pickle.loads(data_bytes)

    # Drop irrelevant ID column
    if 'customerID' in df.columns:
        df = df.drop(columns=['customerID'])
    
    # Fix TotalCharges (handle conversion from object to numeric)
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
    df['TotalCharges'] = df['TotalCharges'].fillna(0)
    
    # Encode categorical features and the target 'Churn'
    le = LabelEncoder()
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        df[col] = le.fit_transform(df[col])
    
    X = df.drop(columns=['Churn'])
    y = df['Churn']
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # bytes -> base64 string for XCom
    processed_serialized_data = pickle.dumps((X_scaled, y))
    return base64.b64encode(processed_serialized_data).decode("ascii")

def train_model(data_b64: str):
    """
    Builds a Random Forest model on the preprocessed churn data and saves it.
    Returns the accuracy score.
    """
    print("Training the model")
    # decode -> bytes -> tuple (X, y)
    data_bytes = base64.b64decode(data_b64)
    X, y = pickle.loads(data_bytes)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    accuracy = model.score(X_test, y_test)
    print(f"Model trained")
    print("Accuracy: {accuracy}")

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the model file
    output_path = os.path.join(output_dir, "temp_model.sav")
    with open(output_path, "wb") as f:
        pickle.dump(model, f)
    
    return float(accuracy)