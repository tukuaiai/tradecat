# Liquidity Rewards - Polymarket Documentation

URL: https://docs.polymarket.com/developers/rewards/overview

---

Liquidity Rewards - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Rewards

Liquidity Rewards

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

Overview

Methodology

Equations

Steps

​

Overview

By posting resting limit orders, liquidity providers (makers) are automatically eligible for Polymarket’s incentive program. The overall goal of this program is to catalyze a healthy, liquid marketplace. We can further define this as creating incentives that:

Catalyze liquidity across all markets

Encourage liquidity throughout a market’s entire lifecycle

Motivate passive, balanced quoting tight to a market’s mid-point

Encourages trading activity

Discourages blatantly exploitative behaviors

This program is heavily inspired by dYdX’s liquidity provider rewards which you can read more about

here

. In fact, the incentive methodology is essentially a copy of dYdX’s successful methodology but with some adjustments including specific adaptations for binary contract markets with distinct books, no staking mechanic a slightly modified order utility-relative depth function and reward amounts isolated per market. Rewards are distributed directly to the maker’s addresses daily at midnight UTC.

​

Methodology

Polymarket liquidity providers will be rewarded based on a formula that rewards participation in markets (complementary consideration!), boosts two-sided depth (single-sided orders still score), and spread (vs. mid-market, adjusted for the size cutoff!). Each market still configure a max spread and min size cutoff within which orders are considered the average of rewards earned is determined by the relative share of each participant’s Q

n

in market m.

Variable

Description

$

order position scoring function

v

max spread from midpoint (in cents)

s

spread from size-cutoff-adjusted midpoint

b

in-game multiplier

m

market

m’

market complement (i.e NO if m = YES)

n

trader index

u

sample index

c

scaling factor (currently 3.0 on all markets)

Q

ne

point total for book one for a sample

Q

no

point total for book two for a sample

Spread%

distance from midpoint (bps or relative) for order n in market m

BidSize

share-denominated quantity of bid

AskSize

share-denominated quantity of ask

​

Equations

Equation 1:

S

(

v

,

s

)

=

(

v

−

s

v

)

2

⋅

b

S(v,s)= (\frac{v-s}{v})^2 \cdot b

S

(

v

,

s

)

=

(

v

v

−

s

​

)

2

⋅

b

Equation 2:

Q

o

n

e

=

S

(

v

,

S

p

r

e

a

d

m

1

)

⋅

B

i

d

S

i

z

e

m

1

+

S

(

v

,

S

p

r

e

a

d

m

2

)

⋅

B

i

d

S

i

z

e

m

2

+

…

Q_{one}= S(v,Spread_{m_1}) \cdot BidSize_{m_1} + S(v,Spread_{m_2}) \cdot BidSize_{m_2} + \dots

Q

o

n

e

​

=

S

(

v

,

Sp

re

a

d

m

1

​

​

)

⋅

B

i

d

S

i

z

e

m

1

​

​

+

S

(

v

,

Sp

re

a

d

m

2

​

​

)

⋅

B

i

d

S

i

z

e

m

2

​

​

+

…

+

S

(

v

,

S

p

r

e

a

d

m

1

′

)

⋅

A

s

k

S

i

z

e

m

1

′

+

S

(

v

,

S

p

r

e

a

d

m

2

′

)

⋅

A

s

k

S

i

z

e

m

2

′

+ S(v, Spread_{m^\prime_1}) \cdot AskSize_{m^\prime_1} + S(v, Spread_{m^\prime_2}) \cdot AskSize_{m^\prime_2}

+

S

(

v

,

Sp

re

a

d

m

1

′

​

​

)

⋅

A

s

k

S

i

z

e

m

1

′

​

​

+

S

(

v

,

Sp

re

a

d

m

2

′

​

​

)

⋅

A

s

k

S

i

z

e

m

2

′

​

​

Equation 3:

Q

t

w

o

=

S

(

v

,

S

p

r

e

a

d

m

1

)

⋅

A

s

k

S

i

z

e

m

1

+

S

(

v

,

S

p

r

e

a

d

m

2

)

⋅

A

s

k

S

i

z

e

m

2

+

…

Q_{two}= S(v,Spread_{m_1}) \cdot AskSize_{m_1} + S(v,Spread_{m_2}) \cdot AskSize_{m_2} + \dots

Q

tw

o

​

=

S

(

v

,

Sp

re

a

d

m

1

​

​

)

⋅

A

s

k

S

i

z

e

m

1

​

​

+

S

(

v

,

Sp

re

a

d

m

2

​

​

)

⋅

A

s

k

S

i

z

e

m

2

​

​

+

…

+

S

(

v

,

S

p

r

e

a

d

m

1

′

)

⋅

B

i

d

S

i

z

e

m

1

′

+

S

(

v

,

S

p

r

e

a

d

m

2

′

)

⋅

B

i

d

S

i

z

e

m

2

′

+ S(v, Spread_{m^\prime_1}) \cdot BidSize_{m^\prime_1} + S(v, Spread_{m^\prime_2}) \cdot BidSize_{m^\prime_2}

+

S

(

v

,

Sp

re

a

d

m

1

′

​

​

)

⋅

B

i

d

S

i

z

e

m

1

′

​

​

+

S

(

v

,

Sp

re

a

d

m

2

′

​

​

)

⋅

B

i

d

S

i

z

e

m

2

′

​

​

Equation 4:

Equation 4a:

If midpoint is in range [0.10,0.90] allow single sided liq to score:

Q

min

⁡

=

max

⁡

(

min

⁡

(

Q

o

n

e

,

Q

t

w

o

)

,

max

⁡

(

Q

o

n

e

/

c

,

Q

t

w

o

/

c

)

)

