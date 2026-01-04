# CLOB Introduction - Polymarket Documentation

URL: https://docs.polymarket.com/developers/CLOB/introduction

---

CLOB Introduction - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Central Limit Order Book

CLOB Introduction

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

System

API

Security

Fees

Schedule

Overview

Additional Resources

Welcome to the Polymarket Order Book API! This documentation provides overviews, explanations, examples, and annotations to simplify interaction with the order book. The following sections detail the Polymarket Order Book and the API usage.

​

System

Polymarket’s Order Book, or CLOB (Central Limit Order Book), is hybrid-decentralized. It includes an operator for off-chain matching/ordering, with settlement executed on-chain, non-custodially, via signed order messages.

The exchange uses a custom Exchange contract facilitating atomic swaps between binary Outcome Tokens (CTF ERC1155 assets and ERC20 PToken assets) and collateral assets (ERC20), following signed limit orders. Designed for binary markets, the contract enables complementary tokens to match across a unified order book.

Orders are EIP712-signed structured data. Matched orders have one maker and one or more takers, with price improvements benefiting the taker. The operator handles off-chain order management and submits matched trades to the blockchain for on-chain execution.

​

API

The Polymarket Order Book API enables market makers and traders to programmatically manage market orders. Orders of any amount can be created, listed, fetched, or read from the market order books. Data includes all available markets, market prices, and order history via REST and WebSocket endpoints.

​

Security

Polymarket’s Exchange contract has been audited by Chainsecurity (

View Audit

).

The operator’s privileges are limited to order matching, non-censorship, and ensuring correct ordering. Operators can’t set prices or execute unauthorized trades. Users can cancel orders on-chain independently if trust issues arise.

​

Fees

​

Schedule

Subject to change

Volume Level

Maker Fee Base Rate (bps)

Taker Fee Base Rate (bps)

>0 USDC

0

0

​

Overview

Fees apply symmetrically in output assets (proceeds). This symmetry ensures fairness and market integrity. Fees are calculated differently depending on whether you are buying or selling:

Selling outcome tokens (base) for collateral (quote):

f

e

e

Q

u

o

t

e

=

b

a

s

e

R

a

t

e

×

min

⁡

(

p

r

i

c

e

,

1

−

p

r

i

c

e

)

×

s

i

z

e

feeQuote = baseRate \times \min(price, 1 - price) \times size

f

ee

Q

u

o

t

e

=

ba

se

R

a

t

e

×

min

(

p

r

i

ce

,

1

−

p

r

i

ce

)

×

s

i

ze

Buying outcome tokens (base) with collateral (quote):

f

e

e

B

a

s

e

=

b

a

s

e

R

a

t

e

×

min

⁡

(

p

r

i

c

e

,

1

−

p

r

i

c

e

)

×

s

i

z

e

p

r

i

c

e

feeBase = baseRate \times \min(price, 1 - price) \times \frac{size}{price}

f

ee

B

a

se

=

ba

se

R

a

t

e

×

min

(

p

r

i

ce

,

1

−

p

r

i

ce

)

×

p

r

i

ce

s

i

ze

​

​

Additional Resources

Exchange contract source code

Exchange contract documentation

Endpoints

Status

⌘

I