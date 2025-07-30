# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


@cocotb.test()
async def test_sram_bist_io(dut):
    dut._log.info("Starting SRAM BIST Test")

    # Create and start a clock
    clock = Clock(dut.clk, 10, units="ns")  # 100 MHz clock
    cocotb.start_soon(clock.start())

    # Apply reset
    dut.rst.value = 1
    dut.in_.value = 0  # avoid in keyword conflict in Python
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0
    await ClockCycles(dut.clk, 2)

    dut._log.info("Triggering BIST")
    # Set in[5] = 1 to start BIST
    dut.in_.value = 0b0010_0000
    await ClockCycles(dut.clk, 1)
    dut.in_.value = 0  # Clear the start signal

    # Wait for DONE state to complete
    while dut.out.value.integer & 0b00000001 == 0:
        await ClockCycles(dut.clk, 1)

    bist_done = dut.out.value.integer & 0b00000001
    bist_fail = (dut.out.value.integer >> 1) & 0b1

    dut._log.info(f"BIST done: {bist_done}, fail: {bist_fail}")

    assert bist_done == 1, "BIST did not complete as expected"
    assert bist_fail == 0, "BIST failed unexpectedly"

    dut._log.info("SRAM BIST Test Passed")
