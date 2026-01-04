# List series - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/series/list-series

---

List series - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Series

List series

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

GET

List series

GET

Get series by id

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

List series

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/series

200

Copy

Ask AI

[

{

"id"

:

"<string>"

,

"ticker"

:

"<string>"

,

"slug"

:

"<string>"

,

"title"

:

"<string>"

,

"subtitle"

:

"<string>"

,

"seriesType"

:

"<string>"

,

"recurrence"

:

"<string>"

,

"description"

:

"<string>"

,

"image"

:

"<string>"

,

"icon"

:

"<string>"

,

"layout"

:

"<string>"

,

"active"

:

true

,

"closed"

:

true

,

"archived"

:

true

,

"new"

:

true

,

"featured"

:

true

,

"restricted"

:

true

,

"isTemplate"

:

true

,

"templateVariables"

:

true

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

"<string>"

,

"updatedBy"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"commentsEnabled"

:

true

,

"competitive"

:

"<string>"

,

"volume24hr"

:

123

,

"volume"

:

123

,

"liquidity"

:

123

,

"startDate"

:

"2023-11-07T05:31:56Z"

,

"pythTokenID"

:

"<string>"

,

"cgAssetName"

:

"<string>"

,

"score"

:

123

,

"events"

: [

{

"id"

:

"<string>"

,

"ticker"

:

"<string>"

,

"slug"

:

"<string>"

,

"title"

:

"<string>"

,

"subtitle"

:

"<string>"

,

"description"

:

"<string>"

,

"resolutionSource"

:

"<string>"

,

"startDate"

:

"2023-11-07T05:31:56Z"

,

"creationDate"

:

"2023-11-07T05:31:56Z"

,

"endDate"

:

"2023-11-07T05:31:56Z"

,

"image"

:

"<string>"

,

"icon"

:

"<string>"

,

"active"

:

true

,

"closed"

:

true

,

"archived"

:

true

,

"new"

:

true

,

"featured"

:

true

,

"restricted"

:

true

,

"liquidity"

:

123

,

"volume"

:

123

,

"openInterest"

:

123

,

"sortBy"

:

"<string>"

,

"category"

:

"<string>"

,

"subcategory"

:

"<string>"

,

"isTemplate"

:

true

,

"templateVariables"

:

"<string>"

,

"published_at"

:

"<string>"

,

"createdBy"

:

"<string>"

,

"updatedBy"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"commentsEnabled"

:

true

,

"competitive"

:

123

,

"volume24hr"

:

123

,

"volume1wk"

:

123

,

"volume1mo"

:

123

,

"volume1yr"

:

123

,

"featuredImage"

:

"<string>"

,

"disqusThread"

:

"<string>"

,

"parentEvent"

:

"<string>"

,

"enableOrderBook"

:

true

,

"liquidityAmm"

:

123

,

"liquidityClob"

:

123

,

"negRisk"

:

true

,

"negRiskMarketID"

:

"<string>"

,

"negRiskFeeBips"

:

123

,

"commentCount"

:

123

,

"imageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"iconOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"featuredImageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"subEvents"

: [

"<string>"

],

"markets"

: [

{

"id"

:

"<string>"

,

"question"

:

"<string>"

,

"conditionId"

:

"<string>"

,

"slug"

:

"<string>"

,

"twitterCardImage"

:

"<string>"

,

"resolutionSource"

:

"<string>"

,

"endDate"

:

"2023-11-07T05:31:56Z"

,

"category"

:

"<string>"

,

"ammType"

:

"<string>"

,

"liquidity"

:

"<string>"

,

"sponsorName"

:

"<string>"

,

"sponsorImage"

:

"<string>"

,

"startDate"

:

"2023-11-07T05:31:56Z"

,

"xAxisValue"

:

"<string>"

,

"yAxisValue"

:

"<string>"

,

"denominationToken"

:

"<string>"

,

"fee"

:

"<string>"

,

"image"

:

"<string>"

,

"icon"

:

"<string>"

,

"lowerBound"

:

"<string>"

,

"upperBound"

:

"<string>"

,

"description"

:

"<string>"

,

"outcomes"

:

"<string>"

,

"outcomePrices"

:

"<string>"

,

"volume"

:

"<string>"

,

"active"

:

true

,

"marketType"

:

"<string>"

,

"formatType"

:

"<string>"

,

"lowerBoundDate"

:

"<string>"

,

"upperBoundDate"

:

"<string>"

,

"closed"

:

true

,

"marketMakerAddress"

:

"<string>"

,

"createdBy"

:

123

,

"updatedBy"

:

123

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"closedTime"

:

"<string>"

,

"wideFormat"

:

true

,

"new"

:

true

,

"mailchimpTag"

:

"<string>"

,

"featured"

:

true

,

"archived"

:

true

,

"resolvedBy"

:

"<string>"

,

"restricted"

:

true

,

"marketGroup"

:

123

,

"groupItemTitle"

:

"<string>"

,

"groupItemThreshold"

:

"<string>"

,

"questionID"

:

"<string>"

,

"umaEndDate"

:

"<string>"

,

"enableOrderBook"

:

true

,

"orderPriceMinTickSize"

:

123

,

"orderMinSize"

:

123

,

"umaResolutionStatus"

:

"<string>"

,

"curationOrder"

:

123

,

"volumeNum"

:

123

,

"liquidityNum"

:

123

,

"endDateIso"

:

"<string>"

,

"startDateIso"

:

"<string>"

,

"umaEndDateIso"

:

"<string>"

,

"hasReviewedDates"

:

true

,

"readyForCron"

:

true

,

"commentsEnabled"

:

true

,

"volume24hr"

:

123

,

"volume1wk"

:

123

,

"volume1mo"

:

123

,

"volume1yr"

:

123

,

"gameStartTime"

:

"<string>"

,

"secondsDelay"

:

123

,

"clobTokenIds"

:

"<string>"

,

"disqusThread"

:

"<string>"

,

"shortOutcomes"

:

"<string>"

,

"teamAID"

:

"<string>"

,

"teamBID"

:

"<string>"

,

"umaBond"

:

"<string>"

,

"umaReward"

:

"<string>"

,

"fpmmLive"

:

true

,

"volume24hrAmm"

:

123

,

"volume1wkAmm"

:

123

,

"volume1moAmm"

:

123

,

"volume1yrAmm"

:

123

,

"volume24hrClob"

:

123

,

"volume1wkClob"

:

123

,

"volume1moClob"

:

123

,

"volume1yrClob"

:

123

,

"volumeAmm"

:

123

,

"volumeClob"

:

123

,

"liquidityAmm"

:

123

,

"liquidityClob"

:

123

,

"makerBaseFee"

:

123

,

"takerBaseFee"

:

123

,

"customLiveness"

:

123

,

"acceptingOrders"

:

true

,

"notificationsEnabled"

:

true

,

"score"

:

123

,

"imageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"iconOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"events"

: [

{}

],

"categories"

: [

{

"id"

:

"<string>"

,

"label"

:

"<string>"

,

"parentCategory"

:

"<string>"

,

"slug"

:

"<string>"

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

"<string>"

,

"updatedBy"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

}

],

"tags"

: [

{

"id"

:

"<string>"

,

"label"

:

"<string>"

,

"slug"

:

"<string>"

,

"forceShow"

:

true

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

123

,

"updatedBy"

:

123

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"forceHide"

:

true

,

"isCarousel"

:

true

}

],

"creator"

:

"<string>"

,

"ready"

:

true

,

"funded"

:

true

,

"pastSlugs"

:

"<string>"

,

"readyTimestamp"

:

"2023-11-07T05:31:56Z"

,

"fundedTimestamp"

:

"2023-11-07T05:31:56Z"

,

"acceptingOrdersTimestamp"

:

"2023-11-07T05:31:56Z"

,

"competitive"

:

123

,

"rewardsMinSize"

:

123

,

"rewardsMaxSpread"

:

123

,

"spread"

:

123

,

"automaticallyResolved"

:

true

,

"oneDayPriceChange"

:

123

,

"oneHourPriceChange"

:

123

,

"oneWeekPriceChange"

:

123

,

"oneMonthPriceChange"

:

123

,

"oneYearPriceChange"

:

123

,

"lastTradePrice"

:

123

,

"bestBid"

:

123

,

"bestAsk"

:

123

,

"automaticallyActive"

:

true

,

"clearBookOnStart"

:

true

,

"chartColor"

:

"<string>"

,

"seriesColor"

:

"<string>"

,

"showGmpSeries"

:

true

,

"showGmpOutcome"

:

true

,

"manualActivation"

:

true

,

"negRiskOther"

:

true

,

"gameId"

:

"<string>"

,

"groupItemRange"

:

"<string>"

,

"sportsMarketType"

:

"<string>"

,

"line"

:

123

,

"umaResolutionStatuses"

:

"<string>"

,

"pendingDeployment"

:

true

,

"deploying"

:

true

,

"deployingTimestamp"

:

"2023-11-07T05:31:56Z"

,

"scheduledDeploymentTimestamp"

:

"2023-11-07T05:31:56Z"

,

"rfqEnabled"

:

true

,

"eventStartTime"

:

"2023-11-07T05:31:56Z"

}

],

"series"

: [

{}

],

"categories"

: [

{

"id"

:

"<string>"

,

"label"

:

"<string>"

,

"parentCategory"

:

"<string>"

,

"slug"

:

"<string>"

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

"<string>"

,

"updatedBy"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

}

],

"collections"

: [

{

"id"

:

"<string>"

,

"ticker"

:

"<string>"

,

"slug"

:

"<string>"

,

"title"

:

"<string>"

,

"subtitle"

:

"<string>"

,

"collectionType"

:

"<string>"

,

"description"

:

"<string>"

,

"tags"

:

"<string>"

,

"image"

:

"<string>"

,

"icon"

:

"<string>"

,

"headerImage"

:

"<string>"

,

"layout"

:

"<string>"

,

"active"

:

true

,

"closed"

:

true

,

"archived"

:

true

,

"new"

:

true

,

"featured"

:

true

,

"restricted"

:

true

,

"isTemplate"

:

true

,

"templateVariables"

:

"<string>"

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

"<string>"

,

"updatedBy"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"commentsEnabled"

:

true

,

"imageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"iconOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"headerImageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

}

}

],

"tags"

: [

{

"id"

:

"<string>"

,

"label"

:

"<string>"

,

"slug"

:

"<string>"

,

"forceShow"

:

true

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

123

,

"updatedBy"

:

123

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"forceHide"

:

true

,

"isCarousel"

:

true

}

],

"cyom"

:

true

,

"closedTime"

:

"2023-11-07T05:31:56Z"

,

"showAllOutcomes"

:

true

,

"showMarketImages"

:

true

,

"automaticallyResolved"

:

true

,

"enableNegRisk"

:

true

,

"automaticallyActive"

:

true

,

"eventDate"

:

"<string>"

,

"startTime"

:

"2023-11-07T05:31:56Z"

,

"eventWeek"

:

123

,

"seriesSlug"

:

"<string>"

,

"score"

:

"<string>"

,

"elapsed"

:

"<string>"

,

"period"

:

"<string>"

,

"live"

:

true

,

"ended"

:

true

,

"finishedTimestamp"

:

"2023-11-07T05:31:56Z"

,

"gmpChartMode"

:

"<string>"

,

"eventCreators"

: [

{

"id"

:

"<string>"

,

"creatorName"

:

"<string>"

,

"creatorHandle"

:

"<string>"

,

"creatorUrl"

:

"<string>"

,

"creatorImage"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

}

],

"tweetCount"

:

123

,

"chats"

: [

{

"id"

:

"<string>"

,

"channelId"

:

"<string>"

,

"channelName"

:

"<string>"

,

"channelImage"

:

"<string>"

,

"live"

:

true

,

"startTime"

:

"2023-11-07T05:31:56Z"

,

"endTime"

:

"2023-11-07T05:31:56Z"

}

],

"featuredOrder"

:

123

,

"estimateValue"

:

true

,

"cantEstimate"

:

true

,

"estimatedValue"

:

"<string>"

,

"templates"

: [

{

"id"

:

"<string>"

,

"eventTitle"

:

"<string>"

,

"eventSlug"

:

"<string>"

,

"eventImage"

:

"<string>"

,

"marketTitle"

:

"<string>"

,

"description"

:

"<string>"

,

"resolutionSource"

:

"<string>"

,

"negRisk"

:

true

,

"sortBy"

:

"<string>"

,

"showMarketImages"

:

true

,

"seriesSlug"

:

"<string>"

,

"outcomes"

:

"<string>"

}

],

"spreadsMainLine"

:

123

,

"totalsMainLine"

:

123

,

"carouselMap"

:

"<string>"

,

"pendingDeployment"

:

true

,

"deploying"

:

true

,

"deployingTimestamp"

:

"2023-11-07T05:31:56Z"

,

"scheduledDeploymentTimestamp"

:

"2023-11-07T05:31:56Z"

,

"gameStatus"

:

"<string>"

}

],

"collections"

: [

{

"id"

:

"<string>"

,

"ticker"

:

"<string>"

,

"slug"

:

"<string>"

,

"title"

:

"<string>"

,

"subtitle"

:

"<string>"

,

"collectionType"

:

"<string>"

,

"description"

:

"<string>"

,

"tags"

:

"<string>"

,

"image"

:

"<string>"

,

"icon"

:

"<string>"

,

"headerImage"

:

"<string>"

,

"layout"

:

"<string>"

,

"active"

:

true

,

"closed"

:

true

,

"archived"

:

true

,

"new"

:

true

,

"featured"

:

true

,

"restricted"

:

true

,

"isTemplate"

:

true

,

"templateVariables"

:

"<string>"

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

"<string>"

,

"updatedBy"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"commentsEnabled"

:

true

,

"imageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"iconOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"headerImageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

}

}

],

