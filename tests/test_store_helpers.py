from db.store import _uuid_or_none


def test_uuid_or_none_passes_real_uuids():
    u = "123e4567-e89b-12d3-a456-426614174000"
    assert _uuid_or_none(u) == u


def test_uuid_or_none_rejects_synthetic_front_half_ids():
    # front-half/company-law items carry non-UUID ids; they must persist as NULL
    assert _uuid_or_none("fh-going_concern_fronthalf") is None
    assert _uuid_or_none("fh-s418") is None
    assert _uuid_or_none("") is None
    assert _uuid_or_none(None) is None
