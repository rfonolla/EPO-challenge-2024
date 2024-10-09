# Standard library imports
import os
from collections import Counter
import re
from typing import Optional, List
import json

# Third-party library imports
from llama_index.core import Document, VectorStoreIndex, Settings, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.schema import MetadataMode, RelatedNodeInfo, NodeRelationship, NodeWithScore, QueryBundle, Node
from llama_index.core.indices import SummaryIndex
from llama_index.core.response.notebook_utils import display_response
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.anthropic import Anthropic
from llama_index.core.prompts import PromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Custom imports
import utils

def extract_keywords_from_template(template: str) -> List[str]:
    """
    Extract keywords from the static part of the prompt template.

    Args:
        template (str): The prompt template.

    Returns:
        List[str]: List of extracted keywords.
    """
    # Remove placeholders and clean the template text
    static_text = re.sub(r'{.*?}', '', template)
    
    # Optional: remove common stopwords
    stopwords = set(["you", "are", "an", "the", "of", "on", "following", "based", "information", "expert", "examiner"])
    
    # Find all words and filter out stopwords
    words = re.findall(r'\b\w+\b', static_text.lower())
    filtered_words = [word for word in words if word not in stopwords]
    
    # Count the frequency of each word
    word_counts = Counter(filtered_words)
    
    return list(word_counts.keys())

class HierarchicalQueryEngine:
    """
    Main engine of the RAG pipeline for patent analysis.
    """

    def __init__(self, claim_index: VectorStoreIndex, **kwargs):
        """
        Initialize the HierarchicalQueryEngine.

        Args:
            claim_index (VectorStoreIndex): Index for patent claims.
            **kwargs: Additional indices for patent information.
        """
        self.claim_index = claim_index
        self.patent_information_indices = kwargs

    def query(self, prompt_template: str, claim_k: int = 2, additional_k: int = 2, print_prompt: bool = False) -> str:
        """
        Execute the hierarchical query process.

        Args:
            prompt_template (str): Template for the prompt.
            claim_k (int): Number of top claims to retrieve.
            additional_k (int): Number of additional information chunks to retrieve.
            print_prompt (bool): Whether to print the generated prompt.

        Returns:
            str: Generated summary based on the query.
        """
        # Extract relevant keywords from the initial claim prompt
        keywords = " ".join(extract_keywords_from_template(prompt_template))

        claim_nodes = self.claim_index.as_retriever(similarity_top_k=claim_k).retrieve(keywords)

        combined_response = "Claims Information:\n"
        combined_response += self._format_response(claim_nodes, "")
        
        # Add extra instructions to the prompts if additional indices were used
        if self.patent_information_indices:
            prompt_template = prompt_template.replace("{information}", "You can use the additional information to improve your answer:\n Additional information \n {information}")

        # Query additional indices if they exist
        for index_name, index in self.patent_information_indices.items():
            if 'claim_text_index' not in index_name:
                additional_nodes = index.as_retriever(similarity_top_k=additional_k).retrieve(self._format_response(claim_nodes, ""))
                combined_response += f"\n{index_name.capitalize().split('_text')[0]} Information:\n"
                combined_response += self._format_response(additional_nodes, "")

        # Prepare the prompt for the LLM using the combined response
        input_prompt = PromptTemplate(prompt_template)
        
        if print_prompt:
            print(input_prompt.format(information=combined_response))

        # Query the LLM to generate the summary or answer
        summary = Settings.llm.complete(input_prompt.format(information=combined_response))

        return summary.text

    def _format_response(self, nodes: List[NodeWithScore], source: str) -> str:
        """
        Format the response from retrieved nodes.

        Args:
            nodes (List[NodeWithScore]): List of retrieved nodes with scores.
            source (str): Source of the information.

        Returns:
            str: Formatted response string.
        """
        response = f"Source: {source}\n\n" if source else ""
        for i, node in enumerate(nodes, 1):
            response += f"{i}. {node.node.get_content()}\n\n"
        return response

def create_document_from_text(text: str) -> Document:
    """
    Create a Document object from text.

    Args:
        text (str): Input text.

    Returns:
        Document: Created Document object.
    """
    return Document(
        text=text,
        metadata={"category": "patent_text"},
        excluded_embed_metadata_keys=["category"], 
        excluded_llm_metadata_keys=["category"], 
        mimetype="text/plain", 
        text_template='{metadata_str}\n\n{content}', 
        metadata_template='{key}: {value}', 
        metadata_seperator='\n'
    )

def run_RAG_pipeline(llm, prompt_template: str, data_patent: dict, print_prompt: bool = False) -> tuple:
    """
    Run the RAG pipeline for patent analysis.

    Args:
        llm: Language model to use.
        prompt_template (str): Template for the prompt.
        data_patent (dict): Dictionary containing patent data.
        print_prompt (bool): Whether to print the generated prompt.

    Returns:
        tuple: Generated summary and references.
    """
    Settings.llm = llm

    # Set up the embedding model
    device = 'cuda' if utils.check_gpu_is_free(min_memory=5) else 'cpu'
    print(f"Using device: {device}")
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3", device=device)
    Settings.embed_model = embed_model

    # Create index for claims
    document_claim = create_document_from_text(data_patent['claim_text'])
    claims_VectorIndex = VectorStoreIndex.from_documents([document_claim], llm=llm)

    # Create indices for additional patent information
    additional_patent_info = [
        'field_of_invention_text',
        'background_of_the_invention_text',
        'summary_of_the_invention_text',
        'brief_description_of_the_drawings_text',
        'detailed_description_of_the_embodiments_text'
    ]

    additional_indices = {}
    for key in additional_patent_info:
        if data_patent[key]:
            print(f'Added: {key}')
            document = create_document_from_text(data_patent[key])
            index = VectorStoreIndex.from_documents([document], llm=llm)
            additional_indices[f'{key}_index'] = index

    # Create the hierarchical query engine
    query_engine = HierarchicalQueryEngine(claims_VectorIndex, **additional_indices)

    # Modify prompt template if dependent claims exist
    if data_patent['dependent_claims_text']:
        for text in reversed(data_patent['dependent_claims_text']):
            prompt_template = prompt_template.replace("{information}", "{information} \n" + text + "\n ")
        prompt_template = prompt_template.replace("{information}", "{information} \nDependant claims:\n ") 

    # Execute the query
    combined_response = query_engine.query(prompt_template, claim_k=1, additional_k=4, print_prompt=print_prompt)

    # Extract and parse JSON from the response
    json_start = combined_response.index('{')
    json_end = combined_response.rindex('}') + 1
    json_str = combined_response[json_start:json_end]
    data_dict = json.loads(json_str)

    return data_dict['summary'], data_dict['reference']