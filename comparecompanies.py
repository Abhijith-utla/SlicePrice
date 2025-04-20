import os
import re
from transformers import pipeline, AutoTokenizer
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import numpy as np

def parse_reviews_text(text_content, company_name):
    """Parse reviews using multiple possible formats."""
    # Split the text by newline to process line by line
    lines = text_content.strip().split('\n')
    
    reviews = []
    current_review = {}
    review_text_lines = []
    
    # Try to detect format based on first few lines
    print(f"Analyzing format for {company_name}...")
    
    # Check for Yelp-like format (reviewer name followed by star rating and date, then review text)
    yelp_pattern = any(re.search(r'\d+ stars?', line, re.IGNORECASE) for line in lines[:20])
    
    if yelp_pattern:
        print(f"Using Yelp-style parsing for {company_name}")
        # Process line by line for Yelp-style format
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for star pattern to identify beginning of a review
            star_match = re.search(r'(\d+) stars?', line, re.IGNORECASE)
            
            if star_match:
                # If we have a previous review in progress, save it
                if current_review and 'rating' in current_review and review_text_lines:
                    current_review['text'] = ' '.join(review_text_lines)
                    reviews.append(current_review)
                
                # Extract reviewer and date if available (common format in Yelp data)
                reviewer = "Anonymous"
                date = ""
                
                # Start a new review
                current_review = {
                    'reviewer': reviewer,
                    'rating': int(star_match.group(1)),
                    'date': date,
                    'company': company_name
                }
                
                # Reset review text collection
                review_text_lines = []
                
                # The review text might start on the next line
                i += 1
                if i < len(lines):
                    review_text_lines.append(lines[i].strip())
            
            # If we're in a review, add line to current review text
            elif current_review and 'rating' in current_review:
                review_text_lines.append(line)
            
            i += 1
    else:
        # Try the original format with "Rating: X stars" and "Review:" labels
        print(f"Using labeled format parsing for {company_name}")
        
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
                    'date': "",
                    'company': company_name
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
    
    # If no reviews found, try a more aggressive approach
    if not reviews:
        print(f"Standard parsing failed for {company_name}. Trying raw text extraction...")
        
        # Try to extract reviews from raw text by looking for rating patterns
        all_text = ' '.join(lines)
        
        # Look for patterns like "X stars" or "rated X/5"
        ratings = re.findall(r'(\d+)\s+stars?|rated\s+(\d+)/5', all_text, re.IGNORECASE)
        
        if ratings:
            # Split text into chunks based on star ratings
            chunks = re.split(r'\d+\s+stars?|rated\s+\d+/5', all_text, flags=re.IGNORECASE)
            
            # First chunk is usually before any rating, so skip it if it's small
            if len(chunks) > len(ratings):
                chunks = chunks[1:] if len(chunks[0]) < 100 else chunks
            
            # Create reviews from chunks
            for i, chunk in enumerate(chunks):
                if i < len(ratings):
                    # Get rating from tuple (either first or second group will be filled)
                    rating = next(int(r) for r in ratings[i] if r)
                    
                    # Add the review if chunk is substantial
                    if len(chunk.strip()) > 20:
                        reviews.append({
                            'reviewer': "Anonymous",
                            'rating': rating,
                            'date': "",
                            'text': chunk.strip(),
                            'company': company_name
                        })
    
    # Handle the case where file might just be raw review text without explicit ratings
    if not reviews and len(lines) > 3:
        print(f"No structured reviews found for {company_name}. Processing as raw review text...")
        
        # Treat each paragraph (groups of non-empty lines) as a review
        paragraphs = []
        current_para = []
        
        for line in lines:
            if line.strip():
                current_para.append(line.strip())
            elif current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
        
        # Add the last paragraph if it exists
        if current_para:
            paragraphs.append(' '.join(current_para))
        
        # Create reviews from paragraphs
        for para in paragraphs:
            if len(para) > 20:  # Only include substantial paragraphs
                reviews.append({
                    'reviewer': "Anonymous",
                    'rating': 0,  # No rating available
                    'date': "",
                    'text': para,
                    'company': company_name
                })
    
    print(f"Successfully parsed {len(reviews)} reviews for {company_name}")
    
    # Create company info
    company_info = {
        'name': company_name
    }
    
    return company_info, reviews

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
        # Check if 'text' key exists in the review dictionary
        if 'text' not in review or not review['text']:
            print(f"Warning: Review missing text content: {review}")
            review['sentiment_label'] = 'NEUTRAL'
            review['sentiment_score'] = 0.5
            review['sentiment'] = 'neutral'
            continue
            
        text = review['text']
        
        # Check if text is too long for the model's max input size
        if len(tokenizer.encode(text)) > max_length:
            # Simple truncation approach - split into chunks and analyze first chunk
            encoded = tokenizer.encode(text, max_length=max_length-10, truncation=True)
            text = tokenizer.decode(encoded)
        
        try:
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
        except Exception as e:
            print(f"Error analyzing text: {e}")
            review['sentiment_label'] = 'NEUTRAL'
            review['sentiment_score'] = 0.5
            review['sentiment'] = 'neutral'
    
    return reviews

