"""Golden reference model for unsigned integer division."""


def divide_unsigned(dividend: int, divisor: int, width: int = 32):
    """Return quotient, remainder and divide-by-zero status.

    The operands are restricted to WIDTH bits.

    Divide-by-zero convention for this project:
        quotient  = all ones
        remainder = dividend
    """

    mask = (1 << width) - 1

    dividend &= mask
    divisor &= mask

    if divisor == 0:
        return {
            "quotient": mask,
            "remainder": dividend,
            "div_by_zero": True,
        }

    quotient, remainder = divmod(dividend, divisor)

    return {
        "quotient": quotient & mask,
        "remainder": remainder & mask,
        "div_by_zero": False,
    }


if __name__ == "__main__":
    vectors = [
        (100, 7),
        (255, 16),
        (12345, 37),
        (0, 17),
        (42, 1),
        (42, 0),
    ]

    for dividend, divisor in vectors:
        result = divide_unsigned(dividend, divisor)

        print(
            f"{dividend} / {divisor}: "
            f"Q={result['quotient']} "
            f"R={result['remainder']} "
            f"DBZ={result['div_by_zero']}"
        )
