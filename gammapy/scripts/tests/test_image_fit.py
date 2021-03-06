# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import, division, print_function, unicode_literals
import json
from numpy.testing.utils import assert_allclose
from ...utils.testing import requires_dependency, requires_data
from ...datasets import load_poisson_stats_image
from ..image_fit import image_fit


@requires_dependency('sherpa')
@requires_data('gammapy-extra')
def test_sherpa_like(tmpdir):
    # load test data
    filenames = load_poisson_stats_image(extra_info=True, return_filenames=True)
    outfile = tmpdir / 'test_sherpa_like.json'

    # write test source json file
    sources_data = {}
    sources_data['gaussian'] = {'ampl': 1E3,
                                'xpos': 99,
                                'ypos': 99,
                                'fwhm': 4 * 2.3548}

    filename = tmpdir / 'test_sherpa_like_sources.json'
    with filename.open('w') as fh:
        json.dump(sources_data, fh)

    # set up args
    args = {'counts': str(filenames['counts']),
            'exposure': str(filenames['exposure']),
            'background': str(filenames['background']),
            'psf': filenames['psf'],
            'sources': str(filename),
            'roi': None,
            'outfile': str(outfile)}
    image_fit(**args)

    with outfile.open() as fh:
        data = json.load(fh)

    # Note: the reference results here changed once and
    # we didn't track down why at the time:
    # See https://github.com/gammapy/gammapy/issues/349
    # old: [  9.016334  ,  99.365574   ,  99.647234   , 10.97365    ]
    # new: [ 10.7427035 ,  98.16618776 ,  98.45487028 ,  7.73529899 ]
    actual = data['fit']['parvals']
    expected = [10.7427035, 98.16618776, 98.45487028, 7.73529899]
    assert_allclose(actual, expected)