Q_{\min} = \max(\min({Q_{one}, Q_{two}}), \max(Q_{one}/c, Q_{two}/c))

Q

m

i

n

​

=

max

(

min

(

Q

o

n

e

​

,

Q

tw

o

​

)

,

max

(

Q

o

n

e

​

/

c

,

Q

tw

o

​

/

c

))

Equation 4b:

If midpoint is in either range [0,0.10) or (.90,1.0] require liq to be double sided to score:

Q

min

⁡

=

min

⁡

(

Q

o

n

e

,

Q

t

w

o

)

Q_{\min} = \min({Q_{one}, Q_{two}})

Q

m

i

n

​

=

min

(

Q

o

n

e

​

,

Q

tw

o

​

)

Equation 5:

Q

n

o

r

m

a

l

=

Q

m

i

n

∑

n

=

1

N

(

Q

m

i

n

)

n

Q_{normal} = \frac{Q_{min}}{\sum_{n=1}^{N}{(Q_{min})_n}}

Q

n

or

ma

l

​

=

∑

n

=

1

N

​

(

Q

min

​

)

n

​

Q

min

​

​

Equation 6:

Q

e

p

o

c

h

=

∑

u

=

1

10

,

080

(

Q

n

o

r

m

a

l

)

u

Q_{epoch} = \sum_{u=1}^{10,080}{(Q_{normal})_u}

Q

e

p

oc

h

​

=

∑

u

=

1

10

,

080

​

(

Q

n

or

ma

l

​

)

u

​

Equation 7:

Q

f

i

n

a

l

=

Q

e

p

o

c

h

∑

n

=

1

N

(

Q

e

p

o

c

h

)

n

Q_{final}=\frac{Q_{epoch}}{\sum_{n=1}^{N}{(Q_{epoch})_n}}

Q

f

ina

l

​

=

∑

n

=

1

N

​

(

Q

e

p

oc

h

​

)

n

​

Q

e

p

oc

h

​

​

​

Steps

Quadratic scoring rule for an order based on position between the adjusted midpoint and the minimum qualifying spread

Calculate first market side score. Assume a trader has the following open orders:

100Q bid on m @0.49 (adjusted midpoint is 0.50 then spread of this order is 0.01 or 1c)

200Q bid on m @0.48

100Q ask on m’ @0.51

and assume an adjusted market midpoint of 0.50 and maxSpread config of 3c for both m and m’. Then the trader’s score is:

Q

n

e

=

(

(

3

−

1

)

3

)

2

⋅

100

+

(

(

3

−

2

)

3

)

2

⋅

200

+

(

(

3

−

1

)

3

)

2

⋅

100

Q_{ne} = \left( \frac{(3-1)}{3} \right)^2 \cdot 100 + \left( \frac{(3-2)}{3} \right)^2 \cdot 200 + \left( \frac{(3-1)}{3} \right)^2 \cdot 100

Q

n

e

​

=

(

3

(

3

−

1

)

​

)

2

⋅

100

+

(

3

(

3

−

2

)

​

)

2

⋅

200

+

(

3

(

3

−

1

)

​

)

2

⋅

100

Q

n

e

Q_{ne}

Q

n

e

​

is calculated every minute using random sampling

Calculate second market side score. Assume a trader has the following open orders:

100Q bid on m @0.485

100Q bid on m’ @0.48

200Q ask on m’ @0.505

and assume an adjusted market midpoint of 0.50 and maxSpread config of 3c for both m and m’. Then the trader’s score is:

Q

n

o

=

(

(

3

−

1.5

)

3

)

2

⋅

100

+

(

(

3

−

2

)

3

)

2

⋅

100

+

(

(

3

−

.

5

)

3

)

2

⋅

200

Q_{no} = \left( \frac{(3-1.5)}{3} \right)^2 \cdot 100 + \left( \frac{(3-2)}{3} \right)^2 \cdot 100 + \left( \frac{(3-.5)}{3} \right)^2 \cdot 200

Q

n

o

​

=

(

3

(

3

−

1.5

)

​

)

2

⋅

100

+

(

3

(

3

−

2

)

​

)

2

⋅

100

+

(

3

(

3

−

.5

)

​

)

2

⋅

200

Q

n

o

Q_{no}

Q

n

o

​

is calculated every minute using random sampling

Boosts 2-sided liquidity by taking the minimum of

Q

n

e

Q_{ne}

Q

n

e

​

and

Q

n

o

Q_{no}

Q

n

o

​

, and rewards 1-side liquidity at a reduced rate (divided by c)

Calculated every minute

Q

n

o

r

m

a

l

Q_{normal}

Q

n

or

ma

l

​

is the

Q

m

i

n

Q_{min}

Q

min

​

of a market maker divided by the sum of all the

Q

m

i

n

Q_{min}

Q

min

​

of other market makers in a given sample

Q

e

p

o

c

h

Q_{epoch}

Q

e

p

oc

h

​

is the sum of all

Q

n

o

r

m

a

l

Q_{normal}

Q

n

or

ma

l

​

for a trader in a given epoch

Q

f

i

n

a

l

Q_{final}

Q

f

ina

l

​

normalizes

Q

e

p

o

c

h

Q_{epoch}

Q

e

p

oc

h

​

by dividing it by the sum of all other market maker’s

Q

e

p

o

c

h

Q_{epoch}

Q

e

p

oc

h

​

in a given epoch this value is multiplied by the rewards available for the market to get a trader’s reward

Both min_incentive_size and max_incentive_spread can be fetched alongside full market objects via both the CLOB API and Markets API. Reward allocations for an epoch can be fetched via the Markets API.

Resolution

Overview

⌘

I