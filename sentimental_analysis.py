import os
import re
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

def parse_reviews_text(text_content):
    """Parse reviews with 'Rating: X stars' and 'Review:' format."""
    # Split the text by newline to process line by line
    lines = text_content.strip().split('\n')
    
    reviews = []
    current_review = {}
    review_text_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Check for rating pattern
        rating_match = re.match(r'^Rating:\s+(\d+)\s+stars?', line, re.IGNORECASE)
        if rating_match:
            # If we have a previous review in progress, save it
            if current_review and 'rating' in current_review:
                if review_text_lines:
                    current_review['text'] = ' '.join(review_text_lines)
                reviews.append(current_review)
                review_text_lines = []
            
            # Start a new review
            current_review = {
                'reviewer': "Anonymous",
                'rating': int(rating_match.group(1)),
                'date': ""
            }
            continue
        
        # Check for review text pattern
        review_match = re.match(r'^Review:\s+(.*)', line, re.IGNORECASE)
        if review_match and current_review:
            review_text_lines = [review_match.group(1)]
            continue
        
        # If not a new review or rating and we're currently processing a review, add line to current review text
        if current_review and 'rating' in current_review:
            review_text_lines.append(line)
    
    # Don't forget to add the last review
    if current_review and 'rating' in current_review:
        if review_text_lines:
            current_review['text'] = ' '.join(review_text_lines)
        reviews.append(current_review)
    
    print(f"Successfully parsed {len(reviews)} reviews from the text")
    
    # Create restaurant info from the data
    restaurant_info = {
        'name': "SauceBros",
        'address': "Plano, TX",  # Extracted from the reviews
        'source': "Customer Reviews"
    }
    
    return restaurant_info, reviews

def analyze_sentiment(reviews, model_name="distilbert-base-uncased-finetuned-sst-2-english"):
    """Analyze sentiment for each review using Hugging Face model."""
    print(f"Loading sentiment analysis model: {model_name}")
    
    # Initialize sentiment analysis pipeline
    sentiment_analyzer = pipeline(
        "sentiment-analysis", 
        model=model_name, 
        tokenizer=model_name
    )
    
    # For longer reviews, we might need to handle token limits
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    max_length = tokenizer.model_max_length
    
    print(f"Analyzing sentiment for {len(reviews)} reviews...")
    for review in tqdm(reviews):
        text = review['text']
        
        # Check if text is too long for the model's max input size
        if len(tokenizer.encode(text)) > max_length:
            # Simple truncation approach - split into chunks and analyze first chunk
            encoded = tokenizer.encode(text, max_length=max_length-10, truncation=True)
            text = tokenizer.decode(encoded)
        
        # Get sentiment prediction
        result = sentiment_analyzer(text)[0]
        review['sentiment_label'] = result['label']
        review['sentiment_score'] = result['score']
        
        # Add a simplified sentiment category
        if result['label'] == 'POSITIVE':
            review['sentiment'] = 'positive'
        elif result['label'] == 'NEGATIVE':
            review['sentiment'] = 'negative'
        else:
            review['sentiment'] = 'neutral'
    
    return reviews

