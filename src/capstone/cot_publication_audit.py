"""Validate post-launch public CFTC row timestamps against local position archives.

This constructs conservative API availability cutoffs, not original release times.
Bulk pre-launch imports and modified or mismatching records are excluded.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from .config import read_config
from .data import _read_snapshot, parse_cot_archive

API = 'https://publicreporting.cftc.gov/resource/72hh-3qpy.json'
LAUNCH = pd.Timestamp('2022-10-21T00:00:00Z')
FIELDS = {'open_interest_all': 'open_interest', 'm_money_positions_long_all': 'managed_long',
          'm_money_positions_short_all': 'managed_short', 'prod_merc_positions_long': 'producer_long',
          'prod_merc_positions_short': 'producer_short'}
CODES = {'088691': 'GLD', '084691': 'SLV'}


def validate_rows(rows, archive):
    """Use only paired, unchanged API rows exactly matching all modeled positions."""
    api = pd.DataFrame(rows)
    api['ticker'] = api.cftc_contract_market_code.map(CODES)
    if api.ticker.isna().any():
        raise ValueError('Unexpected contract in CFTC API response')
    api['report_date'] = pd.to_datetime(api.report_date_as_yyyy_mm_dd, utc=True).dt.tz_localize(None)
    for name in (':created_at', ':updated_at'):
        api[name] = pd.to_datetime(api[name], utc=True, errors='raise')
    if api.duplicated(['report_date', 'ticker']).any():
        raise ValueError('Duplicate API report/contract rows')
    archive = archive.copy()
    archive['report_date'] = pd.to_datetime(archive.report_date)
    joined = api.merge(archive, on=['report_date', 'ticker'], how='left', validate='one_to_one', indicator=True)
    valid = joined['_merge'].eq('both') & joined[':created_at'].ge(LAUNCH)
    valid &= joined.report_date.ge(LAUNCH.tz_localize(None))
    valid &= joined[':created_at'].eq(joined[':updated_at'])
    valid &= joined[':created_at'].gt(joined.report_date.dt.tz_localize('UTC'))
    for api_field, archive_field in FIELDS.items():
        valid &= pd.to_numeric(joined[api_field], errors='raise').eq(joined[archive_field])
    selected = joined.loc[valid].copy()
    manifest = []
    for report, group in selected.groupby('report_date'):
        if set(group.ticker) != set(CODES.values()):
            continue
        # Public dataset creation is evidence for conservative API availability;
        # wait until the following 05:00 UTC, after both contracts were created.
        cutoff = group[':created_at'].max().normalize() + pd.Timedelta(days=1, hours=5)
        query = {'$select': ','.join(['cftc_contract_market_code', 'report_date_as_yyyy_mm_dd',
                                     ':created_at', ':updated_at', *FIELDS]),
                 '$where': f"report_date_as_yyyy_mm_dd='{report:%Y-%m-%d}T00:00:00' AND cftc_contract_market_code in ('088691','084691')"}
        manifest.append({'report_date': f'{report:%Y-%m-%d}', 'available_at': cutoff.isoformat(),
                         'source_url': API + '?' + urlencode(query)})
    return pd.DataFrame(manifest, columns=['report_date', 'available_at', 'source_url']), joined.assign(eligible=valid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='config/config.yml')
    parser.add_argument('--settings')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    cfg = read_config(args.config, args.settings)
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    query = {'$select': ','.join(['cftc_contract_market_code', 'report_date_as_yyyy_mm_dd',
                                 ':created_at', ':updated_at', *FIELDS]),
             '$where': "cftc_contract_market_code in ('088691','084691') AND report_date_as_yyyy_mm_dd >= '2022-10-21T00:00:00'",
             '$order': 'report_date_as_yyyy_mm_dd,cftc_contract_market_code', '$limit': 10000}
    url = API + '?' + urlencode(query)
    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; capstone-research/1.0)'}), timeout=45) as response:
        payload = response.read()
    (output / 'api-rows.json').write_bytes(payload)
    rows = json.loads(payload)
    if not isinstance(rows, list) or not rows or len(rows) >= 10000:
        raise ValueError('Empty, invalid or truncated API response')
    archives, archive_hashes = [], {}
    first = pd.Timestamp('2022-10-21').year
    last = pd.Timestamp(cfg['end']).year if cfg.get('end') else datetime.now(timezone.utc).year
    for year in range(first, last + 1):
        path = Path(cfg['data_dir']) / 'raw/cftc' / f'{year}.zip'
        data = _read_snapshot(path)
        archive_hashes[str(year)] = hashlib.sha256(data).hexdigest()
        archives.append(parse_cot_archive(data))
    manifest, audit = validate_rows(rows, pd.concat(archives, ignore_index=True))
    manifest.to_csv(output / 'release_dates.csv', index=False)
    audit.to_csv(output / 'row-audit.csv', index=False)
    evidence = {'source_url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'payload_sha256': hashlib.sha256(payload).hexdigest(), 'archive_sha256': archive_hashes,
                'api_rows': len(rows), 'paired_reports': len(manifest),
                'policy': 'post-launch, unchanged rows matching all five archive position fields; next-day 05:00 UTC after both contracts; API availability upper bound, not original release instant',
                'sources': ['https://www.cftc.gov/PressRoom/PressReleases/8612-22',
                            'https://www.cftc.gov/media/13801/COTFinal043026/download',
                            'https://dev.socrata.com/docs/system-fields.html']}
    (output / 'provenance.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
