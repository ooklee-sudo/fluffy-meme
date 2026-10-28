import math, pytest
from detectability import required_effect_scale, crit, mde, gamma_star, required_adoption, earliest_year, classify, detectability, se_from_design

K, MDE24, MDE23 = 5.3310921564977445, 0.04972575936879852, 0.0192898500

def test_crit():  assert abs(crit() - 2.8016) < 1e-3
def test_special_case_equation5():  assert gamma_star(0.0955, -0.5, k=K) == pytest.approx(-0.0955 * 0.5 / K)
@pytest.mark.parametrize('A,beta,expected', [(0.0955, -0.19, -0.0034), (0.0955, -0.5, -0.0090), (0.3618, -0.19, -0.0129), (0.3618, -0.5, -0.0339), (0.021, -0.5, -0.0020)])
def test_table5_panel_a(A, beta, expected):  assert gamma_star(A, beta, k=K) == pytest.approx(expected, abs=6e-5)
def test_table5_mde():  assert mde(0.0177592) == pytest.approx(MDE24, rel=2e-3)
def test_attenuation_sqrt_r():  assert gamma_star(0.3, -0.5, k=K, R=0.5) == pytest.approx(gamma_star(0.3, -0.5, k=K) * math.sqrt(0.5))
def test_assimilation_gap_scales_linearly():  assert gamma_star(0.3, -0.5, k=K, g=0.25) == pytest.approx(0.25 * gamma_star(0.3, -0.5, k=K))
def test_required_adoption_table6():
    t = MDE24 * K
    assert required_adoption(-0.5, MDE24, k=K) == pytest.approx(t / 0.5)
    assert required_adoption(-0.19, MDE24, k=K) is None
@pytest.mark.parametrize('beta,slope,all_year,media_year', [(-0.5, 0.75, 2029, 2026), (-0.5, 0.5, 2030, 2027), (-0.5, 0.25, 2035, 2028), (-0.8, 0.75, 2028, 2025), (-0.8, 0.5, 2029, 2025), (-0.8, 0.25, 2032, 2025)])
def test_table6_dates(beta, slope, all_year, media_year):
    req = required_adoption(beta, MDE24, k=K)
    assert earliest_year(0.0955, req, slope) == all_year and earliest_year(0.3618, req, slope) == media_year
def test_classification_rules():
    assert classify(-0.029, 0.0178, gamma_star(0.3618, -0.5, k=K), gamma_max=-0.0339) == 'uninformative'
    assert classify(-0.30, 0.01, -0.20, gamma_max=-0.20) == 'other causes'
    assert classify(-0.05, 0.01, -0.20, gamma_max=-0.25) == 'rejects complete assimilation'
    assert classify(-0.19, 0.02, -0.20, gamma_max=-0.25) == 'consistent with complete assimilation'
def test_detectability_dict():
    d = detectability(0.3618, -0.5, 0.0177592, k=K)
    assert not d['detectable'] and d['required_adoption'] == pytest.approx(MDE24 * K / 0.5, rel=2e-3)
def test_se_from_design():  assert se_from_design(96, 0.31, 0.12, 6.3) == pytest.approx(0.0178, abs=1e-3)

def test_unexplained_signal_term_vanishes_when_reliable():
    a = se_from_design(96, 0.31, 0.12, 6.3); b = se_from_design(96, 0.31, 0.12, 6.3, A=0.4, beta=-0.5, sigma_s=0.19, R=1.0)
    assert a == pytest.approx(b)
def test_unexplained_signal_term_raises_se():
    assert se_from_design(96, 0.31, 0.12, 6.3, A=0.7, beta=-2.0, sigma_s=0.19, R=0.5) > se_from_design(96, 0.31, 0.12, 6.3)
def test_required_effect_scale_self_consistent():
    X = required_effect_scale(96, 0.31, 0.12, 6.3, R=0.6)
    gam = X * math.sqrt(0.6); se = se_from_design(96, 0.31, 0.12, 6.3, A=1.0, beta=X, sigma_s=1.0, R=0.6)
    assert gam == pytest.approx(crit() * se, rel=1e-9)
def test_required_effect_scale_impossible():
    assert required_effect_scale(10, 0.31, 0.12, 6.3, R=0.05) is None