"categories"

: [

{

"id"

:

"<string>"

,

"label"

:

"<string>"

,

"parentCategory"

:

"<string>"

,

"slug"

:

"<string>"

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

"<string>"

,

"updatedBy"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

}

],

"tags"

: [

{

"id"

:

"<string>"

,

"label"

:

"<string>"

,

"slug"

:

"<string>"

,

"forceShow"

:

true

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

123

,

"updatedBy"

:

123

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"forceHide"

:

true

,

"isCarousel"

:

true

}

],

"commentCount"

:

123

,

"chats"

: [

{

"id"

:

"<string>"

,

"channelId"

:

"<string>"

,

"channelName"

:

"<string>"

,

"channelImage"

:

"<string>"

,

"live"

:

true

,

"startTime"

:

"2023-11-07T05:31:56Z"

,

"endTime"

:

"2023-11-07T05:31:56Z"

}

]

}

]

GET

/

series

Try it

List series

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/series

200

Copy

Ask AI

[

{

"id"

:

"<string>"

,

"ticker"

:

"<string>"

,

"slug"

:

"<string>"

,

"title"

:

"<string>"

,

"subtitle"

:

"<string>"

,

"seriesType"

:

"<string>"

,

"recurrence"

:

"<string>"

,

"description"

:

"<string>"

,

"image"

:

"<string>"

,

"icon"

:

"<string>"

,

"layout"

:

"<string>"

,

"active"

:

true

,

"closed"

:

true

,

"archived"

:

true

,

"new"

:

true

,

"featured"

:

true

,

"restricted"

:

true

,

"isTemplate"

:

true

,

"templateVariables"

:

true

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

"<string>"

,

"updatedBy"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"commentsEnabled"

:

true

,

"competitive"

:

"<string>"

,

"volume24hr"

:

123

,

"volume"

:

123

,

"liquidity"

:

123

,

"startDate"

:

"2023-11-07T05:31:56Z"

,

"pythTokenID"

:

"<string>"

,

"cgAssetName"

:

"<string>"

,

"score"

:

123

,

"events"

: [

{

"id"

:

"<string>"

,

"ticker"

:

"<string>"

,

"slug"

:

"<string>"

,

"title"

:

"<string>"

,

"subtitle"

:

"<string>"

,

"description"

:

"<string>"

,

"resolutionSource"

:

"<string>"

,

"startDate"

:

"2023-11-07T05:31:56Z"

,

"creationDate"

:

"2023-11-07T05:31:56Z"

,

"endDate"

:

"2023-11-07T05:31:56Z"

,

"image"

:

"<string>"

,

"icon"

:

"<string>"

,

"active"

:

true

,

"closed"

:

true

,

"archived"

:

true

,

"new"

:

true

,

"featured"

:

true

,

"restricted"

:

true

,

"liquidity"

:

123

,

"volume"

:

123

,

"openInterest"

:

123

,

"sortBy"

:

"<string>"

,

"category"

:

"<string>"

,

"subcategory"

:

"<string>"

,

"isTemplate"

:

true

,

"templateVariables"

:

"<string>"

,

"published_at"

:

"<string>"

,

"createdBy"

:

"<string>"

,

"updatedBy"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"commentsEnabled"

:

true

,

"competitive"

:

123

,

"volume24hr"

:

123

,

"volume1wk"

:

123

,

"volume1mo"

:

123

,

"volume1yr"

:

123

,

"featuredImage"

:

"<string>"

,

"disqusThread"

:

"<string>"

,

"parentEvent"

:

"<string>"

,

"enableOrderBook"

:

true

,

"liquidityAmm"

:

123

,

"liquidityClob"

:

123

,

"negRisk"

:

true

,

"negRiskMarketID"

:

"<string>"

,

"negRiskFeeBips"

:

123

,

"commentCount"

:

123

,

"imageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"iconOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"featuredImageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"subEvents"

: [

"<string>"

],

"markets"

: [

{

"id"

:

"<string>"

,

"question"

:

"<string>"

,

"conditionId"

:

"<string>"

,

"slug"

:

"<string>"

,

"twitterCardImage"

:

"<string>"

,

"resolutionSource"

:

"<string>"

,

"endDate"

:

"2023-11-07T05:31:56Z"

,

"category"

:

"<string>"

,

"ammType"

:

"<string>"

,

"liquidity"

:

"<string>"

,

"sponsorName"

:

"<string>"

,

"sponsorImage"

:

"<string>"

,

"startDate"

:

"2023-11-07T05:31:56Z"

,

"xAxisValue"

:

"<string>"

,

"yAxisValue"

:

"<string>"

,

"denominationToken"

:

"<string>"

,

"fee"

:

"<string>"

,

"image"

:

"<string>"

,

"icon"

:

"<string>"

,

"lowerBound"

:

"<string>"

,

"upperBound"

:

"<string>"

,

"description"

:

"<string>"

,

"outcomes"

:

"<string>"

,

"outcomePrices"

:

"<string>"

,

"volume"

:

"<string>"

,

"active"

:

true

,

"marketType"

:

"<string>"

,

"formatType"

:

"<string>"

,

"lowerBoundDate"

:

"<string>"

,

"upperBoundDate"

:

"<string>"

,

"closed"

:

true

,

"marketMakerAddress"

:

"<string>"

,

"createdBy"

:

123

,

"updatedBy"

:

123

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"closedTime"

:

"<string>"

,

"wideFormat"

:

true

,

"new"

:

true

,

"mailchimpTag"

:

"<string>"

,

"featured"

:

true

,

"archived"

:

true

,

"resolvedBy"

:

"<string>"

,

"restricted"

:

true

,

"marketGroup"

:

123

,

"groupItemTitle"

:

"<string>"

,

"groupItemThreshold"

:

"<string>"

,

"questionID"

:

"<string>"

,

"umaEndDate"

:

"<string>"

,

"enableOrderBook"

:

true

,

"orderPriceMinTickSize"

:

123

,

"orderMinSize"

:

123

,

"umaResolutionStatus"

:

"<string>"

,

"curationOrder"

:

123

,

"volumeNum"

:

123

,

"liquidityNum"

:

123

,

"endDateIso"

:

"<string>"

,

"startDateIso"

:

"<string>"

,

"umaEndDateIso"

:

"<string>"

,

"hasReviewedDates"

:

true

,

"readyForCron"

:

true

,

"commentsEnabled"

:

true

,

"volume24hr"

:

123

,

"volume1wk"

:

123

,

"volume1mo"

:

123

,

"volume1yr"

:

123

,

"gameStartTime"

:

"<string>"

,

"secondsDelay"

:

123

,

"clobTokenIds"

:

"<string>"

,

"disqusThread"

:

"<string>"

,

"shortOutcomes"

:

"<string>"

,

"teamAID"

:

"<string>"

,

"teamBID"

:

"<string>"

,

"umaBond"

:

"<string>"

,

"umaReward"

:

"<string>"

,

"fpmmLive"

:

true

,

"volume24hrAmm"

:

123

,

"volume1wkAmm"

:

123

,

"volume1moAmm"

:

123

,

"volume1yrAmm"

:

123

,

"volume24hrClob"

:

123

,

"volume1wkClob"

:

123

,

"volume1moClob"

:

123

,

"volume1yrClob"

:

123

,

"volumeAmm"

:

123

,

"volumeClob"

:

123

,

"liquidityAmm"

:

123

,

"liquidityClob"

:

123

,

"makerBaseFee"

:

123

,

"takerBaseFee"

:

123

,

"customLiveness"

:

123

,

"acceptingOrders"

:

true

,

"notificationsEnabled"

:

true

,

"score"

:

123

,

"imageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"iconOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"events"

: [

{}

],

"categories"

: [

{

"id"

:

"<string>"

,

"label"

:

"<string>"

,

"parentCategory"

:

"<string>"

,

"slug"

:

"<string>"

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

"<string>"

,

"updatedBy"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

}

],

"tags"

: [

{

"id"

:

"<string>"

,

"label"

:

"<string>"

,

"slug"

:

"<string>"

,

"forceShow"

:

true

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

123

,

"updatedBy"

:

123

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"forceHide"

:

true

,

"isCarousel"

:

true

}

],

"creator"

:

"<string>"

,

"ready"

:

true

,

"funded"

:

true

,

"pastSlugs"

:

"<string>"

,

"readyTimestamp"

:

"2023-11-07T05:31:56Z"

,

"fundedTimestamp"

:

"2023-11-07T05:31:56Z"

,

"acceptingOrdersTimestamp"

:

"2023-11-07T05:31:56Z"

,

"competitive"

:

123

,

"rewardsMinSize"

:

123

,

"rewardsMaxSpread"

:

123

,

"spread"

:

123

,

"automaticallyResolved"

:

true

,

"oneDayPriceChange"

:

123

,

"oneHourPriceChange"

:

123

,

"oneWeekPriceChange"

:

123

,

"oneMonthPriceChange"

:

123

,

"oneYearPriceChange"

:

123

,

"lastTradePrice"

:

123

,

"bestBid"

:

123

,

"bestAsk"

:

123

,

"automaticallyActive"

:

true

,

"clearBookOnStart"

:

true

,

"chartColor"

:

"<string>"

,

"seriesColor"

:

"<string>"

,

"showGmpSeries"

:

true

,

"showGmpOutcome"

:

true

,

"manualActivation"

:

true

,

"negRiskOther"

:

true

,

"gameId"

:

"<string>"

,

"groupItemRange"

:

"<string>"

,

"sportsMarketType"

:

"<string>"

,

"line"

:

123

,

"umaResolutionStatuses"

:

"<string>"

,

"pendingDeployment"

:

true

,

"deploying"

:

true

,

"deployingTimestamp"

:

"2023-11-07T05:31:56Z"

,

"scheduledDeploymentTimestamp"

:

"2023-11-07T05:31:56Z"

,

"rfqEnabled"

:

true

,

"eventStartTime"

:

"2023-11-07T05:31:56Z"

}

],

"series"

: [

{}

],

"categories"

: [

{

"id"

:

"<string>"

,

"label"

:

"<string>"

,

"parentCategory"

:

"<string>"

,

"slug"

:

"<string>"

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

"<string>"

,

"updatedBy"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

}

],

"collections"

: [

{

"id"

:

"<string>"

,

"ticker"

:

"<string>"

,

"slug"

:

"<string>"

,

"title"

:

"<string>"

,

"subtitle"

:

"<string>"

,

"collectionType"

:

"<string>"

,

"description"

:

"<string>"

,

"tags"

:

"<string>"

,

"image"

:

"<string>"

,

"icon"

:

"<string>"

,

"headerImage"

:

"<string>"

,

"layout"

:

"<string>"

,

"active"

:

true

,

"closed"

:

true

,

"archived"

:

true

,

"new"

:

true

,

"featured"

:

true

,

"restricted"

:

true

,

"isTemplate"

:

true

,

"templateVariables"

:

"<string>"

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

"<string>"

,

"updatedBy"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"commentsEnabled"

:

true

,

"imageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"iconOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"headerImageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

}

}

],

"tags"

: [

{

"id"

:

"<string>"

,

"label"

:

"<string>"

,

"slug"

:

"<string>"

,

"forceShow"

:

true

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

123

,

"updatedBy"

:

123

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"forceHide"

:

true

,

"isCarousel"

:

true

}

],

"cyom"

:

true

,

"closedTime"

:

"2023-11-07T05:31:56Z"

,

"showAllOutcomes"

:

true

,

"showMarketImages"

:

true

,

"automaticallyResolved"

:

true

,

"enableNegRisk"

:

true

,

"automaticallyActive"

:

true

,

"eventDate"

:

"<string>"

,

"startTime"

:

"2023-11-07T05:31:56Z"

,

"eventWeek"

:

123

,

"seriesSlug"

:

"<string>"

,

"score"

:

"<string>"

,

"elapsed"

:

"<string>"

,

"period"

:

"<string>"

,

"live"

:

true

,

"ended"

:

true

,

"finishedTimestamp"

:

"2023-11-07T05:31:56Z"

,

"gmpChartMode"

:

"<string>"

,

"eventCreators"

: [

{

"id"

:

"<string>"

,

"creatorName"

:

"<string>"

,

"creatorHandle"

:

"<string>"

,

"creatorUrl"

:

"<string>"

,

"creatorImage"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

}

],

"tweetCount"

:

123

,

"chats"

: [

{

"id"

:

"<string>"

,

"channelId"

:

"<string>"

,

"channelName"

:

"<string>"

,

"channelImage"

:

"<string>"

,

"live"

:

true

,

"startTime"

:

"2023-11-07T05:31:56Z"

,

"endTime"

:

"2023-11-07T05:31:56Z"

}

],

"featuredOrder"

:

123

,

"estimateValue"

:

true

,

"cantEstimate"

:

true

,

"estimatedValue"

:

"<string>"

,

"templates"

: [

{

"id"

:

"<string>"

,

"eventTitle"

:

"<string>"

,

"eventSlug"

:

"<string>"

,

"eventImage"

:

"<string>"

,

"marketTitle"

:

"<string>"

,

"description"

:

"<string>"

,

"resolutionSource"

:

"<string>"

,

"negRisk"

:

true

,

"sortBy"

:

"<string>"

,

"showMarketImages"

:

true

,

"seriesSlug"

:

"<string>"

,

"outcomes"

:

"<string>"

}

],

"spreadsMainLine"

:

123

,

"totalsMainLine"

:

123

,

"carouselMap"

:

"<string>"

,

"pendingDeployment"

:

true

,

"deploying"

:

true

,

"deployingTimestamp"

:

"2023-11-07T05:31:56Z"

,

"scheduledDeploymentTimestamp"

:

"2023-11-07T05:31:56Z"

,

"gameStatus"

:

"<string>"

}

],

"collections"

: [

{

"id"

:

"<string>"

,

"ticker"

:

"<string>"

,

"slug"

:

"<string>"

,

"title"

:

"<string>"

,

"subtitle"

:

"<string>"

,

"collectionType"

:

"<string>"

,

"description"

:

"<string>"

,

"tags"

:

"<string>"

,

"image"

:

"<string>"

,

"icon"

:

"<string>"

,

"headerImage"

:

"<string>"

,

"layout"

:

"<string>"

,

"active"

:

true

,

"closed"

:

true

,

"archived"

:

true

,

"new"

:

true

,

"featured"

:

true

,

"restricted"

:

true

,

"isTemplate"

:

true

,

"templateVariables"

:

"<string>"

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

"<string>"

,

"updatedBy"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"commentsEnabled"

:

true

,

"imageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"iconOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"headerImageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

}

}

],

