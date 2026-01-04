# Market Channel - Polymarket Documentation

URL: https://docs.polymarket.com/developers/CLOB/websocket/market-channel

---

Market Channel - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Websocket

Market Channel

User Guide

For Developers

Changelog

Polymarket

Discord Community

Twitter

Developer Quickstart

Developer Quickstart

Your First Order

Glossary

API Rate Limits

Endpoints

Central Limit Order Book

CLOB Introduction

Status

Clients

Authentication

CLOB Requests

Orderbook

Pricing

Spreads

Order Manipulation

Orders Overview

Place Single Order

Place Multiple Orders (Batching)

Get Order

Get Active Orders

Check Order Reward Scoring

Cancel Orders(s)

Onchain Order Info

Trades

Trades Overview

Get Trades

Websocket

WSS Overview

WSS Quickstart

WSS Authentication

User Channel

Market Channel

Real Time Data Stream

RTDS Overview

RTDS Crypto Prices

RTDS Comments

Gamma Structure

Overview

Gamma Structure

Fetching Markets

Gamma Endpoints

Health

Sports

Tags

Events

Markets

Series

Comments

Search

Data-API

Health

Core

Misc

Subgraph

Overview

Resolution

Resolution

Rewards

Liquidity Rewards

Conditional Token Frameworks

Overview

Splitting USDC

Merging Tokens

Reedeeming Tokens

Deployment and Additional Information

Proxy Wallets

Proxy wallet

Negative Risk

Overview

On this page

Book Message

Structure

price_change Message

Structure

tick_size_change Message

Structure

last_trade_price Message

Public channel for updates related to market updates (level 2 price data).

SUBSCRIBE

<wss-channel> market

​

Book Message

Emitted When:

First subscribed to a market

When there is a trade that affects the book

​

Structure

Name

Type

Description

event_type

string

”book”

asset_id

string

asset ID (token ID)

market

string

condition ID of market

timestamp

string

unix timestamp the current book generation in milliseconds (1/1,000 second)

hash

string

hash summary of the orderbook content

buys

OrderSummary[]

list of type (size, price) aggregate book levels for buys

sells

OrderSummary[]

list of type (size, price) aggregate book levels for sells

Where a

OrderSummary

object is of the form:

Name

Type

Description

price

string

size available at that price level

size

string

price of the orderbook level

Response

Copy

Ask AI

{

"event_type"

:

"book"

,

"asset_id"

:

"65818619657568813474341868652308942079804919287380422192892211131408793125422"

,

"market"

:

"0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af"

,

"bids"

: [

{

"price"

:

".48"

,

"size"

:

"30"

},

{

"price"

:

".49"

,

"size"

:

"20"

},

{

"price"

:

".50"

,

"size"

:

"15"

}

],

"asks"

: [

{

"price"

:

".52"

,

"size"

:

"25"

},

{

"price"

:

".53"

,

"size"

:

"60"

},

{

"price"

:

".54"

,

"size"

:

"10"

}

],

"timestamp"

:

"123456789000"

,

"hash"

:

"0x0...."

}

​

price_change Message

⚠️ Breaking Change Notice:

The price_change message schema will be updated on September 15, 2025 at 11 PM UTC. Please see the

migration guide

for details.

Emitted When:

A new order is placed

An order is cancelled

​

Structure

Name

Type

Description

event_type

string

”price_change”

market

string

condition ID of market

price_changes

PriceChange[]

array of price change objects

timestamp

string

unix timestamp in milliseconds

Where a

PriceChange

object is of the form:

Name

Type

Description

asset_id

string

asset ID (token ID)

price

string

price level affected

size

string

new aggregate size for price level

side

string

”BUY” or “SELL”

hash

string

hash of the order

best_bid

string

current best bid price

best_ask

string

current best ask price

Response

Copy

Ask AI

{

"market"

:

"0x5f65177b394277fd294cd75650044e32ba009a95022d88a0c1d565897d72f8f1"

,

"price_changes"

: [

{

"asset_id"

:

"71321045679252212594626385532706912750332728571942532289631379312455583992563"

,

"price"

:

"0.5"

,

"size"

:

"200"

,

"side"

:

"BUY"

,

"hash"

:

"56621a121a47ed9333273e21c83b660cff37ae50"

,

"best_bid"

:

"0.5"

,

"best_ask"

:

"1"

},

{

"asset_id"

:

"52114319501245915516055106046884209969926127482827954674443846427813813222426"

,

"price"

:

"0.5"

,

"size"

:

"200"

,

"side"

:

"SELL"

,

"hash"

:

"1895759e4df7a796bf4f1c5a5950b748306923e2"

,

"best_bid"

:

"0"

,

"best_ask"

:

"0.5"

}

],

"timestamp"

:

"1757908892351"

,

"event_type"

:

"price_change"

}

​

tick_size_change Message

Emitted When:

The minimum tick size of the market changes. This happens when the book’s price reaches the limits: price > 0.96 or price < 0.04

​

Structure

Name

Type

Description

event_type

string

”price_change”

asset_id

string

asset ID (token ID)

market

string

condition ID of market

old_tick_size

string

previous minimum tick size

new_tick_size

string

current minimum tick size

side

string

buy/sell

timestamp

string

time of event

Response

Copy

Ask AI

{

"event_type"

:

"tick_size_change"

,

"asset_id"

:

"65818619657568813474341868652308942079804919287380422192892211131408793125422"

,

\

"market"

:

"0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af"

,

"old_tick_size"

:

"0.01"

,

"new_tick_size"

:

"0.001"

,

"timestamp"

:

"100000000"

}

​

last_trade_price Message

Emitted When:

When a maker and taker order is matched creating a trade event.

Response

Copy

Ask AI

{

"asset_id"

:

"114122071509644379678018727908709560226618148003371446110114509806601493071694"

,

"event_type"

:

"last_trade_price"

,

"fee_rate_bps"

:

"0"

,

"market"

:

"0x6a67b9d828d53862160e470329ffea5246f338ecfffdf2cab45211ec578b0347"

,

"price"

:

"0.456"

,

"side"

:

"BUY"

,

"size"

:

"219.217767"

,

"timestamp"

:

"1750428146322"

}

User Channel

RTDS Overview

⌘

I