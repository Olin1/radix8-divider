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


@cocotb.test()
async def test_exact_latency_and_done_pulse(dut):
    """Normal division must take exactly WIDTH iteration cycles."""

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    await reset_dut(dut)

    width = len(dut.dividend)
    mask = (1 << width) - 1

    dividend = 0xA5A55A5A & mask
    divisor = 37

    # Present request before the active clock edge.
    await FallingEdge(dut.clk)

    dut.dividend.value = dividend
    dut.divisor.value = divisor
    dut.start.value = 1

    # Acceptance edge.
    await RisingEdge(dut.clk)
    await ReadOnly()

    assert int(dut.busy.value) == 1
    assert int(dut.done.value) == 0
    assert int(dut.div_by_zero.value) == 0

    await FallingEdge(dut.clk)
    dut.start.value = 0

    # A restoring radix-2 divider performs one quotient bit per cycle.
    for cycle in range(1, width + 1):
        await RisingEdge(dut.clk)
        await ReadOnly()

        if cycle < width:
            assert int(dut.busy.value) == 1, (
                f"busy dropped early at cycle {cycle}"
            )
            assert int(dut.done.value) == 0, (
                f"done asserted early at cycle {cycle}"
            )
        else:
            assert int(dut.busy.value) == 0
            assert int(dut.done.value) == 1

    expected = divide_unsigned(dividend, divisor, width)

    assert int(dut.quotient.value) == expected["quotient"]
    assert int(dut.remainder.value) == expected["remainder"]

    # done must be a one-cycle pulse.
    await RisingEdge(dut.clk)
    await ReadOnly()

    assert int(dut.done.value) == 0


@cocotb.test()
async def test_divide_by_zero_protocol(dut):
    """Divide-by-zero must complete immediately and deterministically."""

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    await reset_dut(dut)

    width = len(dut.dividend)
    mask = (1 << width) - 1

    dividend = 0x12345678 & mask

    await FallingEdge(dut.clk)

    dut.dividend.value = dividend
    dut.divisor.value = 0
    dut.start.value = 1

    await RisingEdge(dut.clk)
    await ReadOnly()

    assert int(dut.done.value) == 1
    assert int(dut.busy.value) == 0
    assert int(dut.div_by_zero.value) == 1

    assert int(dut.quotient.value) == mask
    assert int(dut.remainder.value) == dividend

    await FallingEdge(dut.clk)
    dut.start.value = 0

    # done must clear on the next cycle.
    await RisingEdge(dut.clk)
    await ReadOnly()

    assert int(dut.done.value) == 0


@cocotb.test()
async def test_start_while_busy_is_ignored(dut):
    """A new start request while busy must not corrupt the active operation."""

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    await reset_dut(dut)

    width = len(dut.dividend)
    mask = (1 << width) - 1

    first_dividend = 0xDEADBEEF & mask
    first_divisor = 97

    second_dividend = 12345
    second_divisor = 7

    # Launch first transaction.
    await FallingEdge(dut.clk)

    dut.dividend.value = first_dividend
    dut.divisor.value = first_divisor
    dut.start.value = 1

    await RisingEdge(dut.clk)
    await ReadOnly()

    assert int(dut.busy.value) == 1

    await FallingEdge(dut.clk)
    dut.start.value = 0

    # Allow the first operation to progress.
    for _ in range(4):
        await RisingEdge(dut.clk)

    # Attempt to launch another transaction while busy.
    await FallingEdge(dut.clk)

    dut.dividend.value = second_dividend
    dut.divisor.value = second_divisor
    dut.start.value = 1

    await RisingEdge(dut.clk)
    await ReadOnly()

    assert int(dut.busy.value) == 1

    await FallingEdge(dut.clk)
    dut.start.value = 0

    # Wait for the original transaction.
    completed = False

    for _ in range(width + 3):
        await RisingEdge(dut.clk)
        await ReadOnly()

        if int(dut.done.value):
            completed = True
            break

    assert completed, "Original transaction never completed"

    expected = divide_unsigned(
        first_dividend,
        first_divisor,
        width,
    )

    assert int(dut.quotient.value) == expected["quotient"]
    assert int(dut.remainder.value) == expected["remainder"]


@cocotb.test()
async def test_reset_during_operation(dut):
    """Reset must cancel an in-flight transaction and restore idle state."""

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    await reset_dut(dut)

    width = len(dut.dividend)

    # Start a normal operation.
    await FallingEdge(dut.clk)

    dut.dividend.value = 0xABCDEF01
    dut.divisor.value = 113
    dut.start.value = 1

    await RisingEdge(dut.clk)
    await ReadOnly()

    assert int(dut.busy.value) == 1

    await FallingEdge(dut.clk)
    dut.start.value = 0

    for _ in range(5):
        await RisingEdge(dut.clk)

    # Assert asynchronous reset.
    await FallingEdge(dut.clk)
    dut.rst_n.value = 0

    await RisingEdge(dut.clk)
    await ReadOnly()

    assert int(dut.busy.value) == 0
    assert int(dut.done.value) == 0
    assert int(dut.div_by_zero.value) == 0
    assert int(dut.quotient.value) == 0
    assert int(dut.remainder.value) == 0

    # Release reset and verify that another operation succeeds.
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1

    result = await run_division(
        dut,
        1000,
        17,
    )

    check_result(
        width,
        1000,
        17,
        result,
    )