"categories"

: [

{

"id"

:

"<string>"

,

"label"

:

"<string>"

,

"parentCategory"

:

"<string>"

,

"slug"

:

"<string>"

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

"<string>"

,

"updatedBy"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

}

],

"tags"

: [

{

"id"

:

"<string>"

,

"label"

:

"<string>"

,

"slug"

:

"<string>"

,

"forceShow"

:

true

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

123

,

"updatedBy"

:

123

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"forceHide"

:

true

,

"isCarousel"

:

true

}

],

"commentCount"

:

123

,

"chats"

: [

{

"id"

:

"<string>"

,

"channelId"

:

"<string>"

,

"channelName"

:

"<string>"

,

"channelImage"

:

"<string>"

,

"live"

:

true

,

"startTime"

:

"2023-11-07T05:31:56Z"

,

"endTime"

:

"2023-11-07T05:31:56Z"

}

]

}

]

Query Parameters

​

limit

integer

Required range:

x >= 0

​

offset

integer

Required range:

x >= 0

​

order

string

Comma-separated list of fields to order by

​

ascending

boolean

​

slug

string[]

​

categories_ids

integer[]

​

categories_labels

string[]

​

closed

boolean

​

include_chat

boolean

​

recurrence

string

Response

200 - application/json

List of series

​

id

string

​

ticker

string | null

​

slug

string | null

​

title

string | null

​

subtitle

string | null

​

seriesType

string | null

​

recurrence

string | null

​

description

string | null

​

image

string | null

​

icon

string | null

​

layout

string | null

​

active

boolean | null

​

closed

boolean | null

​

archived

boolean | null

​

new

boolean | null

​

featured

boolean | null

​

restricted

boolean | null

​

isTemplate

boolean | null

​

templateVariables

boolean | null

​

publishedAt

string | null

​

createdBy

string | null

​

updatedBy

string | null

​

createdAt

string<date-time> | null

​

updatedAt

string<date-time> | null

​

commentsEnabled

boolean | null

​

competitive

string | null

​

volume24hr

number | null

​

volume

number | null

​

liquidity

number | null

​

startDate

string<date-time> | null

​

pythTokenID

string | null

​

cgAssetName

string | null

​

score

integer | null

​

events

object[]

Show

child attributes

​

collections

object[]

Show

child attributes

​

categories

object[]

Show

child attributes

​

tags

object[]

Show

child attributes

​

commentCount

integer | null

​

chats

object[]

Show

child attributes

Get market by slug

Get series by id

⌘

I