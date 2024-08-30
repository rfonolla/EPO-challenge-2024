

import login_hf
import torch
import os
import transformers

from transformers import AutoModelForCausalLM, AutoTokenizer

login_hf.login_to_hf()

class Llama3:
    def __init__(self, model_path):
        self.model_id = model_path
        self.pipeline = transformers.pipeline(
            "text-generation",
            model=self.model_id,
            device=0,
            model_kwargs={
                "torch_dtype": torch.float16, # In float16 or else does not fit in memory.
                "low_cpu_mem_usage": True,
            },
        )
        self.terminators = [
            self.pipeline.tokenizer.eos_token_id,
            self.pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>"),
        ]
  
    def get_response(
          self, query, message_history=[], max_tokens=4096, temperature=0.6, top_p=0.9
      ):
        user_prompt = message_history + [{"role": "user", "content": query}]
        prompt = self.pipeline.tokenizer.apply_chat_template(
            user_prompt, tokenize=False, add_generation_prompt=True
        )
        print(prompt)
        outputs = self.pipeline(
            prompt,
            max_new_tokens=max_tokens,
            eos_token_id=self.terminators,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
        )
        print(outputs)
        response = outputs[0]["generated_text"][len(prompt):]
        return response, user_prompt + [{"role": "assistant", "content": response}]
    
            
# define the system and user messages
system_input = "You are an expert matplotlib programmer."
user_input = "Give me the code for matplotlib to generate a diagram of a Box A with title Claim 1 and a Box B with title Claim 1.1 , box A points with an arrow towards box B"
conversation = [{"role": "system", "content": system_input}]

# load the model and tokenizer
model_id = "meta-llama/Meta-Llama-3-8B-Instruct"
llama3 = Llama3(model_id)
response, conversation = llama3.get_response(user_input, conversation)

print(response)

  
# if __name__ == "__main__":