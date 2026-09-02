"""Tests for the stability rule.

Plain unit tests: no database, no scheduler, no waiting on a real clock.
"""

from __future__ import annotations

from django.test import SimpleTestCase

from matching.ingest.stability import (
    Measurement,
    is_stable,
    next_measurement,
    required_consecutive_polls,
)


class RequiredConsecutivePollsTests(SimpleTestCase):
    def test_defaults_give_six_measurements(self):
        # 30 minutes of stability at a 5 minute poll interval — docs/architecture.md.
        self.assertEqual(required_consecutive_polls(30, 5), 6)

    def test_rounds_up_when_it_does_not_divide_evenly(self):
        self.assertEqual(required_consecutive_polls(30, 7), 5)
        self.assertEqual(required_consecutive_polls(10, 3), 4)

    def test_stability_shorter_than_the_poll_interval_needs_one_measurement(self):
        # Guard: a margin below the interval cannot ask for less than one poll.
        self.assertEqual(required_consecutive_polls(5, 30), 1)
        self.assertEqual(required_consecutive_polls(1, 5), 1)

    def test_zero_or_negative_stability_disables_the_margin(self):
        self.assertEqual(required_consecutive_polls(0, 5), 1)
        self.assertEqual(required_consecutive_polls(-10, 5), 1)

    def test_poll_interval_must_be_positive(self):
        with self.assertRaises(ValueError):
            required_consecutive_polls(30, 0)


class NextMeasurementTests(SimpleTestCase):
    def test_first_sighting_starts_the_streak(self):
        self.assertEqual(next_measurement(None, 100), Measurement(100, 1))

    def test_unchanged_size_extends_the_streak(self):
        self.assertEqual(next_measurement(Measurement(100, 3), 100).unchanged_polls, 4)

    def test_a_growing_file_restarts_the_streak(self):
        self.assertEqual(next_measurement(Measurement(100, 5), 250), Measurement(250, 1))

    def test_a_shrinking_file_restarts_the_streak(self):
        self.assertEqual(next_measurement(Measurement(250, 5), 100), Measurement(100, 1))


class IsStableTests(SimpleTestCase):
    def test_a_file_seen_once_is_not_stable_yet(self):
        self.assertFalse(is_stable(None, Measurement(100, 1), 6))

    def test_stable_only_on_the_sixth_unchanged_measurement(self):
        previous = None
        for expected_poll in range(1, 6):
            current = next_measurement(previous, 100)
            self.assertEqual(current.unchanged_polls, expected_poll)
            self.assertFalse(is_stable(previous, current, 6))
            previous = current

        sixth = next_measurement(previous, 100)
        self.assertTrue(is_stable(previous, sixth, 6))

    def test_a_file_that_grows_late_in_the_run_starts_over(self):
        previous = Measurement(100, 5)
        current = next_measurement(previous, 500)
        self.assertFalse(is_stable(previous, current, 6))
        self.assertEqual(current.unchanged_polls, 1)

    def test_a_size_change_is_unstable_even_for_an_unfolded_measurement(self):
        # `current` was not folded from `previous`, but the size differs, so the
        # run has clearly been broken.
        self.assertFalse(is_stable(Measurement(100, 5), Measurement(500, 9), 6))

    def test_one_required_measurement_accepts_immediately(self):
        self.assertTrue(is_stable(None, Measurement(100, 1), 1))

    def test_requirement_below_one_is_treated_as_one(self):
        self.assertTrue(is_stable(None, Measurement(100, 1), 0))
