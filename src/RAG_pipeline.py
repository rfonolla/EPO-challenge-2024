# Imports 
import os
from collections import Counter
import re
from typing import Optional, List
import json

# Llama index
from llama_index.core import Document
from llama_index.core import VectorStoreIndex
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.schema import MetadataMode, RelatedNodeInfo, NodeRelationship
from llama_index.core.indices import SummaryIndex
from llama_index.core.response.notebook_utils import display_response
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core import Settings
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import Node
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.anthropic import Anthropic
from llama_index.core.schema import MetadataMode
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.prompts import PromptTemplate



# Function to extract keywords from the static part of the prompt (ignoring placeholders)
def extract_keywords_from_template(template):
    # Remove placeholders and clean the template text
    static_text = re.sub(r'{.*?}', '', template)  # Remove placeholders like {information}
    
    # Optional: remove common stopwords, you can extend the list as needed
    stopwords = set(["you", "are", "an", "the", "of", "on", "following", "based", "information","expert", "examiner"])
    
    # Find all words and filter out stopwords
    words = re.findall(r'\b\w+\b', static_text.lower())
    filtered_words = [word for word in words if word not in stopwords]
    
    # Count the frequency of each word
    word_counts = Counter(filtered_words)
    
    return word_counts.keys()

# Main engine of the RAG pipeline - Query that extract the relevant information from the claim
# The extracted information is fed to the Query of the description , which extracts the relavant information
# A prompt is build based on the previous information.

class HierarchicalQueryEngine():
    def __init__(self, claim_index: VectorStoreIndex, **kwargs):
        self.claim_index = claim_index
        self.patent_information_indices = kwargs

    def query(self, prompt_template: str, claim_k: int = 2, additional_k: int = 2, print_prompt=False) -> str:
        
        # Extract relevant key words from the initial claim prompt
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

        #Prepare the prompt for the LLM using the combined response and query_str
        input_prompt = PromptTemplate((prompt_template))
        
        if print_prompt:
            print(input_prompt.format(information=combined_response))

        # Query the LLM to generate the summary or answer
        summary = Settings.llm.complete(input_prompt.format(information=combined_response))

        return summary.text  # Return the LLM-generated summary

    def _format_response(self, nodes: List[NodeWithScore], source: str) -> str:
        response = f"Source: {source}\n\n" if source else ""
        for i, node in enumerate(nodes, 1):
            response += f"{i}. {node.node.get_content()}\n\n"
        return response

def create_document_from_text(text):
    return Document(
        text=text,
        metadata={
            "category": "patent_text",
        },
        excluded_embed_metadata_keys=["category"], 
        excluded_llm_metadata_keys=["category"], 
        mimetype="text/plain", 
        start_char_idx=None, 
        end_char_idx=None, 
        text_template='{metadata_str}\n\n{content}', 
        metadata_template='{key}: {value}', metadata_seperator='\n'
    )

def run_RAG_pipeline(llm, prompt_template, data_patent, print_prompt=False):

    Settings.llm = llm
    #Settings.embed_model = "local:BAAI/bge-small-en-v1.5"
    Settings.embed_model = "local:BAAI/bge-m3"

    document_claim = create_document_from_text(data_patent['claim_text'])
    claims_VectorIndex = VectorStoreIndex.from_documents([document_claim], llm=llm)

    # Create indices for each section if the text is provided
    additional_patent_info = ['field_of_invention_text',
                   'background_of_the_invetion_text',
                   'summary_of_the_invention_text',
                   'brief_description_of_the_drawings_text',
                   'detailed_description_of_the_embodiments_text']

    additional_indices = {}

    for key in additional_patent_info:
        if data_patent[key]:
            additional_text = data_patent[key]
            print('Added:', key)
            document = create_document_from_text(additional_text)
            index = VectorStoreIndex.from_documents([document], llm=llm)
            additional_indices[f'{key}_index'] = index

    # Create the hierarchical query engine with loaded indices
    query_engine = HierarchicalQueryEngine(claims_VectorIndex, **additional_indices)

    if data_patent['depedent_claims_text']:
        # We want to reverse the loop to include the first depedant claim in the prompt
        for text in reversed(data_patent['depedent_claims_text']):
            prompt_template = prompt_template.replace("{information}", "{information} \n" + text + "\n ")
        prompt_template = prompt_template.replace("{information}", "{information} \nDependant claims:\n ") 
    # Example combined query
    combined_response = query_engine.query(prompt_template , 
                                           claim_k=1, # number of entries for the claim
                                           additional_k=4, # number of entries for the description relevant if we used description text
                                           print_prompt=print_prompt
                                          )
    # Extract the JSON part from the text
    json_start = combined_response.index('{')
    json_end = combined_response.rindex('}') + 1
    json_str = combined_response[json_start:json_end]
    
    # Parse the JSON string into a Python dictionary
    data_dict = json.loads(json_str)

    return data_dict['summary'], data_dict['reference']
    

