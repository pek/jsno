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


def test_jsonify_time():
    assert jsonify(datetime.time(23, 59, 59)) == "23:59:59"


def test_unjsonify_time():
    assert unjsonify[datetime.time]("23:59:59") == datetime.time(23, 59, 59)


def test_unjsonify_time_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[datetime.time]("24:59:59")


def test_unjsonify_date_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[datetime.date]("today")


def test_jsonify_timedelta_days_only():
    assert jsonify(datetime.timedelta(days=23)) == "23 days, 0:00:00"


def test_jsonify_timedelta_microsecond():
    assert jsonify(datetime.timedelta(microseconds=1)) == "0:00:00.000001"


def test_jsonify_timedelta_negative_days():
    assert jsonify(datetime.timedelta(days=-123)) == "-123 days, 0:00:00"


def test_unjsonify_timedelta_days_only():
    assert unjsonify[datetime.timedelta]("23 days, 0:00:00") == datetime.timedelta(days=23)


def test_unjsonify_timedelta_negative():
    assert (
        unjsonify[datetime.timedelta]("-10 days, 1:23:45") ==
        datetime.timedelta(days=-11, hours=22, minutes=36, seconds=15)
    )


def test_unjsonify_timedelta_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[datetime.timedelta]("-10 days, 24:23:45")


def test_unjsonify_timezone_utc():
    assert unjsonify[datetime.timezone]("UTC") == datetime.timezone.utc


def test_unjsonify_timezone_utc_positive():
    assert (
        unjsonify[datetime.timezone]("UTC+01:00:00") ==
        datetime.timezone(datetime.timedelta(hours=1))
    )


def test_unjsonify_timezone_utc_negative():
    assert (
        unjsonify[datetime.timezone]("UTC-03:30:00") ==
        datetime.timezone(datetime.timedelta(hours=-3, minutes=-30))
    )


def test_unjsonify_timezone_failure():
    with pytest.raises(UnjsonifyError):
        unjsonify[datetime.timezone]("UTC03:30:00")
