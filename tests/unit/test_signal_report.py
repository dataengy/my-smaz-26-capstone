import pandas as pd
from capstone.cli import latest_signal_report


def test_latest_signals_identify_frozen_training_cutoff():
    predictions = pd.DataFrame([
        {'split': 'test', 'date': '2024-06-01', 'ticker': 'GLD', 'prediction': 0.1},
        {'split': 'latest', 'date': '2025-01-02', 'ticker': 'SLV', 'prediction': 0.01},
    ])
    result = latest_signal_report(predictions, threshold=0.02, training_last_exit='2024-01-05')
    assert result.ticker.tolist() == ['SLV']
    assert result.signal.tolist() == [False]
    assert result.model_training_last_exit.tolist() == ['2024-01-05']
