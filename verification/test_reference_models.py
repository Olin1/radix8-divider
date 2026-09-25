from hypothesis import given, settings, strategies as st

from division_reference import divide_unsigned
from radix2_reference import radix2_divide_unsigned


@given(
    width=st.integers(min_value=1, max_value=32),
    dividend=st.integers(min_value=0, max_value=(1 << 32) - 1),
    divisor=st.integers(min_value=0, max_value=(1 << 32) - 1),
)
@settings(
    max_examples=2000,
    deadline=None,
    derandomize=True,
)
def test_radix2_algorithm_matches_mathematical_model(
    width,
    dividend,
    divisor,
):
    expected = divide_unsigned(
        dividend,
        divisor,
        width,
    )

    actual = radix2_divide_unsigned(
        dividend,
        divisor,
        width,
    )

    assert actual == expected

    mask = (1 << width) - 1

    dividend &= mask
    divisor &= mask

    if divisor != 0:
        quotient = actual["quotient"]
        remainder = actual["remainder"]

        assert dividend == quotient * divisor + remainder
        assert remainder < divisor
