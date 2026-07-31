"""Unit tests for silver transform pure functions."""
import pandas as pd

from src.silver import transform as t


def test_dates_parse_yyyymmdd():
    df = pd.DataFrame({"clm_from_dt": ["20080829", "", "bad"]})
    out = t.parse_dates(df)
    assert out["clm_from_dt"].iloc[0].strftime("%Y-%m-%d") == "2008-08-29"
    assert pd.isna(out["clm_from_dt"].iloc[1])  # empty -> NaT
    assert pd.isna(out["clm_from_dt"].iloc[2])  # unparseable -> NaT


def test_ids_are_not_cast_to_numeric():
    # alphanumeric provider id must survive as string
    df = pd.DataFrame({"prvdr_num": ["3900QF"], "clm_pmt_amt": ["8000"]})
    out = t.cast_amounts(df, extra=[])
    assert out["prvdr_num"].iloc[0] == "3900QF"
    assert out["clm_pmt_amt"].iloc[0] == 8000  # amount cast to numeric


def test_chronic_flags_decoded():
    df = pd.DataFrame({"sp_diabetes": ["1", "2"]})
    out = t.decode_chronic_flags(df)
    assert list(out["has_diabetes"]) == [True, False]
    assert "sp_diabetes" not in out.columns


def test_unpivot_diagnoses_long_and_drops_empty():
    df = pd.DataFrame({
        "desynpuf_id": ["A"], "clm_id": ["1"],
        "icd9_dgns_cd_1": ["2761"], "icd9_dgns_cd_2": [""],
        "admtng_icd9_dgns_cd": ["78659"],
    })
    out = t.unpivot_diagnoses(df, "inpatient")
    codes = set(out["icd9_code"])
    assert codes == {"2761", "78659"}          # empty dropped
    assert 0 in set(out["dgns_seq"])            # admitting captured as seq 0
    assert (out["claim_type"] == "inpatient").all()


def test_dedup_on_keys():
    df = pd.DataFrame({"clm_id": ["1", "1", "2"], "v": ["a", "b", "c"]})
    out = t.dedup(df, "inpatient")
    assert len(out) == 2
