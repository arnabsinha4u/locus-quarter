from locus_quarter import locus_quarter

config = "test/config-test-locus-quarter.ini"
objMul = locus_quarter(config)

def test_geocode():
  assert objMul.src_geocode("Koningen Wilhelminaplein 430, 1062 KS Amsterdam, Netherlands") == ({'lat': 52.3543272, 'lng': 4.8401973},'Kon. Wilhelminaplein 430, 1062 KS Amsterdam, Netherlands')
