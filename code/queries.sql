-- Query the number of comments and comment_time
SELECT 
    stock, 
    COUNT(*) AS unique_comments_count
FROM (
    SELECT DISTINCT stock, comment_time, comments, influence, sentiment_tag
    FROM "public"."comments"
) subquery
GROUP BY stock
ORDER BY unique_comments_count;

SELECT stock, comment_time
FROM (
  SELECT 
    stock, 
    comment_time,
    ROW_NUMBER() OVER (PARTITION BY stock ORDER BY comment_time ASC) AS row_num
  FROM "public"."comments"
) subquery
WHERE row_num <= 10
ORDER BY stock, comment_time;

SELECT COUNT(*) AS unique_comments_count
FROM (
  SELECT DISTINCT stock, comment_time, comments,influence,sentiment_tag
  FROM "public"."comments"
) subquery;