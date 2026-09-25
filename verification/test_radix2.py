import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge

from division_reference import divide_unsigned


async def reset_dut(dut):
    dut.start.value = 0
    dut.dividend.value = 0
    dut.divisor.value = 0
    dut.rst_n.value = 0

    for _ in range(3):
        await RisingEdge(dut.clk)

    await FallingEdge(dut.clk)
    dut.rst_n.value = 1


async def run_division(dut, dividend, divisor):
    width = len(dut.dividend)

    # Drive inputs away from the active clock edge.
    await FallingEdge(dut.clk)

    dut.dividend.value = dividend
    dut.divisor.value = divisor
    dut.start.value = 1

    # Request is sampled here.
    await RisingEdge(dut.clk)
    await ReadOnly()

    # Divide-by-zero completes immediately.
    if int(dut.done.value):
        result = (
            int(dut.quotient.value),
            int(dut.remainder.value),
            int(dut.div_by_zero.value),
        )

        await FallingEdge(dut.clk)
        dut.start.value = 0

        return result

    await FallingEdge(dut.clk)
    dut.start.value = 0

    # A WIDTH-bit restoring divider requires WIDTH iterations.
    for _ in range(width + 3):
        await RisingEdge(dut.clk)
        await ReadOnly()

        if int(dut.done.value):
            return (
                int(dut.quotient.value),
                int(dut.remainder.value),
                int(dut.div_by_zero.value),
            )

    raise AssertionError("Divider timed out")


def check_result(width, dividend, divisor, rtl_result):
    expected = divide_unsigned(dividend, divisor, width)

    quotient, remainder, div_by_zero = rtl_result

    assert quotient == expected["quotient"]
    assert remainder == expected["remainder"]
    assert div_by_zero == int(expected["div_by_zero"])

    if divisor != 0:
        assert dividend == quotient * divisor + remainder
        assert remainder < divisor


@cocotb.test()
async def test_corner_cases(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    await reset_dut(dut)

    width = len(dut.dividend)
    maximum = (1 << width) - 1

    vectors = [
        (0, 1),
        (1, 1),
        (maximum, 1),
        (maximum, maximum),
        (maximum, 2),
        (maximum, 3),
        (100, 7),
        (123456, 37),
        (0, maximum),
        (1, maximum),
        (maximum, 0),
        (0, 0),
    ]

    for dividend, divisor in vectors:
        dividend &= maximum
        divisor &= maximum

        rtl_result = await run_division(dut, dividend, divisor)

        check_result(
            width,
            dividend,
            divisor,
            rtl_result,
        )


@cocotb.test()
async def test_random_vectors(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    await reset_dut(dut)

    width = len(dut.dividend)

    rng = random.Random(0x8AD1C8)

    for _ in range(100):
        dividend = rng.getrandbits(width)
        divisor = rng.getrandbits(width)

        rtl_result = await run_division(
            dut,
            dividend,
            divisor,
        )

        check_result(
            width,
            dividend,
            divisor,
            rtl_result,
        )
