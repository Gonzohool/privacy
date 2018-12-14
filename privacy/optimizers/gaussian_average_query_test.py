# Copyright 2018, The TensorFlow Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for GaussianAverageQuery."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf

from privacy.optimizers import gaussian_average_query


class GaussianAverageQueryTest(tf.test.TestCase):

  def _run_query(self, query, *records):
    """Executes query on the given set of records and returns the result."""
    global_state = query.initial_global_state()
    params = query.derive_sample_params(global_state)
    sample_state = query.initial_sample_state(global_state, records[0])
    for record in records:
      sample_state = query.accumulate_record(params, sample_state, record)
    result, _ = query.get_query_result(sample_state, global_state)
    return result

  def test_gaussian_sum_no_clip_no_noise(self):
    with self.cached_session() as sess:
      record1 = tf.constant([2.0, 0.0])
      record2 = tf.constant([-1.0, 1.0])

      query = gaussian_average_query.GaussianSumQuery(
          l2_norm_clip=10.0, stddev=0.0)
      query_result = self._run_query(query, record1, record2)
      result = sess.run(query_result)
      expected = [1.0, 1.0]
      self.assertAllClose(result, expected)

  def test_gaussian_sum_with_clip_no_noise(self):
    with self.cached_session() as sess:
      record1 = tf.constant([-6.0, 8.0])  # Clipped to [-3.0, 4.0].
      record2 = tf.constant([4.0, -3.0])  # Not clipped.

      query = gaussian_average_query.GaussianSumQuery(
          l2_norm_clip=5.0, stddev=0.0)
      query_result = self._run_query(query, record1, record2)
      result = sess.run(query_result)
      expected = [1.0, 1.0]
      self.assertAllClose(result, expected)

  def test_gaussian_sum_with_noise(self):
    with self.cached_session() as sess:
      record1, record2 = 2.71828, 3.14159
      stddev = 1.0

      query = gaussian_average_query.GaussianSumQuery(
          l2_norm_clip=5.0, stddev=stddev)
      query_result = self._run_query(query, record1, record2)

      noised_sums = []
      for _ in xrange(1000):
        noised_sums.append(sess.run(query_result))

      result_stddev = np.std(noised_sums)
      self.assertNear(result_stddev, stddev, 0.1)

  def test_gaussian_average_no_noise(self):
    with self.cached_session() as sess:
      record1 = tf.constant([5.0, 0.0])   # Clipped to [3.0, 0.0].
      record2 = tf.constant([-1.0, 2.0])  # Not clipped.

      query = gaussian_average_query.GaussianAverageQuery(
          l2_norm_clip=3.0, sum_stddev=0.0, denominator=2.0)
      query_result = self._run_query(query, record1, record2)
      result = sess.run(query_result)
      expected_average = [1.0, 1.0]
      self.assertAllClose(result, expected_average)

  def test_gaussian_average_with_noise(self):
    with self.cached_session() as sess:
      record1, record2 = 2.71828, 3.14159
      sum_stddev = 1.0
      denominator = 2.0

      query = gaussian_average_query.GaussianAverageQuery(
          l2_norm_clip=5.0, sum_stddev=sum_stddev, denominator=denominator)
      query_result = self._run_query(query, record1, record2)

      noised_averages = []
      for _ in xrange(1000):
        noised_averages.append(sess.run(query_result))

      result_stddev = np.std(noised_averages)
      avg_stddev = sum_stddev / denominator
      self.assertNear(result_stddev, avg_stddev, 0.1)


if __name__ == '__main__':
  tf.test.main()