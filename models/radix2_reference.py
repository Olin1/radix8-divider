"""Bit-accurate restoring radix-2 unsigned division model."""


def radix2_divide_unsigned(dividend: int, divisor: int, width: int = 32):
    """Model the restoring radix-2 algorithm used by the RTL."""

    mask = (1 << width) - 1

    dividend &= mask
    divisor &= mask

    if divisor == 0:
        return {
            "quotient": mask,
            "remainder": dividend,
            "div_by_zero": True,
        }

    quotient = dividend
    remainder = 0

    for _ in range(width):
        next_dividend_bit = (quotient >> (width - 1)) & 1

        remainder = (remainder << 1) | next_dividend_bit
        quotient = (quotient << 1) & mask

        if remainder >= divisor:
            remainder -= divisor
            quotient |= 1

    return {
        "quotient": quotient,
        "remainder": remainder,
        "div_by_zero": False,
    }


if __name__ == "__main__":
    vectors = [
        (100, 7),
        (255, 16),
        (12345, 37),
        (42, 1),
        (42, 0),
    ]

    for dividend, divisor in vectors:
        result = radix2_divide_unsigned(dividend, divisor)

        print(
            f"{dividend} / {divisor}: "
            f"Q={result['quotient']} "
            f"R={result['remainder']} "
            f"DBZ={result['div_by_zero']}"
        )
