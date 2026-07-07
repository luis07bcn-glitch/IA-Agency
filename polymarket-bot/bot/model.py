"""Modelo de probabilidad para ventanas cortas Up/Down.

v2: retorno log ~ normal con media mu_1m * tau (drift de la tendencia
reciente) y desviación sigma_1m * sqrt(tau):

    P(cierre >= open) = Phi( (ln(spot/open) + mu_1m*tau) / (sigma_1m*sqrt(tau)) )

Con mu_1m = 0 se recupera el modelo v1 (sin tendencia). El drift se pondera
con drift_weight porque el momentum a 5 min persiste solo parcialmente.
"""
import math


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def prob_up(spot: float, open_price: float, sigma_1m: float, minutes_left: float,
            mu_1m: float = 0.0, drift_weight: float = 1.0) -> float:
    if minutes_left <= 0:
        return 1.0 if spot >= open_price else 0.0
    sigma = max(sigma_1m, 1e-6) * math.sqrt(minutes_left)
    expected = math.log(spot / open_price) + drift_weight * mu_1m * minutes_left
    return norm_cdf(expected / sigma)
