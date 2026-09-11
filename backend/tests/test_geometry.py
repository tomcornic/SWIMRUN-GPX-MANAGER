import math

import pytest

from app.core.geometry import (
    EARTH_RADIUS_M,
    cumulative_distances_m,
    haversine_m,
    project_equirectangular,
    project_point_onto_track,
    resample_by_distance,
)

REF_LAT, REF_LON = 48.565, -4.596


def _offset_point(dx_m: float, dy_m: float) -> tuple[float, float]:
    lat = REF_LAT + math.degrees(dy_m / EARTH_RADIUS_M)
    lon = REF_LON + math.degrees(dx_m / (EARTH_RADIUS_M * math.cos(math.radians(REF_LAT))))
    return (lat, lon)


def _straight_track(length_m: float) -> list[tuple[float, float, float]]:
    latlon = [_offset_point(0.0, y) for y in (0.0, length_m / 2, length_m)]
    distances = cumulative_distances_m(latlon)
    return [(lat, lon, d) for (lat, lon), d in zip(latlon, distances)]


def test_haversine_zero_for_identical_points():
    assert haversine_m(48.565, -4.596, 48.565, -4.596) == 0.0


def test_haversine_one_degree_of_latitude():
    # Le long d'un méridien, 1° de latitude = R * (pi/180) exactement.
    expected = EARTH_RADIUS_M * math.radians(1.0)
    assert abs(haversine_m(0.0, 0.0, 1.0, 0.0) - expected) < 1.0


def test_cumulative_distances_m():
    # Trois points espacés très précisément de 0.001° de latitude (~111.2 m).
    points = [(0.0, 0.0), (0.001, 0.0), (0.002, 0.0)]
    distances = cumulative_distances_m(points)
    assert distances[0] == 0.0
    step = EARTH_RADIUS_M * math.radians(0.001)
    assert abs(distances[1] - step) < 0.01
    assert abs(distances[2] - 2 * step) < 0.01


def test_cumulative_distances_m_empty():
    assert cumulative_distances_m([]) == []


def test_project_equirectangular_reference_point_is_origin():
    projected = project_equirectangular([(48.565, -4.596)], 48.565, -4.596)
    x, y = projected[0]
    assert abs(x) < 1e-9
    assert abs(y) < 1e-9


def test_project_equirectangular_north_offset_matches_haversine():
    ref_lat, ref_lon = 48.565, -4.596
    target_lat = ref_lat + 0.001
    expected_distance = haversine_m(ref_lat, ref_lon, target_lat, ref_lon)
    _, y = project_equirectangular([(target_lat, ref_lon)], ref_lat, ref_lon)[0]
    assert abs(y - expected_distance) < 0.01


def test_resample_by_distance_regular_step():
    points = [(48.565, -4.596, 0.0), (48.565, -4.5955, 100.0)]
    resampled = resample_by_distance(points, step_m=25.0)
    resampled_distances = [d for _, _, d in resampled]
    assert resampled_distances[0] == 0.0
    assert resampled_distances[-1] == 100.0
    assert resampled_distances == sorted(resampled_distances)


def test_resample_by_distance_empty():
    assert resample_by_distance([], step_m=5.0) == []


def test_project_point_exactly_on_track():
    track = _straight_track(1000.0)
    point_on_track = _offset_point(0.0, 500.0)
    assert project_point_onto_track(point_on_track, track) == pytest.approx(500.0, abs=5.0)


def test_project_point_offset_to_the_side():
    track = _straight_track(1000.0)
    point_a_cote = _offset_point(20.0, 500.0)  # 20 m à l'est du tracé, à mi-hauteur
    assert project_point_onto_track(point_a_cote, track) == pytest.approx(500.0, abs=5.0)


def test_project_point_clamped_before_start():
    track = _straight_track(1000.0)
    point_avant = _offset_point(0.0, -200.0)
    assert project_point_onto_track(point_avant, track) == pytest.approx(0.0, abs=5.0)


def test_project_point_clamped_after_end():
    track = _straight_track(1000.0)
    point_apres = _offset_point(0.0, 1300.0)
    assert project_point_onto_track(point_apres, track) == pytest.approx(1000.0, abs=5.0)


def test_project_point_onto_single_point_track():
    track = [(REF_LAT, REF_LON, 42.0)]
    assert project_point_onto_track(_offset_point(100.0, 100.0), track) == 42.0
