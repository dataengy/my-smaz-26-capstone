"""Fictional records checking conservative public-row availability policy."""
import pandas as pd
import pytest

from capstone.cot_publication_audit import CODES, FIELDS, validate_rows


def paired_rows():
    api, archive = [], []
    for code, ticker in CODES.items():
        api.append({'cftc_contract_market_code': code, 'report_date_as_yyyy_mm_dd': '2024-01-02',
                    ':created_at': '2024-01-05T20:30:15Z', ':updated_at': '2024-01-05T20:30:15Z',
                    **{key: '100' for key in FIELDS}})
        archive.append({'ticker': ticker, 'report_date': '2024-01-02',
                        **{key: 100 for key in FIELDS.values()}})
    return api, pd.DataFrame(archive)


def test_paired_unchanged_matching_records_wait_until_next_day():
    api, archive = paired_rows()
    api[1][':created_at'] = api[1][':updated_at'] = '2024-01-06T01:00:00Z'
    manifest, _ = validate_rows(api, archive)
    assert len(manifest) == 1
    assert manifest.available_at.iloc[0] == '2024-01-07T05:00:00+00:00'


@pytest.mark.parametrize('defect', ['modified', 'mismatch', 'prelaunch', 'before_observation', 'missing_pair'])
def test_unproven_or_mismatched_rows_do_not_establish_publication(defect):
    api, archive = paired_rows()
    if defect == 'modified':
        api[0][':updated_at'] = '2024-01-07T20:30:00Z'
    elif defect == 'mismatch':
        api[0]['open_interest_all'] = '101'
    elif defect == 'prelaunch':
        for row in api:
            row['report_date_as_yyyy_mm_dd'] = '2022-01-04'
            row[':created_at'] = row[':updated_at'] = '2022-08-01T20:30:00Z'
        archive['report_date'] = '2022-01-04'
    elif defect == 'before_observation':
        api[0][':created_at'] = api[0][':updated_at'] = '2024-01-01T20:30:00Z'
    else:
        api.pop()
    manifest, _ = validate_rows(api, archive)
    assert manifest.empty


def test_duplicate_contract_rows_fail():
    api, archive = paired_rows()
    with pytest.raises(ValueError, match='Duplicate'):
        validate_rows(api + [api[0]], archive)