def create_company_comparison_visualizations(companies_data, output_dir="multi_company_analysis_pizza"):
    """Create comparative visualizations across all companies."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare data for comparison
    company_names = []
    positive_counts = []
    negative_counts = []
    neutral_counts = []
    total_counts = []
    positive_percentages = []
    sentiment_scores = []
    
    for company_name, reviews in companies_data.items():
        company_names.append(company_name)
        
        df = pd.DataFrame(reviews)
        
        # Count sentiment types
        pos_count = len(df[df['sentiment'] == 'positive'])
        neg_count = len(df[df['sentiment'] == 'negative'])
        neu_count = len(df[df['sentiment'] == 'neutral'])
        total = len(df)
        
        positive_counts.append(pos_count)
        negative_counts.append(neg_count)
        neutral_counts.append(neu_count)
        total_counts.append(total)
        
        # Calculate percentage
        pos_pct = (pos_count / total) * 100 if total > 0 else 0
        positive_percentages.append(pos_pct)
        
        # Calculate average sentiment score
        avg_score = df['sentiment_score'].mean() if 'sentiment_score' in df.columns else 0
        sentiment_scores.append(avg_score)
    
    # Create DataFrame for easy visualization
    comparison_df = pd.DataFrame({
        'Company': company_names,
        'Positive': positive_counts,
        'Negative': negative_counts,
        'Neutral': neutral_counts,
        'Total': total_counts,
        'Positive_Percentage': positive_percentages,
        'Avg_Sentiment_Score': sentiment_scores
    })
    
    # Sort by positive percentage (descending)
    comparison_df = comparison_df.sort_values('Positive_Percentage', ascending=False)
    comparison_df['Rank'] = range(1, len(comparison_df) + 1)
    
    # Save comparison data
    comparison_df.to_csv(os.path.join(output_dir, 'company_sentiment_comparison.csv'), index=False)
    
    # 1. Comparative bar chart of positive, negative, and neutral counts
    plt.figure(figsize=(14, 8))
    
    # Get positions for bars
    x = np.arange(len(company_names))
    width = 0.25
    
    # Sort for visualization
    sorted_df = comparison_df.sort_values('Positive_Percentage', ascending=False).reset_index(drop=True)
    
    # Create bars
    plt.bar(x - width, sorted_df['Positive'], width, label='Positive', color='green')
    plt.bar(x, sorted_df['Negative'], width, label='Negative', color='red')
    plt.bar(x + width, sorted_df['Neutral'], width, label='Neutral', color='gray')
    
    # Add labels and legend
    plt.xlabel('Company')
    plt.ylabel('Number of Reviews')
    plt.title('Sentiment Distribution Across Companies')
    plt.xticks(x, sorted_df['Company'], rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'sentiment_distribution_comparison.png'))
    
    # 2. Comparative bar chart of positive percentages (ranking visualization)
    plt.figure(figsize=(14, 8))
    
    # Create horizontal bars sorted by positive percentage
    companies_by_pct = comparison_df.sort_values('Positive_Percentage')
    plt.barh(companies_by_pct['Company'], companies_by_pct['Positive_Percentage'], color='skyblue')
    
    # Add percentage labels
    for i, v in enumerate(companies_by_pct['Positive_Percentage']):
        plt.text(v + 1, i, f"{v:.1f}%", va='center')
    
    # Add rank labels
    for i, (_, row) in enumerate(companies_by_pct.iterrows()):
        plt.text(2, i, f"Rank: {len(comparison_df) - i}", va='center', fontweight='bold', bbox=dict(facecolor='white', alpha=0.7))
    
    plt.xlabel('Positive Review Percentage')
    plt.title('Companies Ranked by Positive Sentiment Percentage')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'company_ranking_by_positive_sentiment.png'))
    
    # 3. Stacked percentage bar chart
    plt.figure(figsize=(14, 8))
    
    # Prepare data for stacked chart
    sorted_companies = sorted_df['Company'].tolist()
    
    # Calculate percentages for each sentiment type
    pos_pcts = []
    neg_pcts = []
    neu_pcts = []
    
    for company in sorted_companies:
        total = sorted_df.loc[sorted_df['Company'] == company, 'Total'].values[0]
        pos_pct = (sorted_df.loc[sorted_df['Company'] == company, 'Positive'].values[0] / total) * 100 if total > 0 else 0
        neg_pct = (sorted_df.loc[sorted_df['Company'] == company, 'Negative'].values[0] / total) * 100 if total > 0 else 0
        neu_pct = (sorted_df.loc[sorted_df['Company'] == company, 'Neutral'].values[0] / total) * 100 if total > 0 else 0
        
        pos_pcts.append(pos_pct)
        neg_pcts.append(neg_pct)
        neu_pcts.append(neu_pct)
    
    # Create stacked bar chart
    plt.figure(figsize=(14, 8))
    indices = np.arange(len(sorted_companies))
    
    p1 = plt.bar(indices, pos_pcts, color='green')
    p2 = plt.bar(indices, neg_pcts, bottom=pos_pcts, color='red')
    p3 = plt.bar(indices, neu_pcts, bottom=[pos_pcts[i] + neg_pcts[i] for i in range(len(pos_pcts))], color='gray')
    
    plt.xlabel('Company')
    plt.ylabel('Percentage')
    plt.title('Sentiment Distribution Percentage by Company')
    plt.xticks(indices, sorted_companies, rotation=45, ha='right')
    plt.legend((p1[0], p2[0], p3[0]), ('Positive', 'Negative', 'Neutral'))
    
    # Add percentage labels
    for i in range(len(sorted_companies)):
        # Positive percentage label
        if pos_pcts[i] > 7:  # Only show label if segment is large enough
            plt.text(i, pos_pcts[i]/2, f"{pos_pcts[i]:.1f}%", ha='center', va='center', color='white', fontweight='bold')
        
        # Negative percentage label
        if neg_pcts[i] > 7:
            plt.text(i, pos_pcts[i] + neg_pcts[i]/2, f"{neg_pcts[i]:.1f}%", ha='center', va='center', color='white', fontweight='bold')
        
        # Neutral percentage label
        if neu_pcts[i] > 7:
            plt.text(i, pos_pcts[i] + neg_pcts[i] + neu_pcts[i]/2, f"{neu_pcts[i]:.1f}%", 
                    ha='center', va='center', color='black', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'sentiment_percentage_by_company.png'))
    
    return comparison_df

def generate_ranking_report(comparison_df, output_dir="multi_company_analysis"):
    """Generate a ranking report of the companies based on sentiment analysis."""
    report_path = os.path.join(output_dir, 'company_sentiment_ranking_report.txt')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("COMPANY SENTIMENT ANALYSIS RANKING REPORT\n")
        f.write("========================================\n\n")
        f.write(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n")
        f.write(f"Total Companies Analyzed: {len(comparison_df)}\n\n")
        
        f.write("COMPANY RANKINGS BY POSITIVE SENTIMENT PERCENTAGE:\n")
        f.write("=" * 70 + "\n")
        f.write(f"{'Rank':<5} {'Company':<25} {'Positive %':<10} {'Positive':<10} {'Negative':<10} {'Neutral':<10} {'Total':<10}\n")
        f.write("-" * 85 + "\n")
        
        # Sort by positive percentage for ranking
        ranked_df = comparison_df.sort_values('Positive_Percentage', ascending=False).reset_index(drop=True)
        
        for i, row in ranked_df.iterrows():
            rank = i + 1
            f.write(f"{rank:<5} {row['Company']:<25} {row['Positive_Percentage']:<10.1f} {row['Positive']:<10} "
                   f"{row['Negative']:<10} {row['Neutral']:<10} {row['Total']:<10}\n")
        
        f.write("\n\nSUMMARY OBSERVATIONS:\n")
        f.write("=" * 60 + "\n")
        
        # Add some insights about the data
        top_company = ranked_df.iloc[0]['Company']
        bottom_company = ranked_df.iloc[-1]['Company']
        highest_pct = ranked_df.iloc[0]['Positive_Percentage']
        lowest_pct = ranked_df.iloc[-1]['Positive_Percentage']
        
        f.write(f"• Top ranked company: {top_company} with {highest_pct:.1f}% positive reviews\n")
        f.write(f"• Lowest ranked company: {bottom_company} with {lowest_pct:.1f}% positive reviews\n")
        
        # Difference between highest and lowest
        diff = highest_pct - lowest_pct
        f.write(f"• Difference between highest and lowest: {diff:.1f} percentage points\n")
        
        # Calculate average positive percentage
        avg_pos_pct = ranked_df['Positive_Percentage'].mean()
        f.write(f"• Average positive sentiment across all companies: {avg_pos_pct:.1f}%\n")
        
        # Companies above average
        above_avg = ranked_df[ranked_df['Positive_Percentage'] > avg_pos_pct]
        f.write(f"• {len(above_avg)} companies performed above average in positive sentiment\n")
        
        # Companies with more negative than positive reviews
        more_neg = ranked_df[ranked_df['Negative'] > ranked_df['Positive']]
        if len(more_neg) > 0:
            f.write(f"• {len(more_neg)} companies have more negative than positive reviews\n")
            for _, row in more_neg.iterrows():
                f.write(f"  - {row['Company']}: {row['Negative']} negative vs {row['Positive']} positive\n")
        
    print(f"Ranking report generated: {report_path}")
    return report_path

def main():
    # Get directory containing company review files
    reviews_dir = input("Enter directory containing company review files (or press Enter for current directory): ").strip()
    if not reviews_dir:
        reviews_dir = "."
    
    if not os.path.exists(reviews_dir):
        print(f"Error: Directory not found at {reviews_dir}")
        return
    
    # Look for review files (allow more flexible naming)
    review_files = [f for f in os.listdir(reviews_dir) if f.endswith('.txt') and not f.startswith('.')]
    
    if not review_files:
        print(f"No text files found in {reviews_dir}.")
        return
    
    print(f"Found {len(review_files)} potential review files.")
    
    # Confirm with user
    if len(review_files) != 11:
        proceed = input(f"Found {len(review_files)} files (expected 11). Continue anyway? (y/n): ").lower()
        if proceed != 'y':
            print("Operation cancelled by user.")
            return
    
    # Process each company's reviews
    all_companies_data = {}
    
    for file_name in review_files:
        file_path = os.path.join(reviews_dir, file_name)
        
        # Extract company name from filename (remove extension and common suffixes)
        company_name = file_name.replace('.txt', '')
        for suffix in ['_reviews', '_reviews_with_ratings', '_yelp', '_google', '_data']:
            company_name = company_name.replace(suffix, '')
        
        print(f"\nProcessing reviews for {company_name}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                review_text = f.read()
        except UnicodeDecodeError:
            # Try with a different encoding if UTF-8 fails
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    review_text = f.read()
            except Exception as e:
                print(f"Could not read file {file_path}: {e}")
                continue
        
        # Parse reviews with more flexible parsing
        company_info, reviews = parse_reviews_text(review_text, company_name)
        
        if not reviews:
            print(f"No reviews were parsed for {company_name}. Skipping.")
            continue
        
        # Display sample of first review
        print(f"Sample of first review for {company_name}:")
        print(f"Rating: {reviews[0].get('rating', 'N/A')}")
        print(f"Text sample: {reviews[0]['text'][:100]}...")
        
        # Analyze sentiment
        model_name = "distilbert-base-uncased-finetuned-sst-2-english"
        analyzed_reviews = analyze_sentiment(reviews, model_name)
        
        # Store analyzed reviews
        all_companies_data[company_name] = analyzed_reviews
    
    if not all_companies_data:
        print("No data was processed successfully. Exiting.")
        return
    
    print(f"\nCreating comparative visualizations for {len(all_companies_data)} companies...")
    output_dir = "multi_company_sentiment_analysis"
    comparison_df = create_company_comparison_visualizations(all_companies_data, output_dir)
    
    # Generate ranking report
    report_path = generate_ranking_report(comparison_df, output_dir)
    
    print(f"\nAnalysis complete!")
    print(f"Visualizations and report saved to: {output_dir}")
    print(f"Company ranking report: {report_path}")
    
    # Print top 3 companies
    top3 = comparison_df.sort_values('Positive_Percentage', ascending=False).head(3)
    print("\nTOP 3 COMPANIES BY POSITIVE SENTIMENT:")
    for i, (_, row) in enumerate(top3.iterrows()):
        print(f"{i+1}. {row['Company']}: {row['Positive_Percentage']:.1f}% positive")

if __name__ == "__main__":
    main()