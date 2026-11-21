import pytest

pytest.importorskip('plotly')
from capstone.plotly_report import export_report
from tests.unit.test_reporting import saved_run


def test_interactive_export_is_offline_and_preserves_bundle(saved_run, tmp_path):
    before = {str(p): p.read_bytes() for p in saved_run.rglob('*') if p.is_file()}
    path = export_report(saved_run, tmp_path / 'report.html')
    html = path.read_text()
    assert 'plotly.js' in html and html.count('Plotly.newPlot(') >= 2
    assert '<script src=' not in html
    assert 'fictional-run' in html and 'mean' in html
    assert 'Validation comparison' in html and 'holdout errors' in html
    assert before == {str(p): p.read_bytes() for p in saved_run.rglob('*') if p.is_file()}


def test_export_cannot_write_inside_frozen_bundle(saved_run):
    with pytest.raises(ValueError, match='outside the frozen'):
        export_report(saved_run, saved_run / 'run-1/report.html')
