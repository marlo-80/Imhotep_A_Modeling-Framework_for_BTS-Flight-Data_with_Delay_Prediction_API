import pytest
import pandas as pd
from src.preprocessing import build_preprocessor
from sklearn.pipeline import Pipeline

def test_preprocessor_handles_unknown_categories():
    # Simulate training data with known airports
    train_df = pd.DataFrame({
        'origin': ['JFK', 'LAX', 'ORD'],
        'dep_delay': [5, 10, 0]
    })
    preprocessor = build_preprocessor(
        numeric_cols=['dep_delay'],
        categorical_cols=['origin'],
        impute_num='median',
        impute_cat='most_frequent'
    )
    preprocessor.fit(train_df)
    
    # Test with unseen category 'XYZ'
    test_df = pd.DataFrame({'origin': ['XYZ'], 'dep_delay': [2]})
    transformed = preprocessor.transform(test_df)
    # Should not raise error, and output shape should be (1, n_features)
    assert transformed.shape[0] == 1