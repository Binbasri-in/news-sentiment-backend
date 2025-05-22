-- Updated SQL insert script for the new Profile model schema

INSERT INTO profiles (name, base_url, language, crawling_strategy, crawling_state, is_active)
VALUES 
  ('inshorts', 'https://inshorts.com/en/read', 'English', 'custom', 'idle', true),
  ('deccanheald', 'https://www.deccanherald.com/', 'English', 'custom', 'idle', true),
  ('thehindu', 'https://www.thehindu.com/', 'English', 'custom', 'idle', true),
  ('theguardian', 'https://www.theguardian.com/international', 'English', 'custom', 'idle', true);

-- Insert into articles
INSERT INTO articles (id, source_id, url, title, author, content, summary, published_at, classification, sentiment, thumbnail_url, tags, is_featured, is_reported, reported_reason)
VALUES
(1, 1, 'https://www.bbc.com/news/world-1', 'World leaders gather for summit', 'John Doe', 'Full article content here...', 'Summary of summit meeting', '2025-04-28 08:00:00', 'politics', 'positive', 'https://dummyimage.com/600x400/bbc1', 'politics,world', TRUE, FALSE, NULL),
(2, 1, 'https://www.bbc.com/news/tech-2', 'New Tech Innovations Announced', 'Jane Smith', 'Content about tech innovations...', 'Latest tech news summary', '2025-04-28 09:00:00', 'technology', 'neutral', 'https://dummyimage.com/600x400/bbc2', 'technology,innovation', FALSE, FALSE, NULL),
(3, 2, 'https://edition.cnn.com/news/economy-1', 'Global Markets Volatile', 'Chris Johnson', 'Market volatility details...', 'Economic downturn signs', '2025-04-28 06:30:00', 'economy', 'negative', 'https://dummyimage.com/600x400/cnn1', 'economy,markets', TRUE, FALSE, NULL),
(4, 3, 'https://www.aljazeera.com/news/environment-1', 'Climate Action Urgency', NULL, 'Climate change effects discussed...', 'Urgent climate call', '2025-04-27 07:45:00', 'environment', 'positive', 'https://dummyimage.com/600x400/aljazeera1', 'environment,climate', FALSE, FALSE, NULL),
(5, 2, 'https://www.reuters.com/news/politics-1', 'Elections Coming Soon', 'Alex Green', 'Election news updates...', 'Upcoming elections summary', '2025-04-27 14:20:00', 'politics', 'neutral', 'https://dummyimage.com/600x400/reuters1', 'politics,elections', FALSE, FALSE, NULL);
