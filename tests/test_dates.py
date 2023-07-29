import datetime
import zoneinfo

import pytest

from jsno import jsonify, unjsonify, UnjsonifyError


helsinki = zoneinfo.ZoneInfo("Europe/Helsinki")
ouagadougou = zoneinfo.ZoneInfo("Africa/Ouagadougou")
utc = zoneinfo.ZoneInfo("UTC")


def test_jsonify_dates():

    assert (
        jsonify(
            [
                datetime.datetime(2023, 7, 15, 8, 39, 0, tzinfo=helsinki),
                datetime.datetime(2023, 7, 15, 8, 40, 10, tzinfo=utc),
                datetime.datetime(2023, 7, 15, 8, 41, 20),
                datetime.datetime(2023, 7, 15, 8, 39, 0, 1, tzinfo=helsinki),
                datetime.datetime(2023, 7, 15, 8, 40, 10, 120, tzinfo=utc),
                datetime.datetime(2023, 7, 15, 8, 40, 10, 1, tzinfo=datetime.timezone.utc),
                datetime.datetime(5012, 7, 15, 8, 41, 20, 123400),
                datetime.datetime(2023, 7, 29, 13, 23, 11, tzinfo=ouagadougou)
            ]
        )
        ==
        [
            "2023-07-15T08:39:00+03:00",
            "2023-07-15T08:40:10Z",
            "2023-07-15T08:41:20",
            "2023-07-15T08:39:00.000001+03:00",
            "2023-07-15T08:40:10.000120Z",
            "2023-07-15T08:40:10.000001Z",
            "5012-07-15T08:41:20.123400",
            "2023-07-29T13:23:11Z",
        ]
    )


def test_jsonify_old_dates():
    assert (
        jsonify(
            [
                datetime.datetime(1940, 7, 15, 8, 39, 0, tzinfo=helsinki),
                datetime.datetime(1960, 7, 15, 8, 39, 0, tzinfo=helsinki),
                datetime.datetime(1980, 7, 15, 8, 39, 0, tzinfo=helsinki),
                datetime.datetime(1981, 7, 15, 8, 39, 0, tzinfo=helsinki),
            ]
        )
        ==
        [
            "1940-07-15T08:39:00+02:00",
            "1960-07-15T08:39:00+02:00",
            "1980-07-15T08:39:00+02:00",
            "1981-07-15T08:39:00+03:00",
        ]
    )


def test_unjsonify_datetimes():
    assert (
        unjsonify[list[datetime.datetime]](
            [
                "2023-07-15T08:39:00+03:00",
                "2023-07-15T08:40:10Z",
                "2023-07-15T08:41:20",
                "2023-07-15T08:39:00.000001+03:00",
                "2023-07-15T08:40:10.000120Z",
                "5012-07-15T08:41:20.123400",
            ]
        ) == (
            [
                datetime.datetime(2023, 7, 15, 8, 39, 0, tzinfo=helsinki),
                datetime.datetime(2023, 7, 15, 8, 40, 10, tzinfo=utc),
                datetime.datetime(2023, 7, 15, 8, 41, 20),
                datetime.datetime(2023, 7, 15, 8, 39, 0, 1, tzinfo=helsinki),
                datetime.datetime(2023, 7, 15, 8, 40, 10, 120, tzinfo=utc),
                datetime.datetime(5012, 7, 15, 8, 41, 20, 123400),
            ]
        )
    )


def test_unjsonify_datetime_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[datetime.datetime]('2023-13-13T12:34:56')
