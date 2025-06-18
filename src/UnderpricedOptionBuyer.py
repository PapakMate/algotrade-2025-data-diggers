"""
UnderpricedOptionBuyer.py
---------------
Minimalist options-buying bot submitted by *Data Diggers* for the
AlgoTrade 2025 hackathon.

Key idea
--------
Continuously compare an option's **intrinsic value** to its best ask.
If intrinsic × α (`multiplier`) exceeds the ask, submit a 1-lot buy order.

    • α ∈ [0.85 … 0.95]  - tuned manually during rounds  
    • No Greeks / IV     - speed > theory in this exchange micro-structure  
    • Single-pass loop   - lower latency than richer models

For exhibition only — not hardened for live trading.
"""

import asyncio
import json
import argparse
import websockets


# Pre-formatted JSON avoids costly dict→str conversion on the hot path.
ORDER_TEMPLATE = (
    '{{"type": "add_order", "user_request_id": "{}", "instrument_id": "{}", '
    '"price": {}, "expiry": {}, "side": "{}", "quantity": {}}}'
)


class UnderpricedOptionBuyer:
    """
    Stream-based arbitrageur.

    Parameters
    ----------
    uri : str
        WebSocket endpoint (without `team_secret` query string).
    team_secret : str
        Auth token issued by organisers.
    multiplier : float
        α in the README; <1 makes the bot conservative.
    reconnect_delay : float
        Seconds to wait before reconnect attempts (unused here — process
        exits on abnormal close so a supervisor script can restart it).

    Notes
    -----
    • `underlyings` cache keeps the latest closing price per symbol.  
    • Only `market_data_update` messages are handled for maximal throughput.  
    """

    def __init__(self, uri, team_secret, multiplier, reconnect_delay):
        self.uri = f"{uri}?team_secret={team_secret}"
        self.ws = None
        self.order_id = 0
        self.underlyings = {}
        self.multiplier = multiplier
        self.reconnect_delay = reconnect_delay

    # ------------------------------------------------------------------ #
    # Utility                                                             #
    # ------------------------------------------------------------------ #
    def next_id(self):
        """Return a zero-padded client request ID as required by the exchange."""
        self.order_id += 1
        return str(self.order_id).zfill(10)

    # ------------------------------------------------------------------ #
    # Connection management                                               #
    # ------------------------------------------------------------------ #
    async def connect(self):
        """
        Persistent WebSocket connection.

        Runs `receive_loop` indefinitely; exits on abnormal close so the shell
        (or container) can decide whether to restart the process.
        """
        while True:
            try:
                self.ws = await websockets.connect(self.uri)
                print("Connected to WebSocket")
                await self.receive_loop()
            except websockets.exceptions.ConnectionClosedError as e:
                print("Connection closed unexpectedly:", e)
                exit(1)  # Let external supervisor handle the restart

    # ------------------------------------------------------------------ #
    # Streaming loop                                                      #
    # ------------------------------------------------------------------ #
    async def receive_loop(self):
        """Consume messages; delegate market-data handling."""
        try:
            async for msg in self.ws:
                try:
                    data = json.loads(msg)
                    if data.get("type") == "market_data_update":
                        await self.handle_market_data(data)
                except Exception as e:
                    # Swallow parse/logic errors; keep the stream alive.
                    print("Error processing message:", e)
        except websockets.exceptions.ConnectionClosedError as ce:
            print("Receive loop: connection closed:", ce)

    # ------------------------------------------------------------------ #
    # Trading logic                                                       #
    # ------------------------------------------------------------------ #
    async def handle_market_data(self, data):
        """
        One-pass handler.

        Pipeline
        --------
        1. Update `underlyings` with last close price.  
        2. Iterate over option order-books:  
           * skip if no asks → cannot buy  
           * parse naming convention `$<SYM>_<type>_<strike>_<expiry>`  
        3. Compute intrinsic × α and fire a buy if edge exists.
        """

        # 1⃣  Cache latest underlying prices
        for symbol, candles in data.get("candles", {}).get("untradeable", {}).items():
            if candles and "close" in candles[-1]:
                self.underlyings[symbol.lstrip("$")] = candles[-1]["close"]

        # 2⃣  Scan option books
        for instr, ob in data.get("orderbook_depths", {}).items():
            if "call" not in instr and "put" not in instr:
                continue                    # Non-option instrument
            if not ob.get("asks"):
                continue                    # Nothing to buy

            parts = instr.lstrip("$").split("_")
            if len(parts) != 4:
                continue                    # Unexpected naming

            symbol, opt_type, strike_str, expiry_str = parts
            try:
                strike = int(strike_str)
                expiry = int(expiry_str)    # Unused; kept from round 2 filtering
                ask_price = min(int(k) for k in ob["asks"])
            except ValueError:
                continue                    # Bad data → skip

            if symbol not in self.underlyings:
                continue                    # No spot price yet

            spot = self.underlyings[symbol]

            # 3⃣  Compute intrinsic × α
            if opt_type == "call":
                theo_price = (spot - strike) * self.multiplier
            elif opt_type == "put":
                theo_price = (strike - spot) * self.multiplier
            else:
                continue

            # If edge positive → fire 1-lot buy
            if theo_price > ask_price:
                await self.place_order(instr, ask_price, "bid")

    # ------------------------------------------------------------------ #
    # Order submission                                                    #
    # ------------------------------------------------------------------ #
    async def place_order(self, instrument_id, price, side):
        """Submit a single order (always 'bid' in current logic)."""
        message = ORDER_TEMPLATE.format(
            self.next_id(), instrument_id, price, 99999999, side, 1
        )
        await self.ws.send(message)


# -------------------------------------------------------------------------- #
# CLI                                                                        #
# -------------------------------------------------------------------------- #
# Usage: python UnderpricedOptionBuyer.py [multiplier] [reconnect_delay]
async def main():
    """
    Examples
    --------
    • python UnderpricedOptionBuyer.py              # α = 0.85, delay = 0.1 s  
    • python UnderpricedOptionBuyer.py 0.9 0.05
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "multiplier",
        type=float,
        nargs="?",
        default=0.85,
        help="α multiplier for intrinsic price (default: 0.85)",
    )
    parser.add_argument(
        "reconnect_delay",
        type=float,
        nargs="?",
        default=0.1,
        help="Reconnect delay in seconds (default: 0.1)",
    )
    args = parser.parse_args()

    bot = UnderpricedOptionBuyer(
        uri="ws://192.168.100.10:9001/trade",
        team_secret="84d94e4d-2d00-4514-adc1-a1de4a8f2209",
        multiplier=args.multiplier,
        reconnect_delay=args.reconnect_delay,
    )
    await bot.connect()


if __name__ == "__main__":
    asyncio.run(main())
