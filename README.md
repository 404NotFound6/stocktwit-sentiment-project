<div align="center">
  
# How do Public Sentiments Affect Stock Metrics?

<font size="5">**11 December 2024**</font>  
<font size="5"><i>Python, Big Data, and Databases (ECO395m)</i></font>



**404 NotFound: Rongzheng Ma, Siyi Li, Sherry Chen**
</div>

---

## Introduction

The goal of this project is to analyze how public sentiments could potentially affect the Dow Jones Index and the prices of Companies in the Index. The public sentiments were acquired from the comments of an open online forum, Stocktwit. By performing a time-series regression analysis, we could have a better understanding of how sentiments score from StockTwits predict future stock movements. 


## Methodology

We scraped the comments and the number of comments that are under each comment of 30 companies in the Dow Jones Index from the forum Stocktwit using Python packaging selenium. Since the total number of data is huge, We then connected to the Google Cloud Platform(GCP) to acquire servers to help with scraping. After scraping, we add these posts to the SQL database and use SQLAlchemy to derive sentiment scores in the (GPT model) (need to switch). 

1. Stocktwit Comments: We acquired 85775 posts from these 30 companies. Based on the date that the program stopped, the number of comments on each company is not the same, and the last date of the comment scarped for each company is not the same as well. The output of all the comments was directly pushed to the database. The summary of the number of comments and the last date of the comment scraped is provided below and also in the artifact folder.

2. Sentiments Scores:

3. Regression: We first employed the MA and VAR models for time series analysis to examine the impact of sentiment scores on Dow Jones Index (DJI)'s return and volume. Then to analyze the sentimetn scores's effect on stocks, we use the dynamic panel model with GMM estimation.



## Step for Reproduce

Install the necessary package with the pip install -r requirement.txt 

## Results

**Sentiment Scores:**

**Regression:** 
1. Dow Jones Index:
   Impact of sentiment scores on return:
<div align="center">

| Variable | Coefficient | Std Error | t-value |p-value|
|:-----:|:---------------:|:-----:|:---------------:|:-----:|
| Constant   | -0.4215      | 0.3087   | 0.3087    |0.1722|
| Weighted_Sentiment_Lag1	   | -0.6109     | 0.3335 | -1.8321 |0.0669|
| Sigma2 | 104,217.89       | 0.986    | 3.6375      |0.0003|
</div>

This regression result suggests that the first lag of sentiment scores would negatively affect the log return of Dow Jones Index.

  Impact of sentiment scores on volume:
<div align="center">
  
  | Variable | Coefficient | Std Error | t-value |p-value|
|:-----:|:---------------:|:-----:|:---------------:|:-----:|
| Constant   | 19.9319|	0.1215|	164.0736	|0.0|
| Weighted_Sentiment_Lag3	   |-0.2741|	0.1152|	-2.3786|	0.0174|
| ma.L1	|0.5029	|0.1864|2.6974|	0.007|
|  ma.L2|	0.3557|	0.2059|	1.7276	|0.0841|
|  sigma2|	0.0655|	0.0144|	4.5459|	0.0|
</div>
This MA(2) regression result suggest that the third lag of sentiment scores also negatively affect the log volume of Dow Jones Index. 

We also generate the Impulse Response graph to see the how return and volume respond to the change in sentiment scores.
![ var return ](./artifacts/var_return_impulse_response_irf.png)

![ var return ](./artifacts/var_volume_impulse_response_irf.png)


2. 30 Stocks:
<div align="center">
  
| Variable | Coefficient | Std Error | t-value |p-value|
|:-----:|:---------------:|:-----:|:---------------:|:-----:|
| Constant   | -1.9315|	0.8548|	-2.2597	|0.0238| 
|log_return_lag1|	-0.0367|	0.0266|	-1.3829	|0.1667|
|sentiment_score_lag1|	-0.0053|	0.0191|	-0.2781|	0.781|
|sentiment_score_lag2|	0.0164|	0.0187|	0.8783	|0.3798|
|sentiment_score_lag3	|-0.0472|	0.0189	|-2.4988|	0.0125|
|variation	|37.3647|	3.4888|	10.7098	|0.0|
|log_size|	0.0568|	0.0323|	1.7563	|0.079|
</div>

This regression result suggests that only the third lag of sentiment scores would have negative impact on log return, which is similar to the regression on DJI's return , showing that sentiment scores negatively related to log return both in index level and individual firm level.

<div align="center">
  
| Variable | Coefficient | Std Error | t-value |p-value|
|:-----:|:---------------:|:-----:|:---------------:|:-----:|
| Constant   | -0.4128|	0.3961|	-1.0422	|0.2973| 
|log_volume_lag1|	0.8847|	0.0149|	59.3858|	0.0|
|sentiment_score_lag1|	-0.0007|	0.0074|	-0.0987	|0.9214|
|sentiment_score_lag2|	-0.0061|	0.0073|	-0.832	|0.4054|
|sentiment_score_lag3	|-0.0077|	0.008	|-0.9608|	0.3367|
|variation	|16.0298|	1.4528|	11.0337|	0.0|
|log_size|	0.0743|	0.0164	|4.5232|	0.0|
</div>

This regression results suggests that all the lagd of sentiment scores are not statistically significant, but the coefficients are all negative, which shows the similar negative impact of sentiment score on return from previous regression for DJI.

Generally, the impact of sentiment score on individual stocks shares the same sign as the impact on Dow Jones Index.

## Limitation