def create_visualizations(reviews, restaurant_info, output_dir="review_analysis"):
    """Create visualizations from the sentiment analysis."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(reviews)
    
    # 1. Star rating distribution
    plt.figure(figsize=(10, 6))
    rating_counts = df['rating'].value_counts().sort_index()
    bars = plt.bar(rating_counts.index, rating_counts.values, color='skyblue')
    plt.title(f'Star Rating Distribution - {restaurant_info["name"]}')
    plt.xlabel('Star Rating')
    plt.ylabel('Number of Reviews')
    plt.xticks(range(1, 6))
    
    # Add count labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.0f}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'rating_distribution.png'))
    
    # 2. Sentiment analysis distribution
    plt.figure(figsize=(10, 6))
    sentiment_counts = df['sentiment'].value_counts()
    colors = {'positive': 'green', 'neutral': 'gray', 'negative': 'red'}
    sentiment_bars = plt.bar(sentiment_counts.index, sentiment_counts.values, 
                           color=[colors.get(s, 'blue') for s in sentiment_counts.index])
    plt.title(f'Sentiment Analysis - {restaurant_info["name"]}')
    plt.xlabel('Sentiment')
    plt.ylabel('Number of Reviews')
    
    # Add count labels on top of bars
    for bar in sentiment_bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.0f}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'sentiment_distribution.png'))
    
    # 3. Relationship between star rating and sentiment score
    plt.figure(figsize=(10, 6))
    plt.scatter(df['rating'], df['sentiment_score'], alpha=0.7)
    plt.title(f'Rating vs. Sentiment Score - {restaurant_info["name"]}')
    plt.xlabel('Star Rating')
    plt.ylabel('Sentiment Score (higher = more positive)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(range(1, 6))
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'rating_vs_sentiment.png'))
    
    # 4. New visualization: Rating distribution by sentiment category
    plt.figure(figsize=(12, 7))
    sentiment_categories = df['sentiment'].unique()
    
    # Group data by sentiment and count ratings within each sentiment
    for i, sentiment in enumerate(sentiment_categories):
        sentiment_data = df[df['sentiment'] == sentiment]
        sentiment_rating_counts = sentiment_data['rating'].value_counts().sort_index()
        
        # Plot each sentiment category with offset for better visibility
        offset = (i - len(sentiment_categories)/2 + 0.5) * 0.25
        x_positions = [x + offset for x in range(1, 6)]
        
        available_ratings = sentiment_rating_counts.index.tolist()
        counts = [sentiment_rating_counts.get(rating, 0) for rating in range(1, 6)]
        
        plt.bar(x_positions, counts, width=0.2, 
                color=colors.get(sentiment, 'blue'),
                label=f'{sentiment.capitalize()} sentiment')
    
    plt.title(f'Rating Distribution by Sentiment Category - {restaurant_info["name"]}')
    plt.xlabel('Star Rating')
    plt.ylabel('Number of Reviews')
    plt.xticks(range(1, 6))
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'rating_by_sentiment.png'))
    
    # Save analysis results to CSV
    df.to_csv(os.path.join(output_dir, f'{restaurant_info["name"].replace(" ", "_")}_sentiment_analysis.csv'), index=False)
    
    return os.path.join(output_dir, f'{restaurant_info["name"].replace(" ", "_")}_sentiment_analysis.csv')

def generate_report(reviews, restaurant_info, csv_path, output_dir="review_analysis"):
    """Generate a summary report of the sentiment analysis."""
    df = pd.DataFrame(reviews)
    
    # Calculate summary statistics
    total_reviews = len(df)
    avg_rating = df['rating'].mean() if df['rating'].sum() > 0 else "N/A"
    positive_count = len(df[df['sentiment'] == 'positive'])
    neutral_count = len(df[df['sentiment'] == 'neutral'])
    negative_count = len(df[df['sentiment'] == 'negative'])
    
    positive_pct = (positive_count / total_reviews) * 100 if total_reviews > 0 else 0
    neutral_pct = (neutral_count / total_reviews) * 100 if total_reviews > 0 else 0
    negative_pct = (negative_count / total_reviews) * 100 if total_reviews > 0 else 0
    
    # Extract common menu items mentioned positively and negatively
    menu_items = [
        "harissa chicken", "korean bbq", "korean beef", "naga habanero", 
        "habanero chicken", "4 cheese", "beef taco", "meat lovers"
    ]
    
    item_mentions = {}
    for item in menu_items:
        positive_mentions = sum(1 for r in reviews if item.lower() in r['text'].lower() and r['sentiment'] == 'positive')
        negative_mentions = sum(1 for r in reviews if item.lower() in r['text'].lower() and r['sentiment'] == 'negative')
        item_mentions[item] = {
            'positive': positive_mentions,
            'negative': negative_mentions,
            'total': positive_mentions + negative_mentions
        }
    
    # Generate report
    report_path = os.path.join(output_dir, f'{restaurant_info["name"].replace(" ", "_")}_sentiment_report.txt')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"SENTIMENT ANALYSIS REPORT\n")
        f.write(f"Restaurant: {restaurant_info['name']}\n")
        f.write(f"Address: {restaurant_info['address']}\n")
        f.write(f"Source: {restaurant_info['source']}\n")
        f.write(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"SUMMARY STATISTICS:\n")
        f.write(f"Total Reviews Analyzed: {total_reviews}\n")
        if isinstance(avg_rating, float):
            f.write(f"Average Star Rating: {avg_rating:.2f} / 5.0\n\n")
        else:
            f.write(f"Average Star Rating: {avg_rating} (No ratings explicitly provided)\n\n")
        
        f.write(f"SENTIMENT BREAKDOWN:\n")
        f.write(f"Positive Reviews: {positive_count} ({positive_pct:.1f}%)\n")
        f.write(f"Neutral Reviews: {neutral_count} ({neutral_pct:.1f}%)\n")
        f.write(f"Negative Reviews: {negative_count} ({negative_pct:.1f}%)\n\n")
        
        # Top menu items and their sentiment
        f.write(f"MENU ITEM SENTIMENT ANALYSIS:\n")
        f.write(f"{'Item':<20} {'Positive':<10} {'Negative':<10} {'Total':<10}\n")
        f.write("-" * 50 + "\n")
        
        for item, data in sorted(item_mentions.items(), key=lambda x: x[1]['total'], reverse=True):
            if data['total'] > 0:
                f.write(f"{item:<20} {data['positive']:<10} {data['negative']:<10} {data['total']:<10}\n")
        f.write("\n")
        
        # Key positive aspects mentioned
        positive_aspects = []
        for review in reviews:
            if review['sentiment'] == 'positive':
                text = review['text'].lower()
                if 'service' in text and 'great' in text:
                    positive_aspects.append('Great service')
                if 'crisp' in text or 'crispy' in text:
                    positive_aspects.append('Crispy crust')
                if 'flavor' in text and ('good' in text or 'great' in text):
                    positive_aspects.append('Good flavors')
        
        if positive_aspects:
            f.write(f"KEY POSITIVE ASPECTS MENTIONED:\n")
            for aspect in set(positive_aspects):
                f.write(f"- {aspect}\n")
            f.write("\n")
        
        # Key negative aspects mentioned
        negative_aspects = []
        for review in reviews:
            if review['sentiment'] == 'negative':
                text = review['text'].lower()
                if 'small' in text and ('place' in text or 'size' in text):
                    negative_aspects.append('Small restaurant size')
                if 'sauce' in text and ('too much' in text or 'sweet' in text):
                    negative_aspects.append('Issues with sauce')
                if 'price' in text or 'expensive' in text or 'pricey' in text:
                    negative_aspects.append('Price concerns')
        
        if negative_aspects:
            f.write(f"KEY NEGATIVE ASPECTS MENTIONED:\n")
            for aspect in set(negative_aspects):
                f.write(f"- {aspect}\n")
            f.write("\n")
        
        # Top positive and negative reviews
        if positive_count > 0:
            top_positive = df[df['sentiment'] == 'positive'].sort_values('sentiment_score', ascending=False).iloc[0]
            f.write(f"MOST POSITIVE REVIEW (Score: {top_positive['sentiment_score']:.3f}):\n")
            f.write(f"Rating: {top_positive['rating']} stars\n")
            f.write(f"Review: {top_positive['text']}\n\n")
        
        if negative_count > 0:
            top_negative = df[df['sentiment'] == 'negative'].sort_values('sentiment_score').iloc[0]
            f.write(f"MOST NEGATIVE REVIEW (Score: {top_negative['sentiment_score']:.3f}):\n")
            f.write(f"Rating: {top_negative['rating']} stars\n")
            f.write(f"Review: {top_negative['text']}\n\n")
        
        f.write(f"Full analysis results saved to: {csv_path}\n")
    
    return report_path

def main():
    # Ask user if they want to input from a file or paste text directly
    input_method = input("Enter '1' to read from a file or '2' to paste text directly: ").strip()
    
    if input_method == '1':
        # Get file path from user or use the default
        default_path = "/Users/gayathriutla/Desktop/Projects/hackai/restaurant_reviews/SauceBros_reviews_with_ratings.txt"
        file_path = input(f"Enter review file path (or press Enter to use default {default_path}): ").strip()
        
        if not file_path:
            file_path = default_path

        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            return
        
        print(f"Reading reviews from: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            review_text = f.read()
    else:
        print("Please paste the review text (press Ctrl+D or Ctrl+Z when finished):")
        review_lines = []
        try:
            while True:
                line = input()
                review_lines.append(line)
        except EOFError:
            review_text = '\n'.join(review_lines)
    
    # Parse the reviews
    restaurant_info, reviews = parse_reviews_text(review_text)
    
    if not reviews:
        print("No reviews were parsed from the input. Please check the format.")
        return
        
    print(f"Found {len(reviews)} reviews for {restaurant_info['name']}")
    
    # Analyze a sample of the first review to verify parsing worked correctly
    if reviews:
        print("\nSample of first review:")
        print(f"Rating: {reviews[0]['rating']} stars")
        print(f"Text: {reviews[0]['text'][:100]}...")
    
    # Confirm with user before continuing with large sets
    if len(reviews) > 50:
        proceed = input(f"\nFound {len(reviews)} reviews. Processing may take some time. Continue? (y/n): ").lower()
        if proceed != 'y':
            print("Operation cancelled by user.")
            return
    
    # You can choose from different sentiment models:
    # - "distilbert-base-uncased-finetuned-sst-2-english" (faster, general sentiment)
    # - "nlptown/bert-base-multilingual-uncased-sentiment" (5-class sentiment with star ratings)
    # - "cardiffnlp/twitter-roberta-base-sentiment" (3-class sentiment optimized for social media)
    
    # For restaurant reviews, we'll use a model that handles nuanced opinions well
    model_name = "distilbert-base-uncased-finetuned-sst-2-english"
    analyzed_reviews = analyze_sentiment(reviews, model_name)
    
    output_dir = f"sentiment_analysis_{restaurant_info['name'].replace(' ', '_').replace('/', '_')}"
    csv_path = create_visualizations(analyzed_reviews, restaurant_info, output_dir)
    
    report_path = generate_report(analyzed_reviews, restaurant_info, csv_path, output_dir)
    print(f"Analysis complete! Report saved to: {report_path}")
    
    # Print summary of findings
    df = pd.DataFrame(analyzed_reviews)
    positive_pct = (len(df[df['sentiment'] == 'positive']) / len(df)) * 100 if len(df) > 0 else 0
    print(f"\nSUMMARY:")
    print(f"Average rating: {df['rating'].mean():.2f}/5.0")
    print(f"Sentiment breakdown: {positive_pct:.1f}% positive")
    
    # Find any discrepancies between rating and sentiment
    discrepancies = df[(df['rating'] >= 4) & (df['sentiment'] == 'negative') | 
                    (df['rating'] <= 2) & (df['sentiment'] == 'positive')]
    
    if len(discrepancies) > 0:
        print(f"\nFound {len(discrepancies)} reviews with potential discrepancies between star rating and sentiment.")
        print("These might be worth investigating further:")
        for i, review in discrepancies.iterrows():
            print(f"- Rating: {review['rating']} stars, Sentiment: {review['sentiment']}")
            print(f"  Text snippet: {review['text'][:50]}...")

if __name__ == "__main__":
    main()