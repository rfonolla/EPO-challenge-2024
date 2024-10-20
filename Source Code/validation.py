import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, Any, List

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)

def preprocess_text(text: str) -> str:
    """
    Preprocess the input text by tokenizing, converting to lowercase,
    removing non-alphanumeric tokens and stopwords.

    Args:
        text (str): Input text to preprocess.

    Returns:
        str: Preprocessed text.
    """
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    return ' '.join([word for word in tokens if word.isalnum() and word not in stop_words])

def generate_patent_info_string(data_patent: Dict[str, Any]) -> str:
    """
    Generate a single string containing all relevant patent information.

    Args:
        data_patent (Dict[str, Any]): Dictionary containing patent data.

    Returns:
        str: Concatenated string of patent information.
    """
    info_parts = []
    
    # Add dependent claims if available
    if data_patent.get('dependent_claims_text'):
        info_parts.append(' '.join(data_patent['dependent_claims_text']))
    
    # Add other patent sections if available
    for key in ['field_of_invention_text', 'background_of_the_invention_text',
                'summary_of_the_invention_text', 'brief_description_of_the_drawings_text',
                'detailed_description_of_the_embodiments_text']:
        if data_patent.get(key):
            info_parts.append(data_patent[key])
    
    return " ".join(info_parts)

def check_patent_info(data_patent: Dict[str, Any]) -> bool:
    """
    Check if any relevant patent information is present in the data.

    Args:
        data_patent (Dict[str, Any]): Dictionary containing patent data.

    Returns:
        bool: True if any relevant information is present, False otherwise.
    """
    patent_info_flags = [
        'field_of_invention_text',
        'background_of_the_invention_text',
        'summary_of_the_invention_text',
        'brief_description_of_the_drawings_text',
        'detailed_description_of_the_embodiments_text'
    ]
    
    # Check if any main flags are present
    main_flags_present = any(data_patent[flag] for flag in patent_info_flags)
    
    # Check if dependent claims are present
    dependent_claims = data_patent['dependent_claims_text']
    dependent_claims_present = dependent_claims is not None and len(dependent_claims) > 0
    
    return main_flags_present or dependent_claims_present

def evaluate_patent_claim_summary(data_patent: Dict[str, Any], summary: str) -> Dict[str, Any]:
    """
    Evaluate the quality of a patent claim summary by comparing it to the original claim and patent information.

    Args:
        data_patent (Dict[str, Any]): Dictionary containing patent data.
        summary (str): Summary of the patent claim.

    Returns:
        Dict[str, Any]: Dictionary containing evaluation metrics.
    """
    patent_info_flags = [
        'dependent_claims_text',
        'field_of_invention_text',
        'background_of_the_invention_text',
        'summary_of_the_invention_text',
        'brief_description_of_the_drawings_text',
        'detailed_description_of_the_embodiments_text'
    ]

    # Check if patent information is present
    patent_info_present = check_patent_info(data_patent)

    # Extract claim text
    claim = data_patent['claim_text']
    
    # Preprocess texts
    claim_processed = preprocess_text(claim)
    summary_processed = preprocess_text(summary)
    
    # Initialize TfidfVectorizer
    tfidf = TfidfVectorizer()

    # Prepare texts for vectorization
    texts_to_vectorize: List[str] = [claim_processed, summary_processed]
    
    # Calculate term sets
    claim_terms = set(word_tokenize(claim_processed))
    summary_terms = set(word_tokenize(summary_processed))

    results: Dict[str, Any] = {}
    
    # Vectorize claim and summary
    tfidf_matrix = tfidf.fit_transform(texts_to_vectorize)

    # Calculate cosine similarity between claim and summary
    claim_summary_similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    # Calculate technical term retention
    technical_term_retention = len(summary_terms.intersection(claim_terms)) / len(claim_terms)

    # Store basic metrics
    results["overall_metrics"] = {
        "Cosine similarity": round(float(claim_summary_similarity),4),
        "Ratio summary terms": technical_term_retention,
    }

    # Process additional patent info if present
    if patent_info_present:
        patent_info = generate_patent_info_string(data_patent)
        patent_info_processed = preprocess_text(patent_info)
        texts_to_vectorize.append(patent_info_processed)
        patent_terms = set(word_tokenize(patent_info_processed))

        # Recalculate TF-IDF matrix with patent info
        tfidf_matrix = tfidf.fit_transform(texts_to_vectorize)

        # Calculate additional metrics
        summary_patent_info_similarity = cosine_similarity(tfidf_matrix[1:2], tfidf_matrix[2:3])[0][0]
        patent_info_incorporation = len(summary_terms.intersection(patent_terms)) / len(patent_terms)

        # Update original metrics
        results["overall_metrics"].update({
            "Cosine similarity": round(float(summary_patent_info_similarity),4),
            "Ratio summary terms": patent_info_incorporation
        })

        # Process individual patent info flags
        for flag in patent_info_flags:
            flag_text = data_patent.get(flag)
            if flag_text:
                flag_text = ' '.join(flag_text) if isinstance(flag_text, list) else flag_text
                flag_processed = preprocess_text(flag_text)
                
                # Calculate cosine similarity
                flag_tfidf = tfidf.transform([flag_processed])
                cosine_sim = cosine_similarity(tfidf_matrix[1:2], flag_tfidf)[0][0]
                
                # Calculate ratio of summary terms
                flag_terms = set(word_tokenize(flag_processed))
                term_ratio = len(summary_terms.intersection(flag_terms)) / len(flag_terms) if flag_terms else 0
                
                results[flag] = {
                    "Cosine similarity": round(float(cosine_sim),4),
                    "Ratio of summary terms": term_ratio
                }

    return results