# API Rate Limits - Polymarket Documentation

URL: https://docs.polymarket.com/quickstart/introduction/rate-limits

---

API Rate Limits - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Developer Quickstart

API Rate Limits

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

How Rate Limiting Works

General Rate Limits

Data API Rate Limits

GAMMA API Rate Limits

CLOB API Rate Limits

General CLOB Endpoints

CLOB Market Data

CLOB Ledger Endpoints

CLOB Markets & Pricing

CLOB Authentication

CLOB Trading Endpoints

Other API Rate Limits

​

How Rate Limiting Works

All rate limits are enforced using Cloudflare’s throttling system. When you exceed the maximum configured rate for any endpoint, requests are throttled rather than immediately rejected. This means:

Throttling

: Requests over the limit are delayed/queued rather than dropped

Burst Allowances

: Some endpoints allow short bursts above the sustained rate

Time Windows

: Limits reset based on sliding time windows (e.g., per 10 seconds, per minute)

​

General Rate Limits

Endpoint

Limit

Notes

General Rate Limiting

5000 requests / 10s

Throttle requests over the maximum configured rate

”OK” Endpoint

50 requests / 10s

Throttle requests over the maximum configured rate

​

Data API Rate Limits

Endpoint

Limit

Notes

Data API (General)

200 requests / 10s

Throttle requests over the maximum configured rate

Data API (Alternative)

1200 requests / 1 minute

10 minutes block on violation

Data API

/trades

75 requests / 10s

Throttle requests over the maximum configured rate

Data API “OK” Endpoint

10 requests / 10s

Throttle requests over the maximum configured rate

​

GAMMA API Rate Limits

Endpoint

Limit

Notes

GAMMA (General)

750 requests / 10s

Throttle requests over the maximum configured rate

GAMMA Get Comments

100 requests / 10s

Throttle requests over the maximum configured rate

GAMMA

/events

100 requests / 10s

Throttle requests over the maximum configured rate

GAMMA

/markets

125 requests / 10s

Throttle requests over the maximum configured rate

GAMMA

/markets

/events listing

100 requests / 10s

Throttle requests over the maximum configured rate

GAMMA Tags

100 requests / 10s

Throttle requests over the maximum configured rate

GAMMA Search

300 requests / 10s

Throttle requests over the maximum configured rate

​

CLOB API Rate Limits

​

General CLOB Endpoints

Endpoint

Limit

Notes

CLOB (General)

5000 requests / 10s

Throttle requests over the maximum configured rate

CLOB GET Balance Allowance

125 requests / 10s

Throttle requests over the maximum configured rate

CLOB UPDATE Balance Allowance

20 requests / 10s

Throttle requests over the maximum configured rate

​

CLOB Market Data

Endpoint

Limit

Notes

CLOB

/book

200 requests / 10s

Throttle requests over the maximum configured rate

CLOB

/books

80 requests / 10s

Throttle requests over the maximum configured rate

CLOB

/price

200 requests / 10s

Throttle requests over the maximum configured rate

CLOB

/prices

80 requests / 10s

Throttle requests over the maximum configured rate

CLOB

/midprice

200 requests / 10s

Throttle requests over the maximum configured rate

CLOB

/midprices

80 requests / 10s

Throttle requests over the maximum configured rate

​

CLOB Ledger Endpoints

Endpoint

Limit

Notes

CLOB Ledger (

/trades

/orders

/notifications

/order

)

300 requests / 10s

Throttle requests over the maximum configured rate

CLOB Ledger

/data/orders

150 requests / 10s

Throttle requests over the maximum configured rate

CLOB Ledger

/data/trades

150 requests / 10s

Throttle requests over the maximum configured rate

CLOB

/notifications

125 requests / 10s

Throttle requests over the maximum configured rate

​

CLOB Markets & Pricing

Endpoint

Limit

Notes

CLOB Price History

100 requests / 10s

Throttle requests over the maximum configured rate

CLOB Markets

250 requests / 10s

Throttle requests over the maximum configured rate

CLOB Market Tick Size

50 requests / 10s

Throttle requests over the maximum configured rate

CLOB

markets/0x

50 requests / 10s

Throttle requests over the maximum configured rate

CLOB

/markets

listing

100 requests / 10s

Throttle requests over the maximum configured rate

​

CLOB Authentication

Endpoint

Limit

Notes

CLOB API Keys

50 requests / 10s

Throttle requests over the maximum configured rate

​

CLOB Trading Endpoints

Endpoint

Limit

Notes

CLOB POST

/order

2400 requests / 10s (240/s)

BURST - Throttle requests over the maximum configured rate

CLOB POST

/order

24000 requests / 10 minutes (40/s)

Throttle requests over the maximum configured rate

CLOB DELETE

/order

2400 requests / 10s (240/s)

BURST - Throttle requests over the maximum configured rate

CLOB DELETE

/order

24000 requests / 10 minutes (40/s)

Throttle requests over the maximum configured rate

CLOB POST

/orders

800 requests / 10s (80/s)

BURST - Throttle requests over the maximum configured rate

CLOB POST

/orders

12000 requests / 10 minutes (20/s)

Throttle requests over the maximum configured rate

CLOB DELETE

/orders

800 requests / 10s (80/s)

BURST - Throttle requests over the maximum configured rate

CLOB DELETE

/orders

12000 requests / 10 minutes (20/s)

Throttle requests over the maximum configured rate

CLOB DELETE

/cancel-all

200 requests / 10s (20/s)

BURST - Throttle requests over the maximum configured rate

CLOB DELETE

/cancel-all

3000 requests / 10 minutes (5/s)

Throttle requests over the maximum configured rate

CLOB DELETE

/cancel-market-orders

800 requests / 10s (80/s)

BURST - Throttle requests over the maximum configured rate

CLOB DELETE

/cancel-market-orders

12000 requests / 10 minutes (20/s)

Throttle requests over the maximum configured rate

​

Other API Rate Limits

Endpoint

Limit

Notes

RELAYER

/submit

15 requests / 1 minute

Throttle requests over the maximum configured rate

User PNL API

100 requests / 10s

Throttle requests over the maximum configured rate

Glossary

Endpoints

⌘

I