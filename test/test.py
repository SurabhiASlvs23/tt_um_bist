# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start SRAM BIST test")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Resetting design")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Prepare test: load data 0xA into SRAM via BIST (write + read)
    test_data = 0xA  # 4-bit data
    bist_start = 1 << 7  # Bit 7 = start
    bist_write = 1 << 6  # Bit 6 = write enable (optional)
    bist_mode = 0b00 << 4  # Mode bits [5:4], not used in current version

    dut._log.info("Starting BIST run")
    dut.ui_in.value = bist_start | bist_write | bist_mode | (test_data & 0xF)

    # Wait for completion (done = bit 7 of uo_out)
    for _ in range(100):  # timeout protection
        await ClockCycles(dut.clk, 1)
        if dut.uo_out.value.integer & 0x80:  # done = bit 7
            break
    else:
        assert False, "Timeout: BIST did not complete"

    # Read uo_out
    result = dut.uo_out.value.integer
    done = (result >> 7) & 1
    fail = (result >> 6) & 1

    dut._log.info(f"BIST Done: {done}, Fail: {fail}")
    assert done == 1, "BIST did not set done bit"
    assert fail == 0, "BIST failed unexpectedly"

    # Optional: run again with bad expected data to cause a fail
    dut._log.info("Starting BIST with mismatched read to force failure")

    # Reset and change expected test_data
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    bad_data = 0x5  # deliberately different from earlier
    dut.ui_in.value = bist_start | bist_write | bist_mode | (bad_data & 0xF)

    # Wait for BIST done
    for _ in range(100):
        await ClockCycles(dut.clk, 1)
        if dut.uo_out.value.integer & 0x80:
            break

    result = dut.uo_out.value.integer
    fail = (result >> 6) & 1
    dut._log.info(f"Forced Fail BIST Result: Fail={fail}")
    assert fail == 1, "BIST should have failed but didn't"
