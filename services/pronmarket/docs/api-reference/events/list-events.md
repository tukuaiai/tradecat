# List events - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/events/list-events

---

List events - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Events

List events

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

GET

List events

GET

Get event by id

GET

Get event tags

GET

Get event by slug

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

List events

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/events

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

{}

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

]

GET

/

events

Try it

List events

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/events

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

{}

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

id

integer[]

​

slug

string[]

​

tag_id

integer

​

exclude_tag_id

integer[]

​

related_tags

boolean

​

featured

boolean

​

cyom

boolean

​

include_chat

boolean

​

include_template

boolean

​

recurrence

string

​

closed

boolean

​

start_date_min

string<date-time>

​

start_date_max

string<date-time>

​

end_date_min

string<date-time>

​

end_date_max

string<date-time>

Response

200 - application/json

List of events

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

description

string | null

​

resolutionSource

string | null

​

startDate

string<date-time> | null

​

creationDate

string<date-time> | null

​

endDate

string<date-time> | null

​

image

string | null

​

icon

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

liquidity

number | null

​

volume

number | null

​

openInterest

number | null

​

sortBy

string | null

​

category

string | null

​

subcategory

string | null

​

isTemplate

boolean | null

​

templateVariables

string | null

​

published_at

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

number | null

​

volume24hr

number | null

​

volume1wk

number | null

​

volume1mo

number | null

​

volume1yr

number | null

​

featuredImage

string | null

​

disqusThread

string | null

​

parentEvent

string | null

​

enableOrderBook

boolean | null

​

liquidityAmm

number | null

​

liquidityClob

number | null

​

negRisk

boolean | null

​

negRiskMarketID

string | null

​

negRiskFeeBips

integer | null

​

commentCount

integer | null

​

imageOptimized

object

Show

child attributes

​

iconOptimized

object

Show

child attributes

​

featuredImageOptimized

object

Show

child attributes

​

subEvents

string[] | null

​

markets

object[]

Show

child attributes

​

series

object[]

Show

child attributes

​

categories

object[]

Show

child attributes

​

collections

object[]

Show

child attributes

​

tags

object[]

Show

child attributes

​

cyom

boolean | null

​

closedTime

string<date-time> | null

​

showAllOutcomes

boolean | null

​

showMarketImages

boolean | null

​

automaticallyResolved

boolean | null

​

enableNegRisk

boolean | null

​

automaticallyActive

boolean | null

​

eventDate

string | null

​

startTime

string<date-time> | null

​

eventWeek

integer | null

​

seriesSlug

string | null

​

score

string | null

​

elapsed

string | null

​

period

string | null

​

live

boolean | null

​

ended

boolean | null

​

finishedTimestamp

string<date-time> | null

​

gmpChartMode

string | null

​

eventCreators

object[]

Show

child attributes

​

tweetCount

integer | null

​

chats

object[]

Show

child attributes

​

featuredOrder

integer | null

​

estimateValue

boolean | null

​

cantEstimate

boolean | null

​

estimatedValue

string | null

​

templates

object[]

Show

child attributes

​

spreadsMainLine

number | null

​

totalsMainLine

number | null

​

carouselMap

string | null

​

pendingDeployment

boolean | null

​

deploying

boolean | null

​

deployingTimestamp

string<date-time> | null

​

scheduledDeploymentTimestamp

string<date-time> | null

​

gameStatus

string | null

Get tags related to a tag slug

Get event by id

⌘

I