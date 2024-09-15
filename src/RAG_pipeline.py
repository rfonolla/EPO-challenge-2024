# Imports 
import os
from collections import Counter
import re
from typing import Optional, List

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
    def __init__(self, claim_index: VectorStoreIndex, description_index: Optional[VectorStoreIndex] = None):
        self.claim_index = claim_index
        self.description_index = description_index

    def query(self, prompt_template: str, claim_k: int = 2, description_k: int = 2, print_prompt=False) -> str:
        
        # Extract relevant key words from the initial claim prompt
        keywords = " ".join(extract_keywords_from_template(prompt_template))

        claim_nodes = self.claim_index.as_retriever(similarity_top_k=claim_k).retrieve(keywords)
        
        if self.description_index:
            # Query the claim node to the parent node.
            description_nodes = self.description_index.as_retriever(similarity_top_k=description_k).retrieve(self._format_response(claim_nodes, ""))
        
            # Add extra instructions to the prompts
            prompt_template = prompt_template.replace("{information}", "You can use the information of the patent description to improve your answer:\n {information}")
            # Combine results from both indices
            combined_response = "Claims Information:\n"
            combined_response += self._format_response(claim_nodes, "")
            combined_response += "\nPatent Description:\n"
            combined_response += self._format_response(description_nodes, "")
        else:
            # Return results from claims if available
            print('Using only claim information...')
            combined_response = self._format_response(claim_nodes, "Claims Information:")

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

def run_RAG_pipeline(llm, prompt_template, claim_text, description_text=None, print_prompt=False):

    Settings.llm = llm
    Settings.embed_model = "local:BAAI/bge-small-en-v1.5"

    document_claim = Document(
        text=claim_text,
        metadata={
            "category": "claim", 
        },
        excluded_embed_metadata_keys=['category'], 
        excluded_llm_metadata_keys=['category'], 
        mimetype='text/plain', 
        start_char_idx=None, 
        end_char_idx=None, 
        text_template='{metadata_str}\n\n{content}', 
        metadata_template='{key}: {value}', metadata_seperator='\n'
    )
    
    claims_VectorIndex = VectorStoreIndex.from_documents([document_claim], llm=llm)

    if description_text:
        document_description = Document(
            text=description_text,
            metadata={
                "category": "description",
            },
            excluded_embed_metadata_keys=["category"], 
            excluded_llm_metadata_keys=["category"], 
            mimetype="text/plain", 
            start_char_idx=None, 
            end_char_idx=None, 
            text_template='{metadata_str}\n\n{content}', 
            metadata_template='{key}: {value}', metadata_seperator='\n'
        )
        
        description_VectorIndex = VectorStoreIndex.from_documents([document_description], llm=llm)

        # Create the hierarchical query engine with loaded indices
        query_engine = HierarchicalQueryEngine(claims_VectorIndex, 
                                                description_VectorIndex)
    else:
        query_engine = HierarchicalQueryEngine(claims_VectorIndex)
    
    # Example combined query
    combined_response = query_engine.query(prompt_template, 
                                           claim_k=1, # number of entries for the claim
                                           description_k=4, # number of entries for the description relevant if we used description text
                                           print_prompt=print_prompt
                                          )
    # print the final summary generated by the LLM
    return combined_response
    

