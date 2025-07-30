/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */
`default_nettype none
module tt_um_bist (
    input  wire [7:0] ui_in,    // [7]=start, [6]=write_en, [5:4]=mode, [3:0]=data_in
    output wire [7:0] uo_out,   // [7]=done, [6]=fail, [5:0]=reserved/debug
    input  wire [7:0] uio_in,   // [3:0]=address input (optional external)
    output wire [7:0] uio_out,  // unused
    output wire [7:0] uio_oe,   // unused
    input  wire       ena,      // always high
    input  wire       clk,
    input  wire       rst_n
);

    // Parameters
    parameter MEM_DEPTH = 16;
    parameter ADDR_WIDTH = 4;

    // Signals
    reg  [7:0] mem [0:MEM_DEPTH-1]; // simple 8-bit SRAM
    reg  [ADDR_WIDTH-1:0] addr;
    reg  [7:0] data_out;
    reg        fail;
    reg        done;
    reg  [1:0] state;

    // FSM States
    localparam IDLE  = 2'b00;
    localparam WRITE = 2'b01;
    localparam READ  = 2'b10;
    localparam DONE  = 2'b11;

    // Unpack inputs
    wire start     = ui_in[7];
    wire write_en  = ui_in[6];
    wire [1:0] mode = ui_in[5:4]; // can be used for test selection
    wire [3:0] data_in = ui_in[3:0];
    wire [ADDR_WIDTH-1:0] ext_addr = uio_in[3:0];

    // SRAM BIST FSM
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            addr <= 0;
            state <= IDLE;
            fail <= 0;
            done <= 0;
        end else begin
            case (state)
                IDLE: begin
                    done <= 0;
                    if (start) begin
                        addr <= 0;
                        fail <= 0;
                        state <= WRITE;
                    end
                end

                WRITE: begin
                    mem[addr] <= {4'b0000, data_in};  // write padded data
                    addr <= addr + 1;
                    if (addr == MEM_DEPTH - 1)
                        state <= READ;
                end

                READ: begin
                    if (mem[addr] != {4'b0000, data_in})
                        fail <= 1;
                    addr <= addr + 1;
                    if (addr == MEM_DEPTH - 1)
                        state <= DONE;
                end

                DONE: begin
                    done <= 1;
                    if (!start)
                        state <= IDLE;
                end
            endcase
        end
    end

    // Output assignment
    assign uo_out = {done, fail, 6'b000000};
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // Unused inputs
    wire _unused = &{ena};

endmodule
