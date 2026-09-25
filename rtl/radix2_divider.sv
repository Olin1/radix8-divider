`timescale 1ns/1ps

module radix2_divider #(
    parameter int unsigned WIDTH = 32
) (
    input  logic                 clk,
    input  logic                 rst_n,

    input  logic                 start,
    input  logic [WIDTH-1:0]     dividend,
    input  logic [WIDTH-1:0]     divisor,

    output logic                 busy,
    output logic                 done,
    output logic                 div_by_zero,

    output logic [WIDTH-1:0]     quotient,
    output logic [WIDTH-1:0]     remainder
);

    localparam int unsigned CountW = $clog2(WIDTH + 1);

    logic [WIDTH-1:0] divisor_reg;
    logic [WIDTH-1:0] quotient_reg;
    logic [WIDTH:0]   remainder_reg;

    logic [CountW-1:0] count_reg;

    logic [WIDTH:0]   remainder_shift;
    logic [WIDTH:0]   remainder_next;
    logic [WIDTH-1:0] quotient_next;

    // One restoring-division iteration.
    //
    // Shift the partial remainder left and bring down the next
    // dividend bit from quotient_reg.
    always_comb begin
        remainder_shift = {
            remainder_reg[WIDTH-1:0],
            quotient_reg[WIDTH-1]
        };

        quotient_next  = quotient_reg << 1;
        remainder_next = remainder_shift;

        if (remainder_shift >= {1'b0, divisor_reg}) begin
            remainder_next = remainder_shift - {1'b0, divisor_reg};
            quotient_next[0] = 1'b1;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            divisor_reg  <= '0;
            quotient_reg <= '0;
            remainder_reg <= '0;
            count_reg    <= '0;

            quotient     <= '0;
            remainder    <= '0;

            busy         <= 1'b0;
            done         <= 1'b0;
            div_by_zero  <= 1'b0;
        end else begin
            // done is a one-cycle pulse.
            done <= 1'b0;

            // A new request is accepted only while idle.
            if (start && !busy) begin
                if (divisor == '0) begin
                    // Project-defined divide-by-zero behavior:
                    // quotient = all ones
                    // remainder = original dividend
                    quotient    <= '1;
                    remainder   <= dividend;
                    div_by_zero <= 1'b1;
                    busy        <= 1'b0;
                    done        <= 1'b1;
                end else begin
                    divisor_reg   <= divisor;
                    quotient_reg  <= dividend;
                    remainder_reg <= '0;
                    count_reg     <= CountW'(WIDTH);

                    div_by_zero <= 1'b0;
                    busy        <= 1'b1;
                end
            end else if (busy) begin
                quotient_reg  <= quotient_next;
                remainder_reg <= remainder_next;

                if (count_reg == 1) begin
                    quotient  <= quotient_next;
                    remainder <= remainder_next[WIDTH-1:0];

                    count_reg <= '0;
                    busy      <= 1'b0;
                    done      <= 1'b1;
                end else begin
                    count_reg <= count_reg - 1'b1;
                end
            end
        end
    end

endmodule
