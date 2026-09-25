module radix2_formal;

    parameter int unsigned WIDTH = 4;

    (* gclk *) reg clk;

    reg rst_n = 1'b0;
    reg start = 1'b0;

    reg [2:0] phase = 3'd0;

    (* anyconst *) reg [WIDTH-1:0] dividend;
    (* anyconst *) reg [WIDTH-1:0] divisor;

    wire busy;
    wire done;
    wire div_by_zero;

    wire [WIDTH-1:0] quotient;
    wire [WIDTH-1:0] remainder;

    radix2_divider #(
        .WIDTH(WIDTH)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),

        .start(start),
        .dividend(dividend),
        .divisor(divisor),

        .busy(busy),
        .done(done),
        .div_by_zero(div_by_zero),

        .quotient(quotient),
        .remainder(remainder)
    );

    // Generate one transaction after reset.
    always @(posedge clk) begin
        case (phase)
            3'd0: begin
                rst_n <= 1'b0;
                start <= 1'b0;
                phase <= 3'd1;
            end

            3'd1: begin
                rst_n <= 1'b1;
                start <= 1'b1;
                phase <= 3'd2;
            end

            default: begin
                rst_n <= 1'b1;
                start <= 1'b0;
            end
        endcase
    end

    wire [2*WIDTH-1:0] product =
        quotient * divisor;

    wire [2*WIDTH:0] recomposed =
        {1'b0, product}
        + {{(WIDTH+1){1'b0}}, remainder};

    wire [2*WIDTH:0] dividend_extended =
        {{(WIDTH+1){1'b0}}, dividend};

    reg f_past_valid = 1'b0;

    always @(posedge clk) begin
        f_past_valid <= 1'b1;

        if (f_past_valid) begin
            // busy and done must never be asserted together.
            assert (!(busy && done));

            if (done) begin
                if (div_by_zero) begin
                    assert (divisor == 0);
                    assert (quotient == {WIDTH{1'b1}});
                    assert (remainder == dividend);
                end else begin
                    assert (divisor != 0);

                    // Fundamental division identity:
                    //
                    // dividend = quotient * divisor + remainder
                    assert (recomposed == dividend_extended);

                    // Canonical unsigned remainder range.
                    assert (remainder < divisor);
                end
            end
        end
    end

    always @(*) begin
    // Reach the exceptional path.
    cover(done && div_by_zero);

    // Reach a successfully completed normal division.
    cover(done && !div_by_zero);

    // Reach a non-trivial normal division.
    cover(
        done &&
        !div_by_zero &&
        divisor > 1 &&
        quotient > 0 &&
        remainder > 0
    );
end
endmodule
